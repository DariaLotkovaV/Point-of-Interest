import cv2
import numpy as np
import json


def process_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Image not loaded properly, check the file path and format.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray


def detect_points_of_interest(gray_image, k=0.2, window_size=7, threshold=1500000.0):
    corner_list = []
    offset = int(window_size / 2)
    y_range = gray_image.shape[0] - offset
    x_range = gray_image.shape[1] - offset

    dy, dx = np.gradient(gray_image)
    Ixx = dx**2
    Ixy = dy * dx
    Iyy = dy**2

    for y in range(offset, y_range):
        for x in range(offset, x_range):
            start_y = y - offset
            end_y = y + offset + 1
            start_x = x - offset
            end_x = x + offset + 1

            windowIxx = Ixx[start_y:end_y, start_x:end_x]
            windowIxy = Ixy[start_y:end_y, start_x:end_x]
            windowIyy = Iyy[start_y:end_y, start_x:end_x]

            Sxx = windowIxx.sum()
            Sxy = windowIxy.sum()
            Syy = windowIyy.sum()

            det = (Sxx * Syy) - (Sxy**2)
            trace = Sxx + Syy

            r = det - k * (trace**2)

            if r > threshold:
                corner_list.append([x, y, r])

    # Конвертация результата в формат JSON и сохранение в файл
    with open('output/results.json', 'w') as json_file:
        json.dump(corner_list, json_file)

    return corner_list
