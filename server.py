"""
McMusic Web Server - Flask 后端
提供静态文件服务和 REST API，对接业务逻辑层
"""
import os
import time
import json
from dataclasses import dataclass, field
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response

# 业务逻辑
from utils.logger import LOGGER, SSELogHandler, ColoredFormatter
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
    default: bool = True
    ex: int = 0
    ey: int = 0
    ez: int = 0
    maker: MakeBlock = field(default_factory=lambda: MakeBlock(0, 0, 0))
    midi_info: dict = field(default_factory=lambda: {})

@dataclass
class GlobalContext:
    sx: int = 0
    sy: int = 0
    sz: int = 0
    track_gap: int = 3
    tps: float = 20.0
    parse_result: ParseResult = field(default_factory=lambda: ParseResult())
    placer_message: list = field(default_factory=list)  # 存储放置器的消息

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
    # 重置全局变量
    global global_context
    global_context = GlobalContext()

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
            default=False,
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


# ===================== 获取消息 API =====================
def send(msg, type) -> None:
    if type == 'close':
        global_context.placer_message.append(type)
        return
    out_msg = "event: %s\ndata: %s\n\n"%(type, msg)
    global_context.placer_message.append(out_msg)

@app.route("/api/getMsg")
def api_get_msg():
    """
    获取放置器的消息
    """
    send(json.dumps({'Hello Client.': "#7AA2F7"}), 'msg')
    def stream():
        cur_idx = 0
        try:
            while True:
                messages = global_context.placer_message
                if cur_idx < len(messages):
                    msg = messages[cur_idx]
                    cur_idx += 1
                    if msg == 'close':
                        break
                    # WSGI 要求 yield bytes；统一转字符串后编码，兼容 int/float
                    if not isinstance(msg, str):
                        msg = str(msg)
                    yield msg.encode("utf-8")
                else:
                    time.sleep(0.1)
        except GeneratorExit:
            # 浏览器关闭 EventSource 时生成器被关闭，直接结束
            return

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用代理缓冲
            "Connection": "keep-alive",
        },
    )

# ===================== 放置 API =====================
@app.route("/api/place/<mode>", methods=["POST"])
def api_place_rcon(mode):
    """
    放置方块
    接收：JSON，包含 file(base64) 或 file_path + 配置参数
    简化版：前端先调用 /api/parse，然后把解析结果和配置传过来
    """
    sse_log_handler = SSELogHandler(send)
    sse_log_handler.setFormatter(ColoredFormatter(datefmt="%H:%M:%S", use_color=False))
    LOGGER.addHandler(sse_log_handler)


    # 每次放置前清空历史消息，保证新建立的 SSE 流从本次放置开始读
    global_context.placer_message.clear()
    data = request.get_json()
    if not data:
        LOGGER.error("请求体为空")
        return jsonify({"error": "请求体为空"}), 400

    if global_context.parse_result.default:
        LOGGER.error("请先调用 /api/parse")
        return jsonify({"error": "请先调用 /api/parse"}), 400

    try:
        begin_time = time.time()
        if mode == "rcon":
            LOGGER.info("RCON 模式")
            host = data.get("host", "127.0.0.1")
            port = int(data.get("port", 25575))
            pwd = data.get("pwd", "")
            config = {
                'host': host,
                'port': port,
                'pwd': pwd
            }
        else:
            LOGGER.error("未知的放置模式")
            return jsonify({"error": "未知的放置模式"}), 400

        LOGGER.info("开始获取配置信息...")
        sx, sy, sz = global_context.sx, global_context.sy, global_context.sz
        track_gap = global_context.track_gap
        midi_info = global_context.parse_result.midi_info
        maker = global_context.parse_result.maker
        blocks = maker.get_blocks()
        
        # 放置
        LOGGER.info("初始化放置器...")
        placer = create_placer(mode, config, send_callback=send)
        with placer:
            LOGGER.info("开始放置...")
            placer.place_blocks(blocks)
        send(json.dumps({f"ヾ (≧∇≦*) ｼ 放置完成  耗时:{time.time() - begin_time} s": "#9ECE6A"}), 'msg')
        send("", 'done')
        send("", 'close')

        return jsonify({
            "success": True,
            "block_count": len(blocks),
            "start": (sx, sy, sz),
            "end": (sx + (midi_info["num_tracks"] - 1) * (track_gap + 1), sy, sz + maker.get_track_len() - 1)
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500
    finally:
        LOGGER.removeHandler(sse_log_handler)


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
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
