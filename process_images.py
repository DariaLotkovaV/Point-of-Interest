import os
import json
import requests

# URL для обработки изображений
URL = 'http://127.0.0.1:8000/api/process-image/'

# Путь к папке с изображениями
IMAGES_DIR = 'input'

# Путь для сохранения результатов
OUTPUT_FILE = 'output/results.json'

# Функция для обработки изображения


def process_image(image_path):
    with open(image_path, 'rb') as img:
        files = {'image': img}
        response = requests.post(URL, files=files, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error processing {image_path}: {response.status_code}")
            return None


def main(input_files, output_file):
    results = {}

    if not os.path.exists('output'):
        os.makedirs('output')

    # Обрабатываем каждое изображение и сохраняем результат
    for image_file in input_files[:17]:  # Обработка только первых 17 изображений из переданного списка
        image_path = os.path.join(IMAGES_DIR, image_file)
        print(f"Processing {image_path}...")
        result = process_image(image_path)
        if result:
            results[image_file] = result

    # Сохраняем результаты в JSON файл
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, separators=(',', ':'))


# Пример вызова функции main() с передачей аргументов
if __name__ == "__main__":
    input_files = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]
    output_file = 'output/results.json'
    main(input_files, output_file)
