from utils.logger import LOGGER
from config import config
from utils.constants import BlockType, BlockEntry
from services.blockSetter import BlockSetter


def get_sync_notes_pos(notes_num: int) -> list[dict]:
    if not isinstance(notes_num, int):
        raise ValueError("音符盒数量必须为整数")
    if notes_num <= 0:
        raise ValueError("音符盒数量必须大于 0")

    MAX_SUPPORTED = 7
    if notes_num > MAX_SUPPORTED:
        raise ValueError(f"暂不能处理超过 {MAX_SUPPORTED} 个同时发声的音符盒")

    if notes_num <= 3:
        # (N) N (N)
        pos_template = [
            {"offset_x": 0, "offset_z": 0},
            {"offset_x": 1, "offset_z": 0},
            {"offset_x": -1, "offset_z": 0}
        ]
        pos = pos_template[:notes_num]
    else:
        pos_template = [
            {"offset_x": 0, "offset_z": 0},
            {"offset_x": -1, "offset_z": 1},
            {"offset_x": -1, "offset_z": -1},
            {"offset_x": 1, "offset_z": -1},
            {"offset_x": 1, "offset_z": 1},
            {"offset_x": -2, "offset_z": 0},
            {"offset_x": 2, "offset_z": 0},
        ]
        pos = pos_template[:notes_num]
    return pos


