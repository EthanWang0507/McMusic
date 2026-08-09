from abc import ABC, abstractmethod

from utils.constants import BlockEntry


class BlockPlacer(ABC):
    """放置方块的抽象类"""

    def setup(self) -> None:
        """初始化的方法"""
        pass

    @abstractmethod
    def place_blocks(self, blocks: list[BlockEntry], show_progress: bool = True) -> None:
        """放置多个方块的抽象方法"""
        pass

    def teardown(self) -> None:
        """清理资源的方法"""
        pass

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()
        return False