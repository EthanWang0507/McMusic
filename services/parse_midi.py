from collections import defaultdict
from fractions import Fraction
from typing import Dict, Any

import mido


def parse_midi(file_path: str) -> Dict[str, Any]:
    """解析MIDI文件，为每个有效note_on计算持续时长（秒/tick）"""
    mid = mido.MidiFile(file_path)

    ticks_per_beat = mid.ticks_per_beat
    all_events = []

    # 1. 收集所有事件并计算绝对tick时间
    for track_idx, track in enumerate(mid.tracks):
        current_tick = 0
        for msg in track:
            current_tick += msg.time
            all_events.append({"time_tick": current_tick, "msg": msg, "track": track_idx})
    all_events.sort(key=lambda x: x["time_tick"])

    # 2. 计算绝对时间（秒），修复tempo更新时序错误
    current_tempo = 500000
    current_time_us = 0
    last_tick = 0
    processed_events = []

    for event in all_events:
        tick, msg, track = event["time_tick"], event["msg"], event["track"]

        delta_us = Fraction((tick - last_tick) * current_tempo, ticks_per_beat)
        current_time_us += delta_us
        last_tick = tick

        if msg.type == "set_tempo":
            current_tempo = msg.tempo

        processed_events.append({
            "time_us": current_time_us,
            "time_tick": tick,
            "type": msg.type,
            "track": track,
            "msg": msg,
            "duration_us": -1.0,
            "duration_tick": -1,
            "delta_time_us": -1.0
        })

    # 3. 配对 note_on / note_off
    # 修复key：增加track区分不同轨道同通道同音高，使用栈pop()后进先出
    note_on_cache = defaultdict(list)
    for event in processed_events:
        # 有效音符按下
        if event["type"] == "note_on" and event["msg"].velocity > 0:
            key = (event["track"], event["msg"].channel, event["msg"].note)
            note_on_cache[key].append(event)
        # 音符释放（note_off / velocity=0 note_on）
        elif event["type"] == "note_off" or (event["type"] == "note_on" and event["msg"].velocity == 0):
            key = (event["track"], event["msg"].channel, event["msg"].note)
            if note_on_cache[key]:
                on_event = note_on_cache[key].pop()  # 栈弹出，修复连音配对错误
                on_event["duration_tick"] = event["time_tick"] - on_event["time_tick"]
                on_event["duration_us"] = event["time_us"] - on_event["time_us"]

    filtered_events = []
    for event in processed_events:
        is_note_off = event["type"] == "note_off"
        is_zero_velocity = event["type"] == "note_on" and event["msg"].velocity == 0
        if not (is_note_off or is_zero_velocity):
            filtered_events.append(event)

    # 用过滤后的列表替换
    processed_events = filtered_events

    # 计算播放音符的间隔时间
    last_note_time = 0.0
    for evt in processed_events:
        evt['delta_time_us'] = evt['time_us'] - last_note_time
        last_note_time = evt['time_us']

    # 处理空文件边界
    total_duration = processed_events[-1]["time_us"] if len(processed_events) > 0 else 0.0

    # 没有对应释放事件，就播放到曲子结束
    total_time_us = processed_events[-1]["time_us"] if processed_events else 0
    for event in processed_events:
        if event["type"] == "note_on" and event["msg"].velocity > 0:
            if event["duration_us"] == -1.0:
                event["duration_us"] = total_time_us - event["time_us"]
                event["duration_tick"] = processed_events[-1]["time_tick"] - event["time_tick"]

    return {
        "ticks_per_beat": ticks_per_beat,
        "format": mid.type,
        "num_tracks": len(mid.tracks),
        "total_duration": total_duration,
        "events": processed_events
    }


if __name__ == "__main__":
    MIDI_FILE = "一路生花 – 张博文 一路生花（Instrumental） – 张博文.mid"

    print("正在解析MIDI文件...")
    midi_info = parse_midi(MIDI_FILE)
    print(f"解析完成 | 总时长: {midi_info['total_duration'] / 1e6:.2f}s | "
          f"轨道数: {midi_info['num_tracks']} | PPQN: {midi_info['ticks_per_beat']}")
