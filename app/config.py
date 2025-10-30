"""
配置类
"""
import os
from pathlib import Path


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 默认保存路径
        self.save_path = os.path.join(Path(__file__).resolve().parent.parent, "downloads")

        # 确保目录存在
        os.makedirs(self.save_path, exist_ok=True)

        self._initialized = True

    def set_save_path(self, path):
        """设置保存路径"""
        self.save_path = path
        os.makedirs(self.save_path, exist_ok=True)


# 全局配置实例
config = Config()