from .BaseCrypto import *


class LogisticKeyMixingCrypto(BaseCrypto):
    def __init__(self, key=None):
        """初始化加密类
        Args:
            key: 加密密钥字符串
        """
        super().__init__(key)
        # 将密钥字符串转换为ASCII码列表并扩展到13位
        self.key_list = self.__extend_key([ord(x) for x in key])

    def __extend_key(self, key_list):
        """扩展或压缩密钥到13位
        Args:
            key_list: 原始密钥列表
        Returns:
            扩展或压缩后的13位密钥列表
        """
        result = key_list.copy()
        if len(result) < 13:
            # 如果密钥长度小于13，使用递归公式扩展
            base = sum(result)
            while len(result) < 13:
                next_val = (base + len(result) * result[0]) % 256
                result.append(next_val)
                base = (base + next_val) % 256
        elif len(result) > 13:
            # 如果密钥长度大于13，通过叠加方式压缩
            extra = result[13:]
            for i, val in enumerate(extra):
                result[i % 12] = (result[i % 12] + val) % 256
            result = result[:13]
        return result

    def __get_image_matrix(self, img):
        """将图像转换为像素矩阵
        Args:
            img: 输入图像
        Returns:
            像素矩阵, 宽度, 高度, 是否为彩色图像
        """
        im = Image.fromarray(img)
        pix = im.load()
        color = isinstance(pix[0, 0], tuple)  # 判断是否为彩色图像
        w, h = im.size
        return [[pix[x, y] for y in range(h)] for x in range(w)], w, h, color

    def __init_params(self, key_list):
        """初始化混沌系统参数
        Args:
            key_list: 13位密钥列表
        Returns:
            S_x, S_y, L, L_y: 混沌系统的初始参数
        """
        # 将密钥分成3组，每组4个数
        G = [key_list[i:i + 4] for i in range(0, 12, 4)]
        g = []
        R = 1
        # 计算每组的加权和并累乘
        for i in range(3):
            s = sum(G[i][j] * (10 ** -(j + 1)) for j in range(4))
            g.append(s)
            R = (R * s) % 1

        # 计算密钥的异或和与算术和
        V1 = sum(key_list)
        V2 = key_list[0]
        for k in key_list[1:13]:
            V2 ^= k
        V = V2 / V1

        # 生成初始的混沌参数
        L = (R + key_list[12] / 256) % 1
        L_y = (V + key_list[12] / 256) % 1

        # 生成初始的x和y坐标
        S_x = round(((sum(g) + L) * 10 ** 4) % 256)
        S_y = round((V + V2 + L_y * 10 ** 4) % 256)

        return S_x, S_y, L, L_y

    def __update_values(self, x, y, C, key_list):
        """更新混沌系统的值
        Args:
            x, y: 当前的x,y值
            C: 当前的像素值
            key_list: 当前的密钥列表
        Returns:
            更新后的x, y, key_list
        """
        x = (x + C / 256 + key_list[8] / 256 + key_list[9] / 256) % 1
        y = (x + C / 256 + key_list[8] / 256 + key_list[9] / 256) % 1
        # 更新密钥列表
        for i in range(12):
            key_list[i] = (key_list[i] + key_list[12]) % 256
            key_list[12] ^= key_list[i]
        return x, y, key_list

    def encrypt(self, img: np.ndarray) -> np.ndarray:
        """加密图像
        Args:
            img: 输入图像
        Returns:
            加密后的图像
        """
        time_start = time.time()

        N = 256  # 像素值范围
        key_list = self.key_list.copy()
        # 初始化混沌系统参数
        S_x, S_y, L, L_y = self.__init_params(key_list)

        # 生成初始的混沌值
        x = 4 * S_x * (1 - S_x)  # Logistic映射
        y = 4 * S_y * (1 - S_y)
        C = round((L * L_y * 10 ** 4) % 256)
        C_rgb = [C] * 3  # 用于RGB三通道

        # 获取图像信息
        matrix, w, h, color = self.__get_image_matrix(img)
        encrypted = []

        # 处理每个像素
        for i in tqdm(range(w)):
            row = []
            for j in range(h):
                # 应用Logistic混沌映射
                while 0.2 < x < 0.8: x = 4 * x * (1 - x)
                while 0.2 < y < 0.8: y = 4 * y * (1 - y)

                # 生成随机数
                x_r = round((x * 10 ** 4) % 256)
                y_r = round((y * 10 ** 4) % 256)

                # 生成混淆值
                C1 = x_r ^ ((key_list[0] + x_r) % N) ^ ((S_x + key_list[1]) % N)
                C2 = x_r ^ ((key_list[2] + y_r) % N) ^ ((S_y + key_list[3]) % N)

                # 加密像素值
                if color:
                    # RGB图像处理
                    pixel = []
                    for k in range(3):
                        C_rgb[k] = ((key_list[4] + C1) % N) ^ ((key_list[5] + C2) % N) ^ \
                                   ((key_list[6] + matrix[i][j][k]) % N) ^ ((C_rgb[k] + key_list[7]) % N)
                        pixel.append(C_rgb[k])
                    row.append(tuple(pixel))
                    C = C_rgb[0]
                else:
                    # 灰度图像处理
                    C = ((key_list[4] + C1) % N) ^ ((key_list[5] + C2) % N) ^ \
                        ((key_list[6] + matrix[i][j]) % N) ^ ((C + key_list[7]) % N)
                    row.append(C)

                # 更新混沌参数
                x, y, key_list = self.__update_values(x, y, C, key_list)
            encrypted.append(row)

        # 转换回图像格式
        mode = "RGB" if color else "L"
        im = Image.new(mode, (w, h))
        for x in range(w):
            for y in range(h):
                im.putpixel((x, y), encrypted[x][y])

        time_end = time.time()
        print(f"Encryption time: {time_end - time_start:.2f}s")

        return np.array(im)

    def decrypt(self, img: np.ndarray, key) -> np.ndarray:
        """解密图像
        Args:
            img: 加密后的图像
            key: 解密密钥
        Returns:
            解密后的图像
        """
        time_start = time.time()

        N = 256
        # 从密钥生成初始参数
        key_list = self.__extend_key([ord(x) for x in key])
        S_x, S_y, L_x, L_y = self.__init_params(key_list)

        # 初始化混沌系统
        x = 4 * S_x * (1 - S_x)
        y = 4 * L_x * (1 - S_y)
        C = round((L_x * L_y * 10 ** 4) % 256)
        I_prev = [C] * 4  # [I, I_r, I_g, I_b] 用于存储前一个像素值

        # 获取图像信息
        matrix, w, h, color = self.__get_image_matrix(img)
        decrypted = []

        # 处理每个像素
        for i in tqdm(range(w)):
            row = []
            for j in range(h):
                # 应用Logistic映射，加入最大迭代次数避免死循环
                max_iters = 100
                count = 0
                while 0.2 < x < 0.8 and count < max_iters:
                    x = 4 * x * (1 - x)
                    count += 1

                count = 0
                while 0.2 < y < 0.8 and count < max_iters:
                    y = 4 * y * (1 - y)
                    count += 1

                # 生成随机数
                x_r = round((x * 10 ** 4) % 256)
                y_r = round((y * 10 ** 4) % 256)

                # 生成混淆值
                C1 = x_r ^ ((key_list[0] + x_r) % N) ^ ((S_x + key_list[1]) % N)
                C2 = x_r ^ ((key_list[2] + y_r) % N) ^ ((S_y + key_list[3]) % N)

                # 解密像素值
                if color:
                    # RGB图像处理
                    pixel = []
                    for k in range(3):
                        I = ((((key_list[4] + C1) % N) ^ ((key_list[5] + C2) % N) ^ \
                              ((I_prev[k + 1] + key_list[7]) % N) ^ matrix[i][j][k]) + N - key_list[6]) % N
                        I_prev[k + 1] = matrix[i][j][k]
                        pixel.append(I)
                    row.append(tuple(pixel))
                    x, y, key_list = self.__update_values(x, y, matrix[i][j][0], key_list)
                else:
                    # 灰度图像处理
                    I = ((((key_list[4] + C1) % N) ^ ((key_list[5] + C2) % N) ^ \
                          ((I_prev[0] + key_list[7]) % N) ^ matrix[i][j]) + N - key_list[6]) % N
                    I_prev[0] = matrix[i][j]
                    row.append(I)
                    x, y, key_list = self.__update_values(x, y, matrix[i][j], key_list)
            decrypted.append(row)

        # 转换回图像格式
        mode = "RGB" if color else "L"
        im = Image.new(mode, (w, h))
        for x in range(w):
            for y in range(h):
                im.putpixel((x, y), decrypted[x][y])

        time_end = time.time()
        print(f"Decryption time: {time_end - time_start:.2f}s")

        return np.array(im)


if __name__ == "__main__":
    # 测试代码
    key = "test"
    logistic = LogisticKeyMixingCrypto(key)
    img = cv2.imread("../assets/leno.bmp")
    img_encrypted = logistic.encrypt(img)
    cv2.imshow("encrypted", img_encrypted)
    cv2.waitKey(0)

    img_decrypted = logistic.decrypt(img_encrypted, key)
    cv2.imshow("decrypted", img_decrypted)
    cv2.waitKey(0)