import os

# Mc Rcon Config
SERVER_IP = os.getenv("SERVER_IP", "127.0.0.1")
RCON_PORT = int(os.getenv("RCON_PORT", 25575))
RCON_PWD = os.getenv("RCON_PWD", "")


def validate_rcon_config():
    missing = []
    if not SERVER_IP:
        missing.append("SERVER_IP")
    if not RCON_PWD:
        missing.append("RCON_PWD")
    if missing:
        raise ValueError(f"Requried arguments {', '.join(missing)} is missing. Please check .env")
