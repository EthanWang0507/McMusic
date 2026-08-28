"""
McMusic Web Server - Flask 后端
提供静态文件服务和 REST API，对接业务逻辑层
"""
import os
import json
from dataclasses import dataclass, field
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

# 业务逻辑
from services.parse_midi import parse_midi
from services.transform_block import transform_block
from services.make_block import MakeBlock
from services.block_placer.placer import create_placer

# ===================== 配置 =====================
BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / "web"
TEMP_DIR = BASE_DIR / "data" / "temp"
DEFAULTS_FILE = BASE_DIR / "config" / "defaults.json"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

BUILTIN_DEFAULTS = {
    "tps": 20.0, "track_gap": 3, "sx": 0, "sy": 0, "sz": 0,
    "place_mode": "rcon", "auto_confirm": False,
    "rcon_host": "127.0.0.1", "rcon_port": 25575, "rcon_pwd": "",
    "rcon_auto_unload": True, "mcfunction_output": "output.mcfunction"
}

@dataclass
class ParseResult:
    ex: int = 0
    ey: int = 0
    ez: int = 0
    maker: MakeBlock = field(default_factory=lambda: MakeBlock(sx=0, sy=0, sz=0))
    midi_info: dict = field(default_factory=lambda: {})

@dataclass
class GlobalContext:
    sx: int = 0
    sy: int = 0
    sz: int = 0
    track_gap: int = 3
    tps: float = 20.0
    parse_result: ParseResult = field(default_factory=lambda: ParseResult())

app = Flask(__name__, static_folder=None)
global_context = GlobalContext()

# ===================== 静态文件 =====================
@app.route("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(WEB_DIR, filename)


# ===================== 默认配置 API =====================
@app.route("/api/defaults", methods=["GET"])
def get_defaults():
    """获取默认配置"""
    defaults = dict(BUILTIN_DEFAULTS)
    if DEFAULTS_FILE.exists():
        try:
            with open(DEFAULTS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            defaults.update(saved)
        except (json.JSONDecodeError, IOError):
            pass
    return jsonify(defaults)


@app.route("/api/defaults", methods=["POST"])
def save_defaults():
    """保存默认配置"""
    data = request.get_json()
    defaults = dict(BUILTIN_DEFAULTS)
    if DEFAULTS_FILE.exists():
        try:
            with open(DEFAULTS_FILE, "r", encoding="utf-8") as f:
                defaults.update(json.load(f))
        except (json.JSONDecodeError, IOError):
            pass
    defaults.update(data)
    DEFAULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DEFAULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(defaults, f, indent=2, ensure_ascii=False)
    return jsonify({"success": True})


# ===================== MIDI 解析 API =====================
@app.route("/api/parse", methods=["POST"])
def api_parse():
    """
    解析 MIDI 文件，返回音乐信息和方块统计
    接收：multipart/form-data，包含 file 字段 + 可选参数 tps/sx/sy/sz/track_gap
    """
    if "file" not in request.files:
        return jsonify({"error": "未上传文件"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "文件名为空"}), 400

    # 读取参数
    tps = float(request.form.get("tps", 20.0))
    sx = int(request.form.get("sx", 0))
    sy = int(request.form.get("sy", 0))
    sz = int(request.form.get("sz", 0))
    track_gap = int(request.form.get("track_gap", 3))

    global_context.sx = sx
    global_context.sy = sy
    global_context.sz = sz
    global_context.tps = tps
    global_context.track_gap = track_gap

    # 保存临时文件
    if file.filename is None:
        return jsonify({"error": "无法获取文件名"}), 400
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # 解析 MIDI
        midi_info = parse_midi(tmp_path)
        block_data = transform_block(midi_info, TPS=tps)
        maker = MakeBlock(sx, sy, sz, track_gap=track_gap)
        maker.build(block_data)
        blocks = maker.get_blocks()
        track_len = maker.get_track_len()

        ex = sx + (midi_info["num_tracks"] - 1) * (track_gap + 1)
        ez = sz + track_len - 1

        global_context.parse_result = ParseResult(
            ex=ex, ey=sy, ez=ez,
            maker=maker, midi_info=midi_info
        )

        result = {
            "duration": round(midi_info["total_duration"] / 1e6, 2),
            "tracks": midi_info["num_tracks"],
            "ppqn": midi_info["ticks_per_beat"],
            "block_count": len(blocks),
            "start_x": sx, "start_y": sy, "start_z": sz,
            "end_x": ex, "end_y": sy, "end_z": ez,
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.unlink(tmp_path)


# ===================== RCON 放置 API =====================
@app.route("/api/place/<mode>", methods=["POST"])
def api_place_rcon(mode):
    """
    RCON 模式放置方块
    接收：JSON，包含 file(base64) 或 file_path + 配置参数
    简化版：前端先调用 /api/parse，然后把解析结果和配置传过来
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体为空"}), 400

    if not global_context.parse_result:
        return jsonify({"error": "请先调用 /api/parse"}), 400

    try:
        if mode == "rcon":
            host = data.get("rcon_host", "127.0.0.1")
            port = int(data.get("rcon_port", 25575))
            pwd = data.get("rcon_pwd", "")
            config = {
                'host': host,
                'port': port,
                'pwd': pwd
            }
        else:
            return jsonify({"error": "未知的放置模式"}), 400

        sx, sy, sz = global_context.sx, global_context.sy, global_context.sz
        track_gap = global_context.track_gap
        midi_info = global_context.parse_result.midi_info
        maker = global_context.parse_result.maker
        blocks = maker.get_blocks()
        
        # 放置
        placer = create_placer(mode, config)
        with placer:
            placer.place_blocks(blocks)

        return jsonify({
            "success": True,
            "block_count": len(blocks),
            "start": (sx, sy, sz),
            "end": (sx + (midi_info["num_tracks"] - 1) * (track_gap + 1), sy, sz + maker.get_track_len() - 1)
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


# ===================== mcfunction 导出 API =====================
@app.route("/api/place/mcfunction", methods=["POST"])
def api_place_mcfunction():
    """
    导出 mcfunction 文件
    接收：JSON，包含 midi_path + 配置参数
    返回：文件下载
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体为空"}), 400

    try:
        tps = float(data.get("tps", 20.0))
        sx = int(data.get("sx", 0))
        sy = int(data.get("sy", 0))
        sz = int(data.get("sz", 0))
        track_gap = int(data.get("track_gap", 3))
        output_name = data.get("mcfunction_output", "output.mcfunction")
        midi_path = data.get("midi_path")

        if not midi_path or not Path(midi_path).exists():
            return jsonify({"error": "MIDI 文件路径无效"}), 400

        # 解析并构建方块
        midi_info = parse_midi(midi_path)
        block_data = transform_block(midi_info, TPS=tps)
        maker = MakeBlock(sx, sy, sz, track_gap=track_gap)
        maker.build(block_data)
        blocks = maker.get_blocks()

        # 生成 mcfunction
        output_path = TEMP_DIR / output_name
        with open(output_path, "w", encoding="utf-8") as f:
            for block in blocks:
                cmd = f"setblock {block.x} {block.y} {block.z} {block.block_id}"
                f.write(cmd + "\n")

        return jsonify({
            "success": True,
            "block_count": len(blocks),
            "output_path": str(output_path),
            "download_url": f"/download/{output_name}"
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/download/<filename>")
def download_file(filename):
    """下载生成的 mcfunction 文件"""
    return send_from_directory(TEMP_DIR, filename, as_attachment=True)


# ===================== 健康检查 =====================
@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("=" * 50)
    print("  McMusic Web Server")
    print("  访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=False)
