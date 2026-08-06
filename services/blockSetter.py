import time

from mcrcon import MCRcon

from utils.constants import BlockType, BlockEntry
from utils.logger import LOGGER


class BlockSetter:
    def __init__(self):
        self.mcr = None

    def connect(self, server_ip, rcon_port, rcon_pwd):
        LOGGER.info(f"正在连接到{server_ip}:{rcon_port}... ")
        self.mcr = MCRcon(server_ip, rcon_pwd, port=rcon_port)
        self.mcr.connect()
        LOGGER.info("连接成功")
        return 0

    def setBlock(self, block_type: BlockType, x, y, z, nbt=None, state=None):
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

        r = self.mcr.command(f"/setblock {x} {y} {z} {block_type}{state_cmd}{nbt_cmd}")
        print(f"Set {x} {y} {z}  R:{r}", end='\r', flush=True)
        return 0

    def setOneDelay(self, x, y, z):
        r1 = self.mcr.command(f"/setblock {x} {y} {z} minecraft:sticky_piston[facing=south]")
        r2 = self.mcr.command(f"/setblock {x} {y} {z + 1} minecraft:redstone_block")
        r3 = self.mcr.command(f"/setblock {x} {y} {z + 3} minecraft:redstone_wire")
        print(f"Set {x} {y} {z}  R:{r1 + r2 + r3}", end='\r', flush=True)
        return 0

    def setProgram(self, x, y, z, program):  # 设置noteblcok的音色
        blockIdMap = ['minecraft:dirt', 'minecraft:coarse_dirt', 'minecraft:podzol', 'minecraft:rooted_dirt',
                      'minecraft:clay', 'minecraft:terracotta', 'minecraft:moss_block', 'minecraft:red_nether_bricks',
                      'minecraft:light_blue_concrete', 'minecraft:polished_diorite', 'minecraft:amethyst_block',
                      'minecraft:iron_block', 'minecraft:oak_planks', 'minecraft:bone_block', 'minecraft:gold_block',
                      'minecraft:hay_block', 'minecraft:beehive', 'minecraft:dried_kelp_block', 'minecraft:netherrack',
                      'minecraft:quartz_block', 'minecraft:mushroom_stem', 'minecraft:bookshelf', 'minecraft:bricks',
                      'minecraft:mud_bricks', 'minecraft:oak_log', 'minecraft:white_wool', 'minecraft:shroomlight',
                      'minecraft:sea_lantern', 'minecraft:soul_sand', 'minecraft:blackstone', 'minecraft:obsidian',
                      'minecraft:glass', 'minecraft:oak_wood', 'minecraft:spruce_planks', 'minecraft:birch_planks',
                      'minecraft:jungle_planks', 'minecraft:acacia_planks', 'minecraft:dark_oak_planks',
                      'minecraft:purpur_block', 'minecraft:purpur_pillar', 'minecraft:cherry_planks',
                      'minecraft:mangrove_planks', 'minecraft:crimson_planks', 'minecraft:warped_planks',
                      'minecraft:chiseled_stone_bricks', 'minecraft:melon', 'minecraft:smooth_sandstone',
                      'minecraft:stone', 'minecraft:calcite', 'minecraft:light_gray_wool', 'minecraft:end_stone',
                      'minecraft:end_stone_bricks', 'minecraft:soul_soil', 'minecraft:cyan_wool', 'minecraft:sculk',
                      'minecraft:ancient_debris', 'minecraft:waxed_cut_copper', 'minecraft:waxed_exposed_cut_copper',
                      'minecraft:waxed_copper_block', 'minecraft:waxed_weathered_cut_copper', 'minecraft:copper_ore',
                      'minecraft:waxed_oxidized_copper', 'minecraft:diamond_block', 'minecraft:diamond_ore',
                      'minecraft:yellow_terracotta', 'minecraft:orange_terracotta', 'minecraft:red_terracotta',
                      'minecraft:brown_terracotta', 'minecraft:white_concrete', 'minecraft:light_gray_concrete',
                      'minecraft:gray_concrete', 'minecraft:black_concrete', 'minecraft:stripped_spruce_log',
                      'minecraft:bamboo_planks', 'minecraft:bamboo_block', 'minecraft:stripped_bamboo_block',
                      'minecraft:tinted_glass', 'minecraft:cherry_log', 'minecraft:iron_bars', 'minecraft:packed_mud',
                      'minecraft:emerald_block', 'minecraft:emerald_ore', 'minecraft:lapis_block',
                      'minecraft:lapis_ore', 'minecraft:purple_glazed_terracotta',
                      'minecraft:magenta_glazed_terracotta', 'minecraft:cyan_glazed_terracotta',
                      'minecraft:blue_glazed_terracotta', 'minecraft:ochre_froglight', 'minecraft:glowstone',
                      'minecraft:verdant_froglight', 'minecraft:crying_obsidian', 'minecraft:white_stained_glass',
                      'minecraft:netherite_block', 'minecraft:beacon', 'minecraft:pink_wool',
                      'minecraft:dripstone_block', 'minecraft:dead_tube_coral_block', 'minecraft:magenta_concrete',
                      'minecraft:soul_lantern', 'minecraft:shulker_box', 'minecraft:deepslate_emerald_ore',
                      'minecraft:reinforced_deepslate', 'minecraft:polished_blackstone', 'minecraft:barrel',
                      'minecraft:orange_concrete', 'minecraft:red_sandstone', 'minecraft:chiseled_quartz_block',
                      'minecraft:bamboo_mosaic', 'minecraft:crimson_stem', 'minecraft:acacia_log',
                      'minecraft:warped_stem', 'minecraft:prismarine_bricks', 'minecraft:lodestone',
                      'minecraft:raw_iron_block', 'minecraft:crafting_table', 'minecraft:crimson_hyphae',
                      'minecraft:warped_hyphae', 'minecraft:honeycomb_block', 'minecraft:bell',
                      'minecraft:polished_andesite', 'minecraft:lime_wool', 'minecraft:dark_prismarine',
                      'minecraft:birch_log', 'minecraft:polished_blackstone_bricks', 'minecraft:iron_trapdoor',
                      'minecraft:gilded_blackstone', 'minecraft:tuff', 'minecraft:sandstone']

        blockId = blockIdMap[program]
        self.mcr.command(f"/setblock {x} {y - 1} {z} {blockId}")  # 改变下方方块ID
        return 0

    def place_block(self, blocks: list[BlockEntry], show_progress: bool = True):
        """批量放置方块列表，支持进度显示"""
        begin_time = time.time()
        total = len(blocks)
        LOGGER.info(f"开始放置方块，共计{total}个")

        for i, block in enumerate(blocks):
            self.setBlock(block.blcok_id, block.x, block.y, block.z, nbt=block.nbt, state=block.state)
            if block.program >= 0:
                self.setProgram(block.x, block.y, block.z, block.program)

            if show_progress and i % 150 == 0:
                LOGGER.info(f"放置进度: {(i + 1) / total:.1f}%")

        LOGGER.info(f"所有方块放置完成, 耗时{time.time() - begin_time} s")

    def close(self):
        self.mcr.disconnect()
        LOGGER.info("连接断开")
        return 0
