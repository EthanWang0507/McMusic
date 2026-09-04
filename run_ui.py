"""
McMusic UI 入口
启动 Flask 后端服务器并自动打开浏览器
"""
import threading
import time
import webbrowser
from server import app


def open_browser():
    """延迟打开浏览器，确保服务器已启动"""
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    print("=" * 50)
    print("  McMusic - MIDI 红石音乐生成器")
    print("  正在启动 Web 界面...")
    print("  访问地址: http://127.0.0.1:5000")
    print("  按 Ctrl+C 停止服务器")
    print("=" * 50)

    # 后台线程打开浏览器
    # threading.Thread(target=open_browser, daemon=True).start()

    # 启动 Flask
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
