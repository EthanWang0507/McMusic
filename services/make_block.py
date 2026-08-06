from utils.logger import LOGGER
from config import config
from utils.constants import BlockType
from blockSetter import BlockSetter


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


def make_block(all_notes_info, sx, sy, sz, track_gap=3):
    """
    在起始坐标处，从左至右，从后往前，依次放置。
    track_gap: 轨道间隔
    """
    blockSetter = BlockSetter()

    config.validate_rcon_config()
    blockSetter.connect(
        server_ip=config.SERVER_IP,
        rcon_port=config.RCON_PORT,
        rcon_pwd=config.RCON_PWD
    )

    track_num = all_notes_info['track_num']
    all_notes = all_notes_info['all_notes']

    track_x = [0] * track_num
    for i in range(track_num):  # track下标从0开始
        track_x[i] = sx + i * (track_gap + 1)

    for i in range(track_num):  # 在轨道-1位置放置红石线
        blockSetter.setBlock(BlockType.WIRE, track_x[i], sy, sz - 1)
    # 放置命令方块来激活轨道
    blockSetter.setBlock(BlockType.COMMAND_BLOCK, track_x[0] - 1, sy, sz - 2, {
        "Command": {
            "content": f"/fill ~1 ~ ~ ~{(track_num - 1) * (track_gap + 1) + 2} ~ ~ minecraft:redstone_block",
            "type": "string"
        }
    })
    blockSetter.setBlock(BlockType.LEVER, track_x[0] - 1, sy, sz - 3)
    blockSetter.setBlock(BlockType.COMMAND_BLOCK, track_x[0] - 3, sy, sz - 2, {
        "Command": {
            "content": f"/fill ~3 ~ ~ ~{(track_num - 1) * (track_gap + 1) + 4} ~ ~ minecraft:air",
            "type": "string"
        }
    })
    blockSetter.setBlock(BlockType.LEVER, track_x[0] - 3, sy, sz - 3)

    offset_z = 0
    n = 0  # all_notes当前下标
    while n < len(all_notes):
        delta = all_notes[n]['delta_mc_tick']
        if delta > 0:
            cnt = {4: 0, 3: 0, 2: 0, 1: 0}
            cnt[4] = delta // 8
            delta %= 8
            cnt[3] = delta // 6
            delta %= 6
            cnt[2] = delta // 4
            delta %= 4
            cnt[1] = delta // 2
            delta %= 2
            if delta > 0:
                LOGGER.warning(f"Warn: loss: 1 at z: {sz + offset_z}")  # TPS should be doubled or more to improve rhythm accuracy

            for j in range(4, 0, -1):
                for k in range(cnt[j]):
                    cz = sz + offset_z
                    for i in range(track_num):
                        # y轴垂直于地面，方块水平放置，y不变
                        blockSetter.setBlock(BlockType.REPEATER, track_x[i], sy, cz,
                                             state={"delay": {'content': j, "type": 'int'}})
                    offset_z += 1

            if delta > 0:
                cz = sz + offset_z
                for i in range(track_num):
                    blockSetter.setOneDelay(track_x[i], sy, cz)
                # 脉冲(0 gt) -> 粘性活塞 -> 红石块 -> air -> 红石线 -> 音符盒(1 gt) -> 脉冲
                # setOneDelay在z轴方向占4格
                offset_z += 4
        cur_notes_track = {all_notes[n]['track']: [all_notes[n]]}  # 存储所有同时播放的音符的轨道
        while n + 1 < len(all_notes) and all_notes[n + 1]['delta_mc_tick'] == 0:
            if all_notes[n + 1]['track'] not in cur_notes_track:
                cur_notes_track[all_notes[n + 1]['track']] = []
            cur_notes_track[all_notes[n + 1]['track']].append(all_notes[n + 1])
            n += 1

        for i in range(track_num):
            if i in cur_notes_track:
                pos = get_sync_notes_pos(len(cur_notes_track[i]))

                if len(cur_notes_track[i]) > 3:
                    # 设置红石钱触点朝向, 一个方位side = 四个方位side
                    state = {'south': {'content': 'side', 'type': 'string'}}
                    blockSetter.setBlock(BlockType.WIRE, track_x[i] + 1, sy, sz + offset_z, state=state)
                    blockSetter.setBlock(BlockType.WIRE, track_x[i] - 1, sy, sz + offset_z, state=state)

                for j, note in enumerate(cur_notes_track[i]):
                    offset_x_track = pos[j]['offset_x']
                    offset_z_track = pos[j]['offset_z']

                    cx = track_x[i] + offset_x_track
                    cz = sz + offset_z + offset_z_track
                    blockSetter.setBlock(BlockType.NOTE_BLOCK, cx, sy, cz,
                                         nbt={"note": {'content': note['pitch'], 'type': 'int'},
                                              "velocity": {'content': note['velocity'], 'type': 'int'},
                                              "sustainTime": {
                                                  'content': note['duration_mc_tick'],
                                                  'type': 'int'
                                              }})
                    if delta > 0 and len(cur_notes_track[i]) > 3:  # 音符盒前为红石线，弱充能
                        # 在音符盒上方放置红石线
                        blockSetter.setBlock(BlockType.WIRE, cx, sy + 1, cz)

                    if note['channel'] == 9:  # 打击乐
                        # 音符盒仅支持默认鼓组的音色
                        blockSetter.setProgram(cx, sy, cz, 128)
                    else:
                        blockSetter.setProgram(cx, sy, cz, note['program'])
            else:
                blockSetter.setBlock(BlockType.REDSTONE_LAMP, track_x[i], sy, sz + offset_z)
        offset_z += 1
        n += 1

    blockSetter.close()
    return 0


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

    make_block(all_block_info, 500, -60, -3000)
