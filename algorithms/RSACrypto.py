import struct
from typing import Tuple
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from .BaseCrypto import *


class RSACrypto(BaseCrypto):
    def __init__(self, key: RSA.RsaKey):
        super().__init__(key)
        # 根据密钥长度动态设置块大小
        self.encrypted_block_size = key.size_in_bits() // 8  # 加密后的块大小(bytes)
        self.block_size = self.encrypted_block_size - 42  # PKCS1_OAEP填充需要额外41字节，预留42字节以确保安全

    def __process_blocks(self, data: bytes, key: RSA.RsaKey, mode: str) -> bytes:
        """分块处理数据"""
        cipher = PKCS1_OAEP.new(key)
        result = []

        if mode == 'encrypt':
            # 计算填充后的数据长度
            pad_length = self.block_size - (len(data) % self.block_size)
            if pad_length < self.block_size:
                # 添加PKCS7填充
                data += bytes([pad_length] * pad_length)

            # 分块加密
            for i in tqdm(range(0, len(data), self.block_size)):
                block = data[i:i + self.block_size]
                encrypted_block = cipher.encrypt(block)
                result.append(encrypted_block)

            # 合并加密后的数据
            encrypted_data = b''.join(result)

            return encrypted_data

        else:  # decrypt
            # 分块解密
            for i in tqdm(range(0, len(data), self.encrypted_block_size)):
                block = data[i:i + self.encrypted_block_size]
                try:
                    decrypted_block = cipher.decrypt(block)
                    result.append(decrypted_block)
                except ValueError:
                    continue  # 跳过无效的块

            # 合并解密后的数据
            decrypted_data = b''.join(result)

            # 去除PKCS7填充
            if decrypted_data:
                pad_length = decrypted_data[-1]
                if pad_length < self.block_size:
                    decrypted_data = decrypted_data[:-pad_length]

            return decrypted_data

    def __preprocess_image(self, img: np.ndarray) -> np.ndarray:
        return np.clip(img, 0, 255).astype(np.uint8)

    def encrypt(self, img: np.ndarray) -> np.ndarray:
        """加密图像"""
        time_start = time.time()

        # 预处理
        img = self.__preprocess_image(img)
        height, width = img.shape[:2]
        channels = 1 if len(img.shape) == 2 else img.shape[2]

        # 准备图像信息头
        header = struct.pack('!III', height, width, channels)

        # 准备图像数据
        img_bytes = img.tobytes()

        # 合并头部和图像数据
        data = header + img_bytes

        # 加密
        encrypted_data = self.__process_blocks(data, self.key, 'encrypt')

        # 计算新的图像维度
        total_bytes = len(encrypted_data)
        new_height = int(np.sqrt(total_bytes / 3)) + 1  # 确保有足够空间
        new_width = int(np.ceil(total_bytes / (new_height * 3)))

        # 填充数据至完整大小
        padded_data = encrypted_data + b'\0' * (new_height * new_width * 3 - total_bytes)

        # 重组为图像格式
        encrypted = np.frombuffer(padded_data, dtype=np.uint8).reshape(new_height, new_width, 3)

        time_end = time.time()
        print(f"Encryption time: {time_end - time_start:.2f}s")

        return encrypted

    def decrypt(self, img: np.ndarray, key: RSA.RsaKey) -> np.ndarray:
        """解密图像"""
        time_start = time.time()

        # 将图像转换为字节流
        encrypted_data = img.tobytes()

        # 解密
        decrypted_data = self.__process_blocks(encrypted_data, key, 'decrypt')

        # 使用默认值作为备选
        default_height, default_width = img.shape[:2]
        default_channels = 1 if len(img.shape) == 2 else img.shape[2]

        try:
            # 尝试解析头部信息
            header = struct.unpack('!III', decrypted_data[:12])
            height, width, channels = header
            # 如果解析出的值不合理，使用默认值
            if height <= 0 or width <= 0 or channels <= 0 or channels > 4:
                height, width, channels = default_height, default_width, default_channels
        except:
            # 如果解析失败，使用默认值
            height, width, channels = default_height, default_width, default_channels

        # 解析图像数据
        img_data = decrypted_data[12:]
        expected_size = height * width * channels

        # 如果数据不足，用随机数据填充
        if len(img_data) < expected_size:
            img_data = img_data + np.random.randint(0, 256, expected_size - len(img_data), dtype=np.uint8).tobytes()

        try:
            if channels == 1:
                decrypted = np.frombuffer(img_data, dtype=np.uint8)[:expected_size].reshape(height, width)
            else:
                decrypted = np.frombuffer(img_data, dtype=np.uint8)[:expected_size].reshape(height, width, channels)
        except:
            # 如果重构图像失败，返回随机噪声图像
            decrypted = np.random.randint(0, 256, (height, width, channels), dtype=np.uint8)

        decrypted = self.__preprocess_image(decrypted)

        time_end = time.time()
        print(f"Decryption time: {time_end - time_start:.2f}s")

        return decrypted

    @staticmethod
    def generate_keypair(key_size: int = 2048) -> Tuple[RSA.RsaKey, RSA.RsaKey]:
        """生成RSA密钥对"""
        key = RSA.generate(key_size)
        return key.publickey(), key


if __name__ == "__main__":
    # 读取图像
    img = cv2.imread("../assets/hust.jpg")

    # 创建 RSA 密钥对
    public_key, private_key = RSACrypto.generate_keypair()

    # 创建 RSA 加密算法实例
    rsa = RSACrypto(public_key)

    # 加密图像
    print("Encrypting image...")
    encrypted_image = rsa.encrypt(img)
    cv2.imshow("Encrypted Image", encrypted_image)
    cv2.waitKey(0)

    # 解密图像
    print("Decrypting image...")
    decrypted_image = rsa.decrypt(encrypted_image, key=private_key)
    cv2.imshow("Decrypted Image", decrypted_image)
    cv2.waitKey(0)