from dotenv import load_dotenv
load_dotenv()

import argparse
from dataclasses import dataclass

from utils.logger import LOGGER
from config.config import (
    SERVER_IP, RCON_PORT, RCON_PWD,
    DEFAULT_SX, DEFAULT_SY, DEFAULT_SZ,
    DEFAULT_TPS, DEFAULT_TRACK_GAP,
    DEFAULT_PLACE_MODE, DEFAULT_AUTO_CONFIRM
)
from services.block_placer.rcon_placer import RconBlockPlacer
from services.parse_midi import parse_midi
from services.transform_block import transform_block
from services.make_block import MakeBlock


@dataclass
class AppConfig:
    midi_file: str
    sx: int
    sy: int
    sz: int
    tps: float
    track_gap: int
    place_mode: str
    auto_confirm: bool


# ========== 工具函数 ==========
def parse_args() -> argparse.Namespace:
    """解析命令行参数，默认值全部从配置模块读取"""
    parser = argparse.ArgumentParser(description="Minecraft红石音乐生成工具")
    parser.add_argument("midi_file", type=str, help="Midi 文件路径")
    parser.add_argument("-sx", type=int, default=DEFAULT_SX, help="起始 X 坐标")
    parser.add_argument("-sy", type=int, default=DEFAULT_SY, help="起始 Y 坐标")
    parser.add_argument("-sz", type=int, default=DEFAULT_SZ, help="起始 Z 坐标")
    parser.add_argument("-t", "--tps", type=float, default=DEFAULT_TPS, help="Minecraft TPS")
    parser.add_argument("-m", "--mode", dest="place_mode", type=str, default=DEFAULT_PLACE_MODE,
                        help="放置方块的模式: rcon / mcfunction")
    parser.add_argument("--track-gap", type=int, default=DEFAULT_TRACK_GAP, help="轨道间隔格数")
    parser.add_argument("--auto-confirm", action="store_true", default=DEFAULT_AUTO_CONFIRM,
                        help="自动开始放置方块(较危险)")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> AppConfig:
    """合并命令行参数与默认值，生成最终配置对象"""
    return AppConfig(
        midi_file=args.midi_file,
        sx=args.sx,
        sy=args.sy,
        sz=args.sz,
        tps=args.tps,
        track_gap=args.track_gap,
        place_mode=args.place_mode,
        auto_confirm=args.auto_confirm
    )


def create_placer(place_mode: str):
    """放置器工厂：根据模式创建对应的放置实例，新增模式只需扩展分支"""
    if place_mode == "rcon":
        return RconBlockPlacer(
            host=SERVER_IP,
            port=RCON_PORT,
            pwd=RCON_PWD,
        )
    # 后续新增 mcfunction 模式，在这里加分支即可
    # elif place_mode == "mcfunction":
    #     return McFunctionPlacer(output_path=MCF_OUTPUT_PATH)
    else:
        raise ValueError(f"不支持的放置模式: {place_mode}")


def user_confirm(prompt: str, auto_confirm: bool) -> bool:
    """通用确认函数：自动确认直接返回True，否则等待用户输入"""
    if auto_confirm:
        return True
    confirm = input(prompt).strip()
    return confirm == "Y"


if __name__ == "__main__":
    LOGGER.info("Welcome to My Project.")

    args = parse_args()
    config = build_config(args)

    LOGGER.info("============INPUT============")
    LOGGER.info(f"Midi file: {config.midi_file}")
    LOGGER.info(f"TPS: {config.tps}")
    LOGGER.info(f"Starting position: ({config.sx}, {config.sy}, {config.sz})")
    LOGGER.info(f"Mode of placing blocks: {config.place_mode}")
    LOGGER.info(f"Track's gap: {config.track_gap}")
    LOGGER.info("=============END=============")

    LOGGER.info("正在解析MIDI文件...")
    midi_info = parse_midi(config.midi_file)
    LOGGER.info(f"解析完成 | MIDI总时长: {midi_info['total_duration'] / 1e6:.2f}s | "
                f"轨道数: {midi_info['num_tracks']} | PPQN: {midi_info['ticks_per_beat']}")

    LOGGER.info("正在将Midi信息转化为Mc方块信息...")
    block_data = transform_block(midi_info, TPS=config.tps)
    LOGGER.info("转换完成")

    maker = MakeBlock(config.sx, config.sy, config.sz, track_gap=config.track_gap)
    blocks = maker.build(block_data)
    track_len = maker.get_track_len()

    ex = config.sx + (midi_info['num_tracks'] - 1) * (config.track_gap + 1)
    ez = config.sz + track_len - 1

    LOGGER.info("=============信息统计=============")
    LOGGER.info(f"音乐时长: {midi_info['total_duration'] / 1e6:.2f}s  |  TPS: {config.tps}")
    LOGGER.info(f"放置模式: {config.place_mode}")
    LOGGER.info(f"轨道数: {midi_info['num_tracks']}  |  方块数量: {len(blocks)}")
    LOGGER.info(f"起始坐标: ({config.sx}, {config.sy}, {config.sz})  | "
                f"终点坐标: ({ex}, {config.sy}, {ez})")
    LOGGER.info("===============END==============")

    placer = create_placer(config.place_mode)

    if not user_confirm("确认开始放置？(Y/n): ", config.auto_confirm):
        LOGGER.info("已取消放置。")
        exit(0)

    with placer:
        placer.place_blocks(blocks)

    LOGGER.info("All work done.")