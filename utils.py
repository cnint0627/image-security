import numpy as np
import cv2
from PIL import Image
from matplotlib import pyplot as plt


def imshow(*imgs, titles=None):
    # 在 jupyter notebook 里并排展示多张图片
    plt.figure(figsize=(4 * len(imgs), 4), facecolor='none')

    if titles is None:
        titles = [f'Image {i + 1}' for i in range(len(imgs))]

    for i, (img, title) in enumerate(zip(imgs, titles), 1):
        plt.subplot(1, len(imgs), i)
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title(title, fontsize=16, pad=10, color='white')
        plt.axis('off')

    plt.tight_layout()
    plt.show()


def draw_intensity_histogram(img_ori, img_enc, is_gray=False):
    """
    绘制图像的 intensity_histogram 指标曲线
    img_ori: 原图
    img_enc: 加密后的图像
    is_gray: 是否为灰度图
    """
    plt.figure(figsize=(12, 5))

    # 左侧子图：原图
    plt.subplot(1, 2, 1)
    if is_gray:
        histogram = cv2.calcHist([img_ori], [0], None, [256], [0, 256])
        plt.plot(histogram, color='black', label='gray')
    else:
        histogram_blue = cv2.calcHist([img_ori], [0], None, [256], [0, 256])
        plt.plot(histogram_blue, color='blue', label='blue')
        histogram_green = cv2.calcHist([img_ori], [1], None, [256], [0, 256])
        plt.plot(histogram_green, color='green', label='green')
        histogram_red = cv2.calcHist([img_ori], [2], None, [256], [0, 256])
        plt.plot(histogram_red, color='red', label='red')

    plt.title('Original Image', fontsize=20)
    plt.xlabel('pixel values', fontsize=16)
    plt.ylabel('pixel count', fontsize=16)
    plt.legend()

    # 右侧子图：加密图
    plt.subplot(1, 2, 2)
    if is_gray:
        histogram = cv2.calcHist([img_enc], [0], None, [256], [0, 256])
        plt.plot(histogram, color='black', label='gray')
    else:
        histogram_blue = cv2.calcHist([img_enc], [0], None, [256], [0, 256])
        plt.plot(histogram_blue, color='blue', label='blue')
        histogram_green = cv2.calcHist([img_enc], [1], None, [256], [0, 256])
        plt.plot(histogram_green, color='green', label='green')
        histogram_red = cv2.calcHist([img_enc], [2], None, [256], [0, 256])
        plt.plot(histogram_red, color='red', label='red')

    plt.title('Encrypted Image', fontsize=20)
    plt.xlabel('pixel values', fontsize=16)
    plt.ylabel('pixel count', fontsize=16)
    plt.legend()

    plt.tight_layout()
    plt.show()

def get_image_matrix_gray(img):
    im = Image.fromarray(img).convert('LA')
    pix = im.load()
    color = 1
    image_size = im.size
    image_matrix = []
    for width in range(int(image_size[0])):
        row = []
        for height in range(int(image_size[1])):
            row.append((pix[width,height]))
        image_matrix.append(row)
    return image_matrix, image_size

def draw_adjacent_pixel_auto_correlation(img_ori, img_enc):
    """
    绘制图像的 adjacent pixel auto-correlation 指标曲线
    img_ori: 原图
    img_enc: 加密后的图像
    """
    plt.figure(figsize=(12, 5))

    image_ori, image_size = get_image_matrix_gray(img_ori)
    image_enc, _ = get_image_matrix_gray(img_enc)

    # 采样点
    samples_x_ori = []
    samples_y_ori = []
    samples_x_enc = []
    samples_y_enc = []

    # 随机采样
    for i in range(1024):
        x = np.random.randint(0, image_size[0] - 2)
        y = np.random.randint(0, image_size[1] - 1)
        # 原图采样点
        samples_x_ori.append(image_ori[x][y])
        samples_y_ori.append(image_ori[x + 1][y])
        # 加密图采样点
        samples_x_enc.append(image_enc[x][y])
        samples_y_enc.append(image_enc[x + 1][y])

    # 左侧子图：原图
    plt.subplot(1, 2, 1)
    plt.scatter(samples_x_ori, samples_y_ori, s=2)
    plt.title('Original Image', fontsize=20)
    plt.xlabel('Pixel Value', fontsize=16)
    plt.ylabel('Adjacent Pixel Value', fontsize=16)

    # 右侧子图：加密图
    plt.subplot(1, 2, 2)
    plt.scatter(samples_x_enc, samples_y_enc, s=2)
    plt.title('Encrypted Image', fontsize=20)
    plt.xlabel('Pixel Value', fontsize=16)
    plt.ylabel('Adjacent Pixel Value', fontsize=16)

    plt.tight_layout()
    plt.show()