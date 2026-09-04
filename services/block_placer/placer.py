from mcrcon import MCRcon
from typing import Callable, Optional
import json
import time

from utils.constants import BlockEntry, BlockType, BLOCK_ID_MAP, CommandSuccessResult
from utils.logger import LOGGER
from services.block_placer.base import BlockPlacer


class RconBlockPlacer(BlockPlacer):
    def _validate_config(self) -> None:
        if not self.config['host'] or not self.config['port']:
            raise ValueError("RCON 配置不完整")

    def _init_resource(self) -> None:
        c = self.config
        self.host = c['host']
        self.port = c['port']
        self.pwd = c['pwd']

        self._mcr = None
        self._loaded_chunks: list[tuple[int, int, int, int]] = []


    def setup(self) -> None:
        """实现Rcon连接"""
        self.logger.info(f"正在连接 RCON 服务器: {self.host}:{self.port}")
        try:
            self._mcr = MCRcon(self.host, self.pwd, port=self.port)
            self._mcr.connect()
            self.logger.info("RCON 服务器连接成功")
        except Exception as e:
            self.logger.error(f"RCON 连接失败: {e}")
            raise RuntimeError(f"无法连接到 RCON 服务器: {e}") from e

    def _execute_cmd(self, cmd: str):
        time.sleep(0.001)
        return {
            "command": cmd,
            "status": True,
            "result": "resp"
        }
        if not self._mcr:
            self.logger.error(f"RCON未连接，无法执行命令: {cmd}")
            return {"command": cmd, "status": False, "result": ""}

        try:
            r = self._mcr.command(cmd)
        except Exception as e:
            self.logger.error(f"命令执行异常: {cmd}, 错误: {e}")
            return {"command": cmd, "status": False, "result": str(e)}

        cmd_chunk = cmd.split(' ')

        success_result = None
        match cmd_chunk[0][1:]:
            case "forceload":
                if cmd_chunk[1] == "add":
                    success_result = CommandSuccessResult.FORCELOAD_ADD
                elif cmd_chunk[1] == "remove":
                    success_result = CommandSuccessResult.FORCELOAD_REMOVE
            case "setblock":
                success_result = CommandSuccessResult.SETBLOCK
            case "execute":
                success_result = ""

        if success_result is None:
            self.logger.warning(f"执行了不支持的命令: {cmd}")
            self.logger.warning(f"命令返回: {r}")
            is_success = False
        else:
            if success_result not in r or r.lower() in CommandSuccessResult.COMMON_ERROR_KEYWORDS:
                self.logger.error(f"{cmd} 执行失败")
                self.logger.error(f"命令返回: {r}")
                is_success = False
            else:
                # LOGGER.debug(f"{cmd} 执行成功。 返回: {r}")
                is_success = True

        return {
            "command": cmd,
            "status": is_success,
            "result": r
        }

    def _is_area_all_air(self, blocks: list[BlockEntry]) -> bool:
        """
        检测指定长方体区域是否全部为空气
        :return: True=全空，False=存在非空气方块
        """
        self.logger.info("开始检查指定区域是否为空")
        try:
            for block in blocks:
                x, y, z = block.x, block.y, block.z
                cmd = f"/execute if block {x} {y} {z} minecraft:air run seed"
                resp = self._execute_cmd(cmd)['result']
                if len(resp.strip()) == 0:
                    self.logger.error(f"({x}, {y}, {z})方块非空。")
                    return False
        except Exception as e:
            self.logger.error(f"区域空气检测失败: {e}")
            return False
        return True

    def _set_block(self, block_type: BlockType, x, y, z, nbt=None, state=None):
        if nbt is None:
            nbt = {}
        if state is None:
            state = {}

        nbt_cmd, state_cmd = "", ""
        if len(nbt) > 0:
            nbt_cmd = "{"
            for (key, value) in nbt.items():
                if value.get('type') == "string":
                    nbt_cmd += str(key) + ":\"" + str(value['content']) + "\","
                elif value.get('type') == "bool" or isinstance(value['content'], bool):
                    nbt_cmd += str(key) + ":" + str(value['content']).lower() + ","
                else:
                    nbt_cmd += str(key) + ":" + str(value['content']) + ","
            nbt_cmd = nbt_cmd[:-1]
            nbt_cmd += "}"

        if len(state) > 0:
            state_cmd = "["
            for (key, value) in state.items():
                content = str(value['content']).lower() if isinstance(value['content'], bool) else str(value['content'])
                state_cmd += f"{key}={content},"
            state_cmd = state_cmd[:-1]
            state_cmd += "]"

        self._execute_cmd(f"/setblock {x} {y} {z} {block_type}{state_cmd}{nbt_cmd}")
        return 0

    def _set_program(self, x, y, z, program):  # 设置noteblcok的音色
        blockId = BLOCK_ID_MAP[program]
        self._execute_cmd(f"/setblock {x} {y - 1} {z} {blockId}")  # 改变下方方块ID
        return 0

    @staticmethod
    def _calc_chunk(block_pos: tuple[int, int]) -> tuple[int, int]:
        """计算方块所在的区块坐标"""
        return block_pos[0] >> 4, block_pos[1] >> 4

    def _load_chunks(self, min_pos: tuple[int, int], max_pos: tuple[int, int]):
        """加载范围内的所有区块"""
        if min_pos[0] > max_pos[0] or min_pos[1] > max_pos[1]:
            raise ValueError(f"区块起始坐标{min_pos} 大于 结束坐标{max_pos}")

        ONE_FORCELOAD_CHUNK_NUM_LIMIT = 255  # 一条命令最多加载的区块数
        min_x, min_z = min_pos[0], min_pos[1]
        max_x, max_z = max_pos[0], max_pos[1]

        min_chunk = self._calc_chunk(min_pos)
        max_chunk = self._calc_chunk(max_pos)

        min_cx, min_cz = min_chunk[0], min_chunk[1]
        max_cx, max_cz = max_chunk[0], max_chunk[1]

        chunk_x_num = max_cx - min_cx + 1  # x轴方向的区块数(区块宽)
        if chunk_x_num > ONE_FORCELOAD_CHUNK_NUM_LIMIT:
            raise ValueError("轨道过宽(在X方向上过长)，请手动执行forceload。")

        total_chunks = chunk_x_num * (max_cz - min_cz + 1)
        self.logger.info(f"开始加载区块，总计{total_chunks}个。")

        chunk_z_per_batch = ONE_FORCELOAD_CHUNK_NUM_LIMIT // chunk_x_num
        chunk_z_per_batch = max(chunk_z_per_batch, 1)

        cur_cz = min_cz
        while cur_cz <= max_cz:
            end_cz = min(cur_cz + chunk_z_per_batch - 1, max_cz)

            load_z_min = cur_cz * 16
            load_z_max = (end_cz + 1) * 16 - 1

            self._loaded_chunks.append((min_x, load_z_min, max_x, load_z_max))
            r = self._execute_cmd(f"/forceload add {min_x} {load_z_min} {max_x} {load_z_max}")
            if not r["status"]:
                raise RuntimeError(f"区块加载失败，终止生成: {r['result']}")

            cur_cz = end_cz + 1

        self.logger.info("区块加载完成。")

    def _unload_chunks(self):
        self.logger.info("开始卸载区块。")
        for x1, z1, x2, z2 in self._loaded_chunks:
            self._execute_cmd(f"/forceload remove {x1} {z1} {x2} {z2}")
        self.logger.info("区块卸载完成。")

    def _check(self, blocks: list[BlockEntry]) -> bool:
        """检查放置方案的可行性"""
        if not blocks:
            self.logger.warning("方块列表为空，跳过放置")
            return False
        # 计算实际放置的坐标边界
        min_x = min(b.x for b in blocks)
        max_x = max(b.x for b in blocks)
        min_z = min(b.z for b in blocks)
        max_z = max(b.z for b in blocks)
        self._load_chunks((min_x, min_z), (max_x, max_z))

        if not self._is_area_all_air(blocks):
            self.logger.error("在指定的范围内存在非空方块，无法生成轨道。")
            return False
        return True

    def place_blocks(self, blocks: list[BlockEntry], show_progress: bool = True) -> None:
        """批量放置方块列表，支持进度显示"""
        res = self._check(blocks)
        if not res:  # 可行性检查
            self.logger.error("可行性检查不通过，结束放置。")
            return

        begin_time = time.time()
        total = len(blocks)
        self.logger.info(f"开始放置方块，共计{total}个")

        for i, block in enumerate(blocks):
            self._set_block(block.block_id, block.x, block.y, block.z, nbt=block.nbt, state=block.state)
            if block.program >= 0:
                self._set_program(block.x, block.y, block.z, block.program)

            if show_progress and i % 500 == 0:
                cur_progress = round((i + 1) / total * 100, 1)
                self.send(json.dumps({'progress': cur_progress}), 'progress')
                self.logger.info(f"放置进度: {cur_progress}%")
        self.send(json.dumps({'progress': 100}), 'progress')
        self.logger.info("放置进度: 100%")

        self.logger.info(f"所有方块放置完成, 耗时{time.time() - begin_time} s")

    def teardown(self) -> None:
        if self._loaded_chunks:
            self._unload_chunks()
        if self._mcr:
            self._mcr.disconnect()
        self.logger.info("连接断开")


def create_placer(place_mode: str, config: dict, send_callback: Optional[Callable[[str, str], None]] = None) -> BlockPlacer:
    """放置器工厂：根据模式创建对应的放置实例，新增模式只需扩展分支"""
    if place_mode == "rcon":
        return RconBlockPlacer(config, send_callback=send_callback)
    # 后续新增 mcfunction 模式，在这里加分支即可
    # elif place_mode == "mcfunction":
    #     return McFunctionPlacer(output_path=MCF_OUTPUT_PATH)
    else:
        raise ValueError(f"不支持的放置模式: {place_mode}")