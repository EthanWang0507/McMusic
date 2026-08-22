from mcrcon import MCRcon
from config.config import SERVER_IP, RCON_PORT, RCON_PWD

mcr = MCRcon(SERVER_IP, RCON_PWD, port=RCON_PORT)
mcr.connect()
# forceload Marked chunk [0, 0] in minecraft:overworld to be force loaded
# Unmarked chunk [0, 0] in minecraft:overworld for force loading
# setblock Changed the block at 0, 0, 0
print()