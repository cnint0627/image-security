import numpy as np
import cv2
import time
from abc import abstractmethod
from tqdm.notebook import tqdm  # 专门用于notebook的tqdm
from PIL import Image

# 所有算法必须实现该接口
class BaseCrypto:
    def __init__(self, key):    # key -> 加密用的 key
        assert key is not None, "初始化时请至少传入一个加密用的key"
        self.key = key

    @abstractmethod
    def encrypt(self, img: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def decrypt(self, img: np.ndarray, key) -> np.ndarray:  # key -> 解密用的 key
        pass