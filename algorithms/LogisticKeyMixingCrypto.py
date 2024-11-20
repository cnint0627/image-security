from .BaseCrypto import *


class LogisticKeyMixingCrypto(BaseCrypto):
    def __init__(self, key=None):
        super().__init__(key)
        self.key_list = self.__extend_key([ord(x) for x in key])

    def __extend_key(self, key_list):
        result = key_list.copy()
        if len(result) < 13:
            base = sum(result)
            while len(result) < 13:
                next_val = (base + len(result) * result[0]) % 256
                result.append(next_val)
                base = (base + next_val) % 256
        elif len(result) > 13:
            extra = result[13:]
            for i, val in enumerate(extra):
                result[i % 12] = (result[i % 12] + val) % 256
            result = result[:13]
        return result

    def __get_image_matrix(self, img):
        im = Image.fromarray(img)
        pix = im.load()
        color = isinstance(pix[0, 0], tuple)
        w, h = im.size
        return [[pix[x, y] for y in range(h)] for x in range(w)], w, h, color

    def __init_params(self, key_list):
        G = [key_list[i:i + 4] for i in range(0, 12, 4)]
        g = []
        R = 1
        for i in range(3):
            s = sum(G[i][j] * (10 ** -(j + 1)) for j in range(4))
            g.append(s)
            R = (R * s) % 1

        V1 = sum(key_list)
        V2 = key_list[0]
        for k in key_list[1:13]:
            V2 ^= k
        V = V2 / V1

        L = (R + key_list[12] / 256) % 1
        L_y = (V + key_list[12] / 256) % 1

        S_x = round(((sum(g) + L) * 10 ** 4) % 256)
        S_y = round((V + V2 + L_y * 10 ** 4) % 256)

        return S_x, S_y, L, L_y

    def __update_values(self, x, y, C, key_list):
        x = (x + C / 256 + key_list[8] / 256 + key_list[9] / 256) % 1
        y = (x + C / 256 + key_list[8] / 256 + key_list[9] / 256) % 1
        for i in range(12):
            key_list[i] = (key_list[i] + key_list[12]) % 256
            key_list[12] ^= key_list[i]
        return x, y, key_list

    def encrypt(self, img: np.ndarray) -> np.ndarray:
        time_start = time.time()

        N = 256
        key_list = self.key_list.copy()
        S_x, S_y, L, L_y = self.__init_params(key_list)

        x = 4 * S_x * (1 - S_x)
        y = 4 * S_y * (1 - S_y)
        C = round((L * L_y * 10 ** 4) % 256)
        C_rgb = [C] * 3

        matrix, w, h, color = self.__get_image_matrix(img)
        encrypted = []

        for i in tqdm(range(w)):
            row = []
            for j in range(h):
                while 0.2 < x < 0.8: x = 4 * x * (1 - x)
                while 0.2 < y < 0.8: y = 4 * y * (1 - y)

                x_r = round((x * 10 ** 4) % 256)
                y_r = round((y * 10 ** 4) % 256)

                C1 = x_r ^ ((key_list[0] + x_r) % N) ^ ((S_x + key_list[1]) % N)
                C2 = x_r ^ ((key_list[2] + y_r) % N) ^ ((S_y + key_list[3]) % N)

                if color:
                    pixel = []
                    for k in range(3):
                        C_rgb[k] = ((key_list[4] + C1) % N) ^ ((key_list[5] + C2) % N) ^ \
                                   ((key_list[6] + matrix[i][j][k]) % N) ^ ((C_rgb[k] + key_list[7]) % N)
                        pixel.append(C_rgb[k])
                    row.append(tuple(pixel))
                    C = C_rgb[0]
                else:
                    C = ((key_list[4] + C1) % N) ^ ((key_list[5] + C2) % N) ^ \
                        ((key_list[6] + matrix[i][j]) % N) ^ ((C + key_list[7]) % N)
                    row.append(C)

                x, y, key_list = self.__update_values(x, y, C, key_list)
            encrypted.append(row)

        mode = "RGB" if color else "L"
        im = Image.new(mode, (w, h))
        for x in range(w):
            for y in range(h):
                im.putpixel((x, y), encrypted[x][y])

        time_end = time.time()
        print(f"Encryption time: {time_end - time_start:.2f}s")

        return np.array(im)

    def decrypt(self, img: np.ndarray, key) -> np.ndarray:
        time_start = time.time()

        N = 256
        key_list = self.__extend_key([ord(x) for x in key])
        S_x, S_y, L_x, L_y = self.__init_params(key_list)

        x = 4 * S_x * (1 - S_x)
        y = 4 * L_x * (1 - S_y)
        C = round((L_x * L_y * 10 ** 4) % 256)
        I_prev = [C] * 4  # [I, I_r, I_g, I_b]

        matrix, w, h, color = self.__get_image_matrix(img)
        decrypted = []

        for i in tqdm(range(w)):
            row = []
            for j in range(h):
                max_iters = 100
                count = 0
                while 0.2 < x < 0.8:
                    x = 4 * x * (1 - x)
                    count += 1
                    if count > max_iters:
                        break

                count = 0
                while 0.2 < y < 0.8:
                    y = 4 * y * (1 - y)
                    count += 1
                    if count > max_iters:
                        break

                x_r = round((x * 10 ** 4) % 256)
                y_r = round((y * 10 ** 4) % 256)

                C1 = x_r ^ ((key_list[0] + x_r) % N) ^ ((S_x + key_list[1]) % N)
                C2 = x_r ^ ((key_list[2] + y_r) % N) ^ ((S_y + key_list[3]) % N)

                if color:
                    pixel = []
                    for k in range(3):
                        I = ((((key_list[4] + C1) % N) ^ ((key_list[5] + C2) % N) ^ \
                              ((I_prev[k + 1] + key_list[7]) % N) ^ matrix[i][j][k]) + N - key_list[6]) % N
                        I_prev[k + 1] = matrix[i][j][k]
                        pixel.append(I)
                    row.append(tuple(pixel))
                    x, y, key_list = self.__update_values(x, y, matrix[i][j][0], key_list)
                else:
                    I = ((((key_list[4] + C1) % N) ^ ((key_list[5] + C2) % N) ^ \
                          ((I_prev[0] + key_list[7]) % N) ^ matrix[i][j]) + N - key_list[6]) % N
                    I_prev[0] = matrix[i][j]
                    row.append(I)
                    x, y, key_list = self.__update_values(x, y, matrix[i][j], key_list)
            decrypted.append(row)

        mode = "RGB" if color else "L"
        im = Image.new(mode, (w, h))
        for x in range(w):
            for y in range(h):
                im.putpixel((x, y), decrypted[x][y])

        time_end = time.time()
        print(f"Decryption time: {time_end - time_start:.2f}s")

        return np.array(im)

if __name__ == "__main__":
    key = "test"
    logistic = LogisticKeyMixingCrypto(key)
    img = cv2.imread("../assets/hust.jpg")
    img_encrypted = logistic.encrypt(img)
    img_decrypted = logistic.decrypt(img_encrypted, key)
    cv2.imshow("decrypted", img_decrypted)
    cv2.waitKey(0)