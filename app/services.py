import torch
import torchvision.models as models
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import os
import gdown
import logging
import json
from pathlib import Path
import tempfile
from shutil import rmtree
from .config import settings


class MushroomClassifier:
    def __init__(self):
        self.logger = logging.getLogger("app.services")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"Инициализация классификатора. Устройство: {self.device}")

        self.model = None
        self.load_model()

        # Определим трансформации для подготовки изображения
        self.transform = transforms.Compose([
            transforms.Resize(256),  # Уменьшаем изображение до 256x256
            transforms.CenterCrop(224),  # Обрезаем центральную часть до 224x224
            transforms.ToTensor(),  # Преобразуем изображение в тензор
            transforms.Normalize(  # Нормализация изображения с усредненными значениями для ImageNet
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])

    def download_file_from_gdrive(self, file_id, filename, temp_dir):
        """Загрузка файла с Google Диска по ID"""
        self.logger.debug(f"Начало загрузки файла {filename} с ID {file_id}")
        url = f"https://drive.google.com/uc?id={file_id}"
        output_path = os.path.join(temp_dir, filename)

        try:
            gdown.download(url, output_path, quiet=False)
            self.logger.info(f"Файл {filename} успешно загружен в {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Ошибка загрузки файла {filename}: {str(e)}")
            raise

    def load_model(self):
        """Загрузка модели ResNet и метаданных с Google Диска"""
        self.logger.info("Начало загрузки модели ResNet с Google Диска")
        temp_dir = tempfile.mkdtemp()
        self.logger.debug(f"Создана временная директория: {temp_dir}")

        try:
            # Загружаем файлы модели
            model_file = self.download_file_from_gdrive(settings.gdrive_file_ids['ResNet_model.pth'],
                                                        'ResNet_model.pth', temp_dir)
            metadata_file = self.download_file_from_gdrive(settings.gdrive_file_ids['metadata.json'], 'metadata.json',
                                                           temp_dir)

            # Загружаем метаданные
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Загружаем модель ResNet
            model = models.resnet18(pretrained=False)
            model.fc = nn.Linear(model.fc.in_features, len(metadata['class_names']))
            model.load_state_dict(torch.load(model_file, map_location=torch.device('cpu')))
            model.eval()

            # Сохраняем id2label и label2id для использования в предсказаниях
            model.id2label = metadata['id2label']
            model.label2id = metadata['label2id']
            model.class_names = metadata['class_names']

            self.model = model.to(self.device)
            self.logger.info("Модель ResNet успешно загружена!")

        except Exception as e:
            self.logger.error(f"Ошибка при загрузке модели: {str(e)}")
            raise RuntimeError(f"Ошибка загрузки модели: {e}")
        finally:
            try:
                rmtree(temp_dir, ignore_errors=True)
                self.logger.debug(f"Временная директория {temp_dir} удалена")
            except Exception as e:
                self.logger.warning(f"Не удалось удалить временную директорию: {str(e)}")

    def predict(self, image_path: str):
        self.logger.info(f"Начало обработки изображения: {image_path}")
        try:
            image = Image.open(image_path).convert("RGB")
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                outputs = self.model(image_tensor)

            probs = torch.nn.functional.softmax(outputs, dim=-1)[0]
            top5_probs, top5_indices = torch.topk(probs, 5)

            self.logger.debug(f"Predicted indices: {top5_indices}")  # Добавить вывод индексов
            self.logger.debug(f"Predicted probabilities: {top5_probs}")  # Добавить вывод вероятностей

            results = []
            for prob, idx in zip(top5_probs, top5_indices):
                idx_item = str(idx.item())  # Преобразуем индекс в строку

                # Теперь можно безопасно искать по строковым ключам
                if idx_item in self.model.id2label:
                    class_name = self.model.id2label[idx_item]
                else:
                    class_name = f"Неизвестный класс (индекс: {idx_item})"
                results.append({
                    "class_name": class_name,
                    "confidence": float(prob) * 100
                })

            self.logger.info("Предсказание успешно завершено")
            return results

        except Exception as e:
            self.logger.error(f"Ошибка при выполнении предсказания: {str(e)}")
            raise

