from .BaseCrypto import *

class LogisticCrypto(BaseCrypto):
    def __init__(self, key=None):
        """
        key: 元组 (r, x0)
        r: logistic参数，取值范围[3.57,4]
        x0: 初始值，取值范围[0,1]
        """
        super().__init__(key)

    def __get_image_matrix(self, img):
        im = Image.fromarray(img)
        pix = im.load()
        color = isinstance(pix[0, 0], tuple)
        w, h = im.size
        return [[pix[x, y] for y in range(h)] for x in range(w)], w, h, color

    def __logistic_sequence(self, length, key):
        """生成logistic混沌序列"""
        sequence = []
        r, x = key

        # 丢弃前200个值以消除瞬态效应
        for _ in range(200):
            x = r * x * (1 - x)

        # 生成所需的序列
        for _ in range(length):
            x = r * x * (1 - x)
            sequence.append(int(x * 256))

        return sequence

    def __shuffle_matrix(self, matrix, w, h, chaos_seq, reverse=False):
        """使用混沌序列对矩阵进行置乱"""
        # 创建位置索引
        indices = list(range(w * h))

        # 使用混沌序列进行置乱
        if not reverse:
            for i in range(w * h - 1, 0, -1):
                j = chaos_seq[i] % (i + 1)
                indices[i], indices[j] = indices[j], indices[i]
        else:
            for i in range(1, w * h):
                j = chaos_seq[i] % (i + 1)
                indices[i], indices[j] = indices[j], indices[i]

        # 重构矩阵
        result = [[0 for _ in range(h)] for _ in range(w)]
        for idx in range(w * h):
            orig_x, orig_y = indices[idx] // h, indices[idx] % h
            new_x, new_y = idx // h, idx % h
            result[new_x][new_y] = matrix[orig_x][orig_y]

        return result

    def __process_image(self, img, operation, key):
        """统一的图像处理函数，用于加密和解密"""
        time_start = time.time()

        # 获取图像信息
        matrix, w, h, color = self.__get_image_matrix(img)

        # 生成用于置乱的混沌序列
        shuffle_seq = self.__logistic_sequence(w * h, key)

        # 生成用于扩散的混沌序列
        diffuse_seq = self.__logistic_sequence(w * h * (3 if color else 1), key)

        # 置乱过程
        if operation == 'encrypt':
            matrix = self.__shuffle_matrix(matrix, w, h, shuffle_seq)

        # 扩散过程
        processed = []
        prev = 0  # 前一个像素值用于扩散
        seq_index = 0

        for i in tqdm(range(w)):
            row = []
            for j in range(h):
                if color:
                    pixel = []
                    for k in range(3):
                        # 使用异或运算和扩散进行加密/解密
                        if operation == 'encrypt':
                            processed_value = (matrix[i][j][k] ^ diffuse_seq[seq_index] ^ prev) % 256
                        else:
                            processed_value = (matrix[i][j][k] ^ diffuse_seq[seq_index] ^ prev) % 256
                        pixel.append(processed_value)
                        prev = processed_value if operation == 'encrypt' else matrix[i][j][k]
                        seq_index += 1
                    row.append(tuple(pixel))
                else:
                    if operation == 'encrypt':
                        processed_value = (matrix[i][j] ^ diffuse_seq[seq_index] ^ prev) % 256
                    else:
                        processed_value = (matrix[i][j] ^ diffuse_seq[seq_index] ^ prev) % 256
                    row.append(processed_value)
                    prev = processed_value if operation == 'encrypt' else matrix[i][j]
                    seq_index += 1
            processed.append(row)

        matrix = processed

        # 逆置乱过程（解密时）
        if operation == 'decrypt':
            matrix = self.__shuffle_matrix(matrix, w, h, shuffle_seq, reverse=True)

        # 构建处理后的图像
        mode = "RGB" if color else "L"
        im = Image.new(mode, (w, h))
        for x in range(w):
            for y in range(h):
                im.putpixel((x, y), matrix[x][y])

        time_end = time.time()
        print(f"{operation.capitalize()} time: {time_end - time_start:.2f}s")

        return np.array(im)

    def encrypt(self, img: np.ndarray) -> np.ndarray:
        return self.__process_image(img, 'encrypt', self.key)

    def decrypt(self, img: np.ndarray, key) -> np.ndarray:
        return self.__process_image(img, 'decrypt', key)


if __name__ == "__main__":
    key = (3.8, 0.8)
    logistic = LogisticCrypto(key)
    img = cv2.imread("../assets/hust.jpg")
    img_encrypted = logistic.encrypt(img)
    cv2.imshow("encrypted", img_encrypted)
    cv2.waitKey(0)

    # draw_intensity_histogram(img, img_encrypted)

    img_decrypted = logistic.decrypt(img_encrypted, (3.8, 0.8))
    cv2.imshow("decrypted", img_decrypted)
    cv2.waitKey(0)
