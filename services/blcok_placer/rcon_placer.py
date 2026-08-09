from mcrcon import MCRcon
import time

from utils.constants import BlockEntry, BlockType, BLOCK_ID_MAP
from utils.logger import LOGGER
from services.blcok_placer.base import BlockPlacer


class RconBlockPlacer(BlockPlacer):
    _mcr = None

    def __init__(self, host: str, port: int, pwd: str) -> None:
        self.host = host
        self.port = port
        self.pwd = pwd

    def setup(self) -> None:
        """实现Rcon连接"""
        LOGGER.info(f"正在连接 RCON 服务器: {self.host}:{self.port}")
        try:
            self._mcr = MCRcon(self.host, self.pwd, port=self.port)
            self._mcr.connect()
            LOGGER.info("RCON 服务器连接成功")
        except Exception as e:
            LOGGER.error(f"RCON 连接失败: {e}")
            raise RuntimeError(f"无法连接到 RCON 服务器: {e}") from e

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
                else:
                    nbt_cmd += str(key) + ":" + str(value['content']) + ","
            nbt_cmd = nbt_cmd[:-1]
            nbt_cmd += "}"

        if len(state) > 0:
            state_cmd = "["
            for (key, value) in state.items():
                if value.get('type') == "string":
                    state_cmd += str(key) + "=\"" + str(value['content']) + "\","
                else:
                    state_cmd += str(key) + "=" + str(value['content']) + ","
            state_cmd = state_cmd[:-1]
            state_cmd += "]"

        r = self._mcr.command(f"/setblock {x} {y} {z} {block_type}{state_cmd}{nbt_cmd}")
        # print(f"Set {x} {y} {z}  R:{r}")
        return 0

    def _set_program(self, x, y, z, program):  # 设置noteblcok的音色
        blockId = BLOCK_ID_MAP[program]
        self._mcr.command(f"/setblock {x} {y - 1} {z} {blockId}")  # 改变下方方块ID
        return 0

    def place_blocks(self, blocks: list[BlockEntry], show_progress: bool = True) -> None:
        """批量放置方块列表，支持进度显示"""
        begin_time = time.time()
        total = len(blocks)
        LOGGER.info(f"开始放置方块，共计{total}个")

        for i, block in enumerate(blocks):
            self._set_block(block.block_id, block.x, block.y, block.z, nbt=block.nbt, state=block.state)
            if block.program >= 0:
                self._set_program(block.x, block.y, block.z, block.program)

            if show_progress and i % 150 == 0:
                LOGGER.info(f"放置进度: {(i + 1) / total * 100:.1f}%")

        LOGGER.info(f"所有方块放置完成, 耗时{time.time() - begin_time} s")

    def teardown(self) -> None:
        self._mcr.disconnect()
        LOGGER.info("连接断开")
