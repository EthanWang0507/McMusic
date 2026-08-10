from dataclasses import dataclass, field


class BlockType:
    WIRE = "minecraft:redstone_wire"
    REDSTONE_LAMP = "minecraft:redstone_lamp"
    NOTE_BLOCK = "extendednoteblock:extended_note_block"
    REPEATER = "minecraft:repeater"
    COMMAND_BLOCK = "minecraft:command_block"
    LEVER = "minecraft:lever"
    STICKY_PISTON = "minecraft:sticky_piston"
    REDSTONE_BLOCK = "minecraft:redstone_block"


class CommandSuccessResult:
    FORCELOAD_ADD = "to be force loaded"
    FORCELOAD_REMOVE = "for force loading"
    SETBLOCK = "Changed the block at"

    COMMON_ERROR_KEYWORDS = [
        "error", "unknown", "cannot", "invalid",
        "not found", "not loaded", "outside of the world"
    ]

@dataclass
class BlockEntry:
    block_id: BlockType
    x: int
    y: int
    z: int
    program: int = field(default=-1)
    nbt: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)


BLOCK_ID_MAP = ['minecraft:dirt', 'minecraft:coarse_dirt', 'minecraft:podzol', 'minecraft:rooted_dirt',
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
