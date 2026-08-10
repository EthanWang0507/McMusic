from dotenv import load_dotenv
load_dotenv()

import argparse

from utils.logger import LOGGER
from config.config import SERVER_IP, RCON_PORT, RCON_PWD
from services.block_placer.rcon_placer import RconBlockPlacer
from services.parse_midi import parse_midi
from services.transform_block import transform_block
from services.make_block import MakeBlock


if __name__ == "__main__":
    LOGGER.info("Welcome to My Project.")

    SX, SY, SZ = 370, -60, -3000
    TPS = 16.0
    MIDI_FILE = "data/midi/60BPM_G_River Flows In You.mid"
    TRACK_GAP = 3
    MODE = "rcon"
    AUTO_CONFIRM = False

    # parser = argparse.ArgumentParser(description="Minecraft红石音乐生成工具")
    # parser.add_argument("midifile", help="Midi 文件路径")
    # parser.add_argument("sx", type=int, help="起始 X 坐标")
    # parser.add_argument("sy", type=int, help="起始 Y 坐标")
    # parser.add_argument("sz", type=int, help="起始 Z 坐标")
    # parser.add_argument("-t", "--tps", type=float, default=20.0, help="Minecraft TPS")
    # parser.add_argument("-m", "--mode", type=str, default="rcon", help="放置方块的模式: rcon")
    # parser.add_argument("--track-gap", type=int, default=3, help="轨道间隔格数")
    # parser.add_argument("--auto-confirm", type=bool, default=False, help="自动开始放置方块(较危险)")
    # args = parser.parse_args()
    #
    # SX, SY, SZ = args.sx, args.sy, args.sz
    # TPS = args.tps
    # MIDI_FILE = args.midifile
    # TRACK_GAP = args.track_gap
    # MODE = args.mode
    # AUTO_CONFIRM = args.auto_confirm

    LOGGER.info("============INPUT============")
    LOGGER.info(f"Midi file: {MIDI_FILE}")
    LOGGER.info(f"TPS: {TPS}")
    LOGGER.info(f"Starting position: ({SX}, {SY}, {SZ})")
    LOGGER.info(f"Mode of placing blocks: {MODE}")
    LOGGER.info(f"Track's gap: {TRACK_GAP}")
    LOGGER.info("=============END=============")

    LOGGER.info("正在解析MIDI文件...")
    midi_info = parse_midi(MIDI_FILE)
    LOGGER.info(f"解析完成 | MIDI总时长: {midi_info['total_duration'] / 1e6:.2f}s | "
                f"轨道数: {midi_info['num_tracks']} | PPQN: {midi_info['ticks_per_beat']}")

    LOGGER.info("正在将Midi信信息转化为Mc方块信息...")
    all_block_info = transform_block(midi_info, TPS=TPS)
    LOGGER.info("转换完成")

    maker = MakeBlock(SX, SY, SZ, track_gap=TRACK_GAP)
    blocks = maker.build(all_block_info)

    EX = SX + (midi_info['num_tracks'] - 1) * (TRACK_GAP + 1)
    EY = SY
    EZ = SZ + maker.get_track_len() - 1
    LOGGER.info("=============信息统计=============")
    LOGGER.info(f"音乐时长: {midi_info['total_duration'] / 1e6:.2f}s  |  TPS: {TPS}")
    LOGGER.info(f"放置模式: {MODE}")
    LOGGER.info(f"轨道数: {midi_info['num_tracks']}  |  方块数量: {len(blocks)}")
    LOGGER.info(f"起始坐标: ({SX}, {SY}, {SZ})  | "
                f"终点坐标: ({EX}, {SY}, {EZ})")
    LOGGER.info("===============END==============")

    if not AUTO_CONFIRM:
        confirm = input("确认开始放置？(Y/n): ").strip()
        if confirm != "Y":
            LOGGER.info("已取消放置")
            exit(0)

    if MODE == "rcon":
        placer = RconBlockPlacer(
            host=SERVER_IP,
            port=RCON_PORT,
            pwd=RCON_PWD,
            auto_unload=True,
            auto_confirm=AUTO_CONFIRM
        )
    else:
        raise ValueError(f"不支持的放置模式: {MODE}")

    with placer:
        placer.place_blocks(blocks)

    LOGGER.info("All work done.")