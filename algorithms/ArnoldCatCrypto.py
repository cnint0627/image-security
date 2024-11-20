from .BaseCrypto import *

class ArnoldCatCrypto(BaseCrypto):
    def __init__(self, key=None):
        super().__init__(key)
        self.__a, self.__b, self.__num_iter = key

    def __transform(self, img, a, b, num_iter, reverse=False):
        # 确保图像是方形的
        h, w = img.shape[:2]
        if h != w:
            size = max(h, w)
            padded_img = np.zeros((size, size, 3) if len(img.shape) > 2 else (size, size),
                                  dtype=img.dtype)
            padded_img[:h, :w] = img
            img = padded_img
            h = w = size

        # 创建结果数组
        result = np.zeros_like(img)
        N = h  # 图像尺寸

        # 创建坐标矩阵
        x, y = np.meshgrid(range(N), range(N))

        for _ in tqdm(range(num_iter)):
            if not reverse:
                # 正向变换
                new_x = (x + b * y) % N
                new_y = (a * x + (a * b + 1) * y) % N
            else:
                # 逆向变换
                new_x = ((a * b + 1) * x - b * y) % N
                new_y = (-a * x + y) % N

            # 更新图像
            if len(img.shape) == 3:
                for i in range(3):
                    result[:, :, i] = img[new_y, new_x, i]
            else:
                result[:, :] = img[new_y, new_x]

            img = result.copy()

        return result

    def encrypt(self, img):
        time_start = time.time()
        encrypted_image = self.__transform(img, self.__a, self.__b, self.__num_iter)
        time_end = time.time()
        print(f"Encryption time: {time_end - time_start:.2f}s")
        return encrypted_image

    def decrypt(self, img, key):
        time_start = time.time()
        a, b, num_iter = key
        decrypted_image = self.__transform(img, a, b, num_iter, reverse=True)
        time_end = time.time()
        print(f"Encryption time: {time_end - time_start:.2f}s")
        return decrypted_image

if __name__ == "__main__":
    # 读取图像
    image, ext = "../assets/hust", ".jpg"
    img = cv2.imread(image + ext)

    # 创建 ArnoldCat 实例
    key = (50, 50, 20)
    arnold = ArnoldCatCrypto(key)

    # 加密图像
    print("Encrypting image...")
    encrypted_image = arnold.encrypt(img)
    cv2.imshow("Encrypted Image", encrypted_image)
    cv2.waitKey(0)

    # 解密图像
    # 该过程相比 RSA 算法快了非常多
    print("Decrypting image...")
    decrypted_image = arnold.decrypt(encrypted_image, key=(50, 50, 20))

    # # 创建保存目录
    # results_dir = os.path.join("../", "results", "RSA")
    # os.makedirs(results_dir, exist_ok=True)

    cv2.imshow("Decrypted Image", decrypted_image)
    cv2.waitKey(0)