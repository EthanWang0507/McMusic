import time

from PianoPlayer import PianoPlayer
from functions import is_integer_loose
from services.parse_midi import parse_midi

if __name__ == "__main__":
    MIDI_FILE = "一路生花 – 张博文 一路生花（Instrumental） – 张博文.mid"

    print("正在解析MIDI文件...")
    midi_info = parse_midi(MIDI_FILE)
    print(f"解析完成 | 总时长: {midi_info['total_duration'] / 1e6:.2f}s | "
          f"轨道数: {midi_info['num_tracks']} | PPQN: {midi_info['ticks_per_beat']}")

    player = PianoPlayer(r"MS Basic.sf2")
    not_int_M = []
    for evt in midi_info['events']:
        msg = evt['msg']

        print(f"T:{float(evt['time_us'] / int(1e6))}", end="  ")
        if evt['delta_time_us'] > 0:
            # delta_time_us = round(evt['delta_time_us'] / 2.5e4) * 2.5e4
            delta_time_us = evt['delta_time_us']
            M = float(delta_time_us / int(6.25e4))

            if not is_integer_loose(M):
                not_int_M.append(M)
                print("**", end=' ')

            player.ms_delay(delta_time_us / 1e3)
            print(f"Dt(ms): {float(delta_time_us / int(1e3))} ; M:{M}", end="  ")
        else:
            print(f"Dt(ms): 0", end="  ")

        if msg.is_meta:
            print(f"Meta设置 {msg.type}")
            continue
        match msg.type:  # 20t = 1s ; 1e6 us = 20t ; 1t = 5e4 us // 1t = 50ms
            case "control_change":
                print(f"控制器设置 {msg} 于 通道{msg.channel}")
                player.synth.cc(msg.channel, msg.control, msg.value)
            case "program_change":
                print(f"设置音色 {msg.program} 于 通道{msg.channel}")
                if msg.channel == 9:
                    # 打击乐通道：使用鼓组音色库 bank=128，保留原program编号
                    player.synth.program_select(9, player.sf_id, 128, msg.program)
                else:
                    # 旋律通道：使用标准旋律库 bank=0
                    player.synth.program_select(msg.channel, player.sf_id, 0, msg.program)
            case "note_on":
                if msg.channel == 9:
                    print(f"打击乐 {msg}")
                    player.play_drum(msg.note, msg.velocity)
                    continue
                # duration_ms = round(evt['duration_us'] / int(2.5e4)) * 25
                duration_us = evt['duration_us']
                duration_ms = duration_us / 1e3

                M = float(duration_us / int(6.25e4))

                if not is_integer_loose(M):
                    not_int_M.append(M)
                    print("**", end=' ')

                print(f"音符播放 {msg} 于 通道{msg.channel} "
                      f"d(ms):{duration_ms}  M:{M} loss(ms):{float((evt['duration_us'] / int(1e3)) - duration_ms)}")
                player.play_note(pitch=msg.note, velocity=msg.velocity,
                                 duration=duration_ms / 1e3, channel=msg.channel)
            case _:
                print(f"UnKnown Msg {msg}")

    print(f"Not Int M:{not_int_M}")
    time.sleep(5)
    player.close()