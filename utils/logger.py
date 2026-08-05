import logging
import colorama
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


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # 获取当前级别对应的颜色
        level_color = LEVEL_COLOR_MAP.get(record.levelno, Fore.WHITE)

        # 分别给每一部分上色，括号天然和代码位置同色
        time_part = f"{COLOR_TIME}[{self.formatTime(record, self.datefmt)}]"
        level_part = f"{level_color}[{record.levelname}]"
        location_part = f"{COLOR_LOCATION}({record.filename}/{record.funcName}:{record.lineno})"
        message_part = f"{COLOR_MESSAGE}{record.getMessage()}"

        # 拼接整行日志
        log_line = f"{time_part} {level_part} {location_part} {message_part}"

        # 兼容异常堆栈输出（报错时的堆栈信息也用白色）
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            log_line += f"\n{COLOR_MESSAGE}{exc_text}"

        return log_line


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