import logging
import json
import colorama
from typing import Union
from colorama import Fore

colorama.init(autoreset=True)

# 固定字段颜色
COLOR_TIME = Fore.BLUE
COLOR_LOCATION = Fore.CYAN
COLOR_MESSAGE = Fore.WHITE

# 各日志级别名称的颜色
LEVEL_COLOR_MAP = {
    logging.DEBUG:    Fore.LIGHTBLACK_EX,  # DEBUG：灰色（亮黑=终端标准灰色）
    logging.INFO:     Fore.GREEN,          # INFO：绿色
    logging.WARNING:  Fore.LIGHTYELLOW_EX, # WARNING：亮黄色
    logging.ERROR:    Fore.LIGHTRED_EX,    # ERROR：亮红色
    logging.CRITICAL: Fore.RED,            # CRITICAL：深红色
}

def ansi_color_to_hex(ansi: str):
    n = int(ansi[-3:-1])
    if (n < 30 and n > 37 and n < 90 and n > 97):
        raise ValueError("仅支持字体颜色转换")
    if (30 <= n and n <= 37):
        ANSI_HEX_MAP = ['#000000', '#FF0000', '#008000', '#FFFF00', '#0000FF', '#00FFFF', '#800080', '#FFFFFF']
        return ANSI_HEX_MAP[n - 30]
    else:
        ANSI_HEX_MAP = ['#808080', '#FF1B00', '#90EE90', '#FFFFE0', '#ADD8E6', '#E0FFFF', '#FFB6C1', '#FFFFFF']
        return ANSI_HEX_MAP[n - 90]

class SSELogHandler(logging.Handler):
    """把日志从"输出到控制台"改为"调用 send 走 SSE"；格式完全由挂载的 Formatter 决定。"""

    def __init__(self, push, event="msg", level=logging.DEBUG):
        super().__init__(level)
        self._push = push
        self._event = event

    def emit(self, record):
        try:
            text = self.format(record)
            for line in text.splitlines():
                self._push(line, self._event)  # 发送格式化json的日志信息
        except Exception:
            self.handleError(record)


class ColoredFormatter(logging.Formatter):
    def __init__(self, *args, use_color=True, **kwargs):
            super().__init__(*args, **kwargs)
            self.use_color = use_color

    def format(self, record):
        # 获取当前级别对应的颜色
        level_color = LEVEL_COLOR_MAP.get(record.levelno, Fore.WHITE)

        def c(color, text):
            return f"{color}{text}{Fore.RESET}" if self.use_color else text

        # 分别给每一部分上色，括号天然和代码位置同色
        time_part = c(COLOR_TIME, f"[{self.formatTime(record, self.datefmt)}]")
        level_part = c(level_color, f"[{record.levelname}]")
        location_part = c(COLOR_LOCATION, f"({record.filename}/{record.funcName}:{record.lineno})")
        message_part = c(COLOR_MESSAGE, record.getMessage())

        # 拼接整行日志
        log_line = ""
        log_json = {}
        if self.use_color:
            log_line = f"{time_part} {level_part} {location_part} {message_part}"
        else:
            log_json = {time_part: ansi_color_to_hex(COLOR_TIME), 
                        level_part: ansi_color_to_hex(level_color),
                        location_part: ansi_color_to_hex(COLOR_LOCATION),
                        message_part: ansi_color_to_hex(COLOR_MESSAGE)}

        # 兼容异常堆栈输出（报错时的堆栈信息也用白色）
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            if self.use_color:
                log_line += "\n" + c(COLOR_MESSAGE, exc_text)
            else:
                log_json.update({f"\n{exc_text}": ansi_color_to_hex(COLOR_MESSAGE)})


        return log_line if len(log_line) else json.dumps(log_json)


def setup_global_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = False  # 禁止传递到根logger，避免重复输出
    logger.setLevel(level)

    # 创建控制台输出处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # 应用自定义彩色格式
    formatter = ColoredFormatter(datefmt="%H:%M:%S")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


LOGGER = setup_global_logger("McMusic", logging.DEBUG)

if __name__ == "__main__":
    LOGGER.debug('This is a debug message.')
    LOGGER.info('This is an info message.')
    LOGGER.warning('This is a warning message.')
    LOGGER.error('This is an error message.')
    LOGGER.critical('This is a critical message.')