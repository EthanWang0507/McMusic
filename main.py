from dotenv import load_dotenv
load_dotenv()

from utils.logger import LOGGER
from services.parse_midi import parse_midi
from services.transform_block import transform_block
from services.make_block import make_block


if __name__ == "__main__":
    LOGGER.info("Welcome to My Project.")

    SX, SY, SZ = 400, -60, -3000
    TPS = 16
    MIDI_FILE = "data/midi/60BPM_G_River Flows In You.mid"

    LOGGER.info("============INPUT============")
    LOGGER.info(f"Midi file: {MIDI_FILE}")
    LOGGER.info(f"TPS: {TPS}")
    LOGGER.info(f"Starting position: ({SX}, {SY}, {SZ})")
    LOGGER.info("=============END=============")

    LOGGER.info("正在解析MIDI文件...")
    midi_info = parse_midi(MIDI_FILE)
    LOGGER.info(f"解析完成 | MIDI总时长: {midi_info['total_duration'] / 1e6:.2f}s | "
                f"轨道数: {midi_info['num_tracks']} | PPQN: {midi_info['ticks_per_beat']}")

    LOGGER.info("正在将Midi信信息转化为Mc方块信息...")
    all_block_info = transform_block(midi_info, TPS=TPS)
    LOGGER.info("转换完成")

    input()

    LOGGER.info("正在放置方块...")
    make_block(all_block_info, SX, SY, SZ)
    LOGGER.info("放置完成")

    LOGGER.info("All work done.")