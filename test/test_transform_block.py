from PianoPlayer import PianoPlayer
from services.parse_midi import parse_midi
from services.transform_block import transform_block


if __name__ == "__main__":
    MIDI_FILE = "60BPM_G_River Flows In You.mid"

    print("正在解析MIDI文件...")
    midi_info = parse_midi(MIDI_FILE)
    print(f"解析完成 | 总时长: {midi_info['total_duration'] / 1e6:.2f}s | "
          f"轨道数: {midi_info['num_tracks']} | PPQN: {midi_info['ticks_per_beat']}")

    all_block_info = transform_block(midi_info)

    print(all_block_info)

    player = PianoPlayer(r"MS Basic.sf2")
    player.synth.program_select(0, player.sf_id, 0, 0)
    player.synth.program_select(1, player.sf_id, 0, 0)
    for note in all_block_info['all_notes']:
        print(note)
        if note['delta_mc_tick'] > 0:
            player.ms_delay(note['delta_mc_tick'] / 16 * 1000)
        player.play_note(pitch=note['pitch'], velocity=note['velocity'],
                         duration=note['duration_mc_tick'] / 16 * 1000, channel=note['channel'])
