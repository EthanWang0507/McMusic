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


@dataclass
class BlockEntry:
    block_id: BlockType
    x: float
    y: float
    z: float
    program: int = field(default=-1)
    nbt: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)