class MakeBlock:
    def __init__(self, sx, sy, sz, track_gap=3):
        self.sx = sx
        self.sy = sy
        self.sz = sz
        self.track_gap = track_gap
        self.blocks = []  # 存储所有待放置的方块

    def _add_block(self, block: BlockEntry):
        self.blocks.append(block)

    def _add_one_delay(self, x: float, y: float, z: float):
        self._add_block(BlockEntry(BlockType.STICKY_PISTON, x, y, z, state={"facing": {"content": "south", "type": "normal"}}))
        self._add_block(BlockEntry(BlockType.REDSTONE_BLOCK, x, y, z + 1))
        self._add_block(BlockEntry(BlockType.WIRE, x, y, z + 3))

    def build(self, all_notes_info) -> list[BlockEntry]:
        def make_track_trigger():
            """用于在轨道前放置红石原件以激活轨道"""
            for i in range(track_num):  # 在轨道z=-1位置放置红石线
                self._add_block(BlockEntry(BlockType.WIRE, track_x[i], self.sy, self.sz - 1))
            # 放置命令方块来激活轨道
            self._add_block(BlockEntry(BlockType.COMMAND_BLOCK, track_x[0] - 1, self.sy, self.sz - 2, nbt={
                "Command": {
                    "content": f"/fill ~1 ~ ~ ~{(track_num - 1) * (self.track_gap + 1) + 2} ~ ~ minecraft:redstone_block",
                    "type": "string"
                }
            }))
            self._add_block(BlockEntry(BlockType.LEVER, track_x[0] - 1, self.sy, self.sz - 3))
            self._add_block(BlockEntry(BlockType.COMMAND_BLOCK, track_x[0] - 3, self.sy, self.sz - 2, nbt={
                "Command": {
                    "content": f"/fill ~3 ~ ~ ~{(track_num - 1) * (self.track_gap + 1) + 4} ~ ~ minecraft:air",
                    "type": "string"
                }
            }))
            self._add_block(BlockEntry(BlockType.LEVER, track_x[0] - 3, self.sy, self.sz - 3))
        self.blocks.clear()

        track_num = all_notes_info['track_num']
        all_notes = all_notes_info['all_notes']

        # 计算每个轨道的x坐标
        track_x = [0] * track_num
        for i in range(track_num):  # track下标从0开始
            track_x[i] = self.sx + i * (self.track_gap + 1)

        make_track_trigger()

        offset_z = 0
        n = 0  # all_notes当前下标
        while n < len(all_notes):
            delta = all_notes[n]['delta_mc_tick']  # 音符与上一个音符的时间差
            if delta > 0:
                cnt = {4: delta // 8, 3: 0, 2: 0, 1: 0}  # 四个档位的红石中继器个数
                delta %= 8
                cnt[3] = delta // 6
                delta %= 6
                cnt[2] = delta // 4
                delta %= 4
                cnt[1] = delta // 2
                delta %= 2

                for j in range(4, 0, -1):  # 遍历cnt
                    for k in range(cnt[j]):  # 遍历红石中继器个数
                        cz = self.sz + offset_z
                        for i in range(track_num):
                            # y轴垂直于地面，方块水平放置，y不变
                            self._add_block(BlockEntry(
                                BlockType.REPEATER,
                                track_x[i], self.sy, cz,
                                state={"delay": {'content': j, "type": 'int'}}
                            ))
                        offset_z += 1

                if delta > 0:
                    cz = self.sz + offset_z
                    LOGGER.info(f"Put OneDelay at z={cz}")
                    for i in range(track_num):
                        self._add_one_delay(track_x[i], self.sy, cz)
                    # 脉冲(0 gt) -> 粘性活塞 -> 红石块 -> air -> 红石线 -> 音符盒(1 gt) -> 脉冲
                    # setOneDelay在z轴方向占4格
                    offset_z += 4

            cur_notes_track = {all_notes[n]['track']: [all_notes[n]]}  # 同时播放的音符的轨道下标
            while n + 1 < len(all_notes) and all_notes[n + 1]['delta_mc_tick'] == 0:
                cur_notes_track[all_notes[n + 1]['track']].append(all_notes[n + 1])
                n += 1

            for i in range(track_num):
                if i in cur_notes_track:
                    pos = get_sync_notes_pos(len(cur_notes_track[i]))

                    if len(cur_notes_track[i]) > 3:
                        # 设置红石钱触点朝向, 一个方位side = 四个方位side
                        state = {'south': {'content': 'side', 'type': 'string'}}
                        self._add_block(
                            BlockEntry(BlockType.WIRE, track_x[i] + 1, self.sy, self.sz + offset_z, state=state))
                        self._add_block(
                            BlockEntry(BlockType.WIRE, track_x[i] - 1, self.sy, self.sz + offset_z, state=state))

                    for j, note in enumerate(cur_notes_track[i]):
                        offset_x_track = pos[j]['offset_x']
                        offset_z_track = pos[j]['offset_z']

                        if note['channel'] == 9:  # 打击乐
                            # 音符盒仅支持默认鼓组的音色
                            program = 128
                        else:
                            program = note['program']

                        cx = track_x[i] + offset_x_track
                        cz = self.sz + offset_z + offset_z_track
                        self._add_block(BlockEntry(
                            BlockType.NOTE_BLOCK, cx, self.sy, cz,
                            program=program,
                            nbt={"note": {'content': note['pitch'], 'type': 'int'},
                                 "velocity": {'content': note['velocity'], 'type': 'int'},
                                 "sustainTime": {
                                     'content': note['duration_mc_tick'],
                                     'type': 'int'
                                 }}
                        ))
                        if delta > 0 and len(cur_notes_track[i]) > 3:  # 音符盒前为红石线，弱充能
                            # 在音符盒上方放置红石线
                            self._add_block(BlockEntry(BlockType.WIRE, cx, self.sy + 1, cz))
                else:
                    self._add_block(BlockEntry(BlockType.REDSTONE_LAMP, track_x[i], self.sy, self.sz + offset_z))
            offset_z += 1
            n += 1

        return self.blocks


if __name__ == "__main__":
    from parse_midi import parse_midi
    from transform_block import transform_block

    TPS = 25.6
    MIDI_FILE = "一路生花 – 张博文 一路生花（Instrumental） – 张博文.mid"

    print("正在解析MIDI文件...")
    midi_info = parse_midi(MIDI_FILE)
    print(f"解析完成 | MIDI总时长: {midi_info['total_duration'] / 1e6:.2f}s | "
          f"轨道数: {midi_info['num_tracks']} | PPQN: {midi_info['ticks_per_beat']}")

    all_block_info = transform_block(midi_info, TPS=TPS)

    maker = MakeBlock(500, -60, -3000)
    blocks = maker.build(all_block_info)
