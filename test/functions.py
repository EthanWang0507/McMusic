import math
from typing import Any


def is_integer_loose(value: Any) -> bool:
    """
    宽松模式判断整数（接受int和float形式的整数）

    Args:
        value: 待检测的值

    Returns:
        bool: 是否为数值型整数
    """
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return not (math.isnan(value) or math.isinf(value)) and value.is_integer()
    return False