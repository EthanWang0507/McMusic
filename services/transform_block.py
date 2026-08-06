from fractions import Fraction
from utils.logger import LOGGER


def transform_block(midi_info, TPS=20):
    all_notes = []
    programs = [0] * 16  # programs[channel] = program

    for evt in midi_info['events']:
        msg = evt['msg']
        track_id = evt['track']

        if msg.is_meta:
            LOGGER.warning(f"Ignore: Meta设置 {msg.type}")
            continue
        match msg.type:
            case "control_change":
                LOGGER.warning(f"Ignore: 控制器设置 {msg} 于 通道{msg.channel}")
            case "program_change":
                LOGGER.info(f"设置音色 {msg.program} 于 通道{msg.channel}")
                programs[msg.channel] = msg.program
            case "note_on":
                block_note = {
                    'track': track_id,
                    'channel': msg.channel,
                    'time_mc_tick': round(Fraction(evt['time_us'], 10 ** 6) * Fraction(TPS)),
                    'program': programs[msg.channel],
                    'pitch': msg.note,
                    'velocity': msg.velocity,
                    'duration_mc_tick': round(Fraction(evt['duration_us'], 10 ** 6) * Fraction(TPS)),
                    'delta_mc_tick': -1  # 与前一个note的时间差
                }

                LOGGER.debug(f"音符播放 {block_note}")

                all_notes.append(block_note)
            case _:
                LOGGER.warning(f"Ignore: UnKnown Msg {msg}")

    # 计算delta_mc_tick
    all_notes.sort(key=lambda x: x['time_mc_tick'])

    last_mc_tick = 0
    for note in all_notes:
        note['delta_mc_tick'] = note['time_mc_tick'] - last_mc_tick
        last_mc_tick = note['time_mc_tick']

    return {
        'track_num': midi_info['num_tracks'],
        'all_notes': all_notes
    }


if __name__ == "__main__":
    from parse_midi import parse_midi

    MIDI_FILE = "60BPM_G_River Flows In You.mid"

    print("正在解析MIDI文件...")
    midi_info = parse_midi(MIDI_FILE)
    print(f"解析完成 | 总时长: {midi_info['total_duration'] / 1e6:.2f}s | "
          f"轨道数: {midi_info['num_tracks']} | PPQN: {midi_info['ticks_per_beat']}")

    all_block_info = transform_block(midi_info)

    print(all_block_info)
