import torch
from transformers import ViTForImageClassification, ViTImageProcessor
from PIL import Image
import os
import tempfile
from shutil import rmtree
import gdown
import logging
from .config import settings


class MushroomClassifier:
    def __init__(self):
        self.logger = logging.getLogger("app.services")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"Инициализация классификатора. Устройство: {self.device}")
        self.model = None
        self.processor = None
        self.load_model()

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
        """Загрузка модели и процессора с Google Диска"""
        self.logger.info("Начало загрузки модели с Google Диска")
        temp_dir = tempfile.mkdtemp()
        self.logger.debug(f"Создана временная директория: {temp_dir}")

        try:
            # Загружаем все необходимые файлы
            for name, file_id in settings.gdrive_file_ids.items():
                self.logger.debug(f"Загрузка файла модели: {name}")
                self.download_file_from_gdrive(file_id, name, temp_dir)

            # Проверяем, что все обязательные файлы загружены
            required_files = ["config.json", "model.safetensors", "preprocessor_config.json"]
            for file in required_files:
                if not os.path.exists(os.path.join(temp_dir, file)):
                    error_msg = f"Файл {file} не загружен!"
                    self.logger.error(error_msg)
                    raise FileNotFoundError(error_msg)

            # Загружаем модель и процессор из временной директории
            self.logger.info("Загрузка модели в память...")
            self.model = ViTForImageClassification.from_pretrained(
                temp_dir,
                local_files_only=True,
                use_safetensors=True
            ).to(self.device)

            self.processor = ViTImageProcessor.from_pretrained(
                temp_dir,
                local_files_only=True
            )
            self.logger.info("Модель успешно загружена!")

        except Exception as e:
            self.logger.error(f"Критическая ошибка при загрузке модели: {str(e)}")
            raise RuntimeError(f"Ошибка загрузки модели: {e}")
        finally:
            try:
                rmtree(temp_dir, ignore_errors=True)
                self.logger.debug(f"Временная директория {temp_dir} удалена")
            except Exception as e:
                self.logger.warning(f"Не удалось удалить временную директорию: {str(e)}")

    def predict(self, image_path: str):
        """Предсказание классов грибов по изображению"""
        self.logger.info(f"Начало обработки изображения: {image_path}")
        try:
            image = Image.open(image_path)
            self.logger.debug("Изображение успешно открыто")

            if image.mode != "RGB":
                self.logger.debug("Конвертация изображения в RGB")
                image = image.convert("RGB")

            self.logger.debug("Подготовка входных данных для модели")
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)

            self.logger.debug("Выполнение предсказания")
            with torch.no_grad():
                outputs = self.model(**inputs)

            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]
            top5_probs, top5_indices = torch.topk(probs, 5)

            results = []
            for prob, idx in zip(top5_probs, top5_indices):
                class_name = self.model.config.id2label[idx.item()]
                results.append({
                    "class_name": class_name,
                    "confidence": float(prob) * 100
                })

            self.logger.info("Предсказание успешно завершено")
            return results

        except FileNotFoundError:
            error_msg = f"Файл {image_path} не найден!"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении предсказания: {str(e)}")
            raise