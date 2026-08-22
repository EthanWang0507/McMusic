from dotenv import load_dotenv
load_dotenv()

import os

# Mc Rcon Config
SERVER_IP = os.getenv("SERVER_IP", "127.0.0.1")
RCON_PORT = int(os.getenv("RCON_PORT", 25575))
RCON_PWD = os.getenv("RCON_PWD", "")

DEFAULT_SX = 0
DEFAULT_SY = 0
DEFAULT_SZ = 0
DEFAULT_TPS = 20.0
DEFAULT_TRACK_GAP = 3
DEFAULT_PLACE_MODE = "rcon"
DEFAULT_AUTO_CONFIRM = False