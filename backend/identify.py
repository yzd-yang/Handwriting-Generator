import cv2
import numpy as np
from sklearn.cluster import DBSCAN


def get_avg_distance(distances):
    """计算距离列表的聚类平均值（使用DBSCAN过滤异常值）"""
    if distances is None or len(distances) == 0:
        return 0
    # 将列表转化为 N x 1 的矩阵，因为DBSCAN需要这种格式的输入
    distances_np = np.array(distances).reshape(-1, 1)

    # 使用DBSCAN算法
    clustering = DBSCAN(eps=5, min_samples=3).fit(distances_np)

    # 找出最常见的标签（除了-1，-1代表噪声）
    labels, counts = np.unique(clustering.labels_, return_counts=True)
    counts[labels == -1] = 0
    most_common_label = labels[np.argmax(counts)]
    # 选择最常见的聚类中的间距，并计算这些间距的平均值
    selected_distances = distances_np[clustering.labels_ == most_common_label]
    avg_distance = np.mean(selected_distances)
    return avg_distance


def identify_distance(filename):
    """
    识别图片中的横线位置，返回 (左边距, 右边距, 上边距, 下边距, 行间距)。
    如果识别失败，返回全 0 兜底。
    """
    try:
        # 读取图像
        image = cv2.imread(filename)
        if image is None:
            raise ValueError("无法读取图片，文件损坏或格式不支持")

        # 转化为灰度图像
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 二值化
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

        # 使用形态学操作来连接线条的两侧
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=1)
        eroded = cv2.erode(dilated, kernel, iterations=1)

        # 边缘检测
        edges = cv2.Canny(eroded, 50, 150, apertureSize=3)

        # 直线检测
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
        # 检测不到直线时返回 None，必须判空
        if lines is None or len(lines) == 0:
            raise ValueError("图片中未检测到横线，无法识别边距/行距")

        lines = sorted(lines, key=lambda x: x[0][1])

        # 选择线，计算旋转角度并存储
        angles = []
        for line in lines:
            for x1, y1, x2, y2 in line:
                angle = np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi
                angles.append(angle)

        # 计算平均角度
        avg_angle = np.mean(angles)

        # 得到旋转矩阵
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, avg_angle, 1.0)

        # 执行旋转
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        # 转换为灰度图像
        gray_rotated = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)

        # 二值化
        _, binary_rotated = cv2.threshold(gray_rotated, 150, 255, cv2.THRESH_BINARY_INV)

        # 边缘检测
        edges_rotated = cv2.Canny(binary_rotated, 50, 150, apertureSize=3)

        # 直线检测（旋转后）
        lines_rotated = cv2.HoughLinesP(edges_rotated, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
        # 检测不到直线时，返回全 0 兜底
        if lines_rotated is None or len(lines_rotated) == 0:
            return 0, 0, 0, 0, 0

        # 对直线的y坐标进行排序
        lines_rotated = sorted(lines_rotated, key=lambda x: x[0][1])

        # 初始化空列表来存储每行的空白长度
        l_whitespaces = []
        r_whitespaces = []

        for line in lines_rotated:
            for x1, y1, x2, y2 in line:
                # 提取每行像素
                row = binary_rotated[y1]
                # 计算空白长度
                if x1 != 0 and x2 != len(row):
                    whitespace_left = x1
                    whitespace_right = len(row) - x2
                    l_whitespaces.append(whitespace_left)
                    r_whitespaces.append(whitespace_right)

        # 安全调用 get_avg_distance：列表为空时返回 0
        avg_l_whitespace = get_avg_distance(l_whitespaces) if l_whitespaces else 0
        avg_r_whitespace = get_avg_distance(r_whitespaces) if r_whitespaces else 0

        # 初始化空列表来存储每列的空白长度
        t_whitespaces = []
        b_whitespaces = []

        # 转置图像，使得列变成行
        binary_rotated_T = binary_rotated.T

        for column in binary_rotated_T:
            # 找到上方第一个非空白像素
            top = np.where(column == 255)[0][0] if np.where(column == 255)[0].size != 0 else 0
            # 找到下方第一个非空白像素
            bottom = np.where(column == 255)[0][-1] if np.where(column == 255)[0].size != 0 else len(column)
            # 计算空白长度
            if top != 0 and bottom != len(column):
                t_whitespaces.append(top)
                b_whitespaces.append(len(column) - bottom)

        avg_t_whitespace = get_avg_distance(t_whitespaces) if t_whitespaces else 0
        avg_b_whitespace = get_avg_distance(b_whitespaces) if b_whitespaces else 0

        # 计算行间距
        distances = []
        for i in range(1, len(lines_rotated)):
            distance = lines_rotated[i][0][1] - lines_rotated[i - 1][0][1]
            if distance > 5:
                distances.append(distance)

        avg_distance = get_avg_distance(distances) if distances else 0

        avg_l_whitespace = round(avg_l_whitespace)
        avg_r_whitespace = round(avg_r_whitespace)
        avg_t_whitespace = round(avg_t_whitespace)
        avg_b_whitespace = round(avg_b_whitespace)
        avg_distance = round(avg_distance)

        return avg_l_whitespace, avg_r_whitespace, avg_t_whitespace, avg_b_whitespace, avg_distance

    except Exception as e:
        print(f"identify_distance failed: {e}")
        # 返回全 0 兜底，让前端提示"无法识别"
        return 0, 0, 0, 0, 0


if __name__ == "__main__":
    identify_distance("notebook.jpg")
