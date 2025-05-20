import logging
import os
import tempfile
import asyncio
import io
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from app.services import MushroomClassifier
from app.config import settings, logger


class TelegramBot:
    def __init__(self, token: str, classifier: MushroomClassifier):
        self.token = token
        self.classifier = classifier
        self.logger = logging.getLogger("app.telegram_bot")
        self.app = Application.builder().token(self.token).build()

        # Загружаем изображения грибов
        self.mushroom_images = self._load_mushroom_images()

        # Регистрируем обработчики
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.app.add_handler(CallbackQueryHandler(self.handle_button))

    def _load_mushroom_images(self):
        """Загружает все изображения грибов из папки в память"""
        folder_path = "mushroom_photo"
        mushroom_images = {}

        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.jpg'):
                file_path = os.path.join(folder_path, filename)
                mushroom_images[filename[:-4]] = file_path

        self.logger.info(f"Загружено {len(mushroom_images)} изображений грибов")
        return mushroom_images

    def _find_similar_mushrooms(self, query: str):
        """Находит грибы, названия которых содержат запрос"""
        query = query.lower().strip()
        matches = []

        for name in self.mushroom_images.keys():
            if query in name.lower():
                matches.append(name)

        return sorted(matches)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start с клавиатурой выбора действия"""
        keyboard = [
            [InlineKeyboardButton("Определить гриб по фото", callback_data='identify')],
            [InlineKeyboardButton("Найти гриб по названию", callback_data='search')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = (
            "Привет! Я бот для определения грибов.\n\n"
            "Выберите действие:"
        )
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        try:
            await update.message.reply_text("Обрабатываю изображение...")
            photo_file = await update.message.photo[-1].get_file()
            photo_bytes = await photo_file.download_as_bytearray()
            image = Image.open(io.BytesIO(photo_bytes))

            if image.mode != "RGB":
                image = image.convert("RGB")

            with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
                image.save(temp_file, format="JPEG")
                predictions = self.classifier.predict(temp_file.name)
                response = "Топ 5 предсказаний:\n"

                for i, pred in enumerate(predictions, 1):
                    class_name = pred['class_name']
                    description = settings.mushroom_descriptions.get(
                        class_name,
                        f"{class_name}. Информация о съедобности отсутствует"
                    )
                    response += f"{i}. {description} - {pred['confidence']:.2f}%\n"

                response += f"\nP.S. Бот может ошибаться!!! Просьба думать своей головой."
                await update.message.reply_text(response)

                # Предлагаем посмотреть фото для первого результата
                first_pred = predictions[0]['class_name']
                if first_pred in self.mushroom_images:
                    await self._send_mushroom_photo(update, context, first_pred)

        except Exception as e:
            self.logger.error(f"Ошибка обработки фото: {str(e)}", exc_info=True)
            await update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений (поиск гриба по названию)"""
        query = update.message.text.strip()

        # Ищем похожие грибы
        matches = self._find_similar_mushrooms(query)

        if not matches:
            await update.message.reply_text("Грибы с таким названием не найдены. Попробуйте уточнить запрос.")
            return

        if len(matches) == 1:
            # Если нашелся ровно один вариант - показываем его фото
            await self._send_mushroom_photo(update, context, matches[0])
        else:
            # Если несколько вариантов - предлагаем выбрать
            buttons = []
            for name in matches[:10]:  # Ограничиваем 10 вариантами
                buttons.append([InlineKeyboardButton(name, callback_data=f"photo_{name}")])

            reply_markup = InlineKeyboardMarkup(buttons)
            await update.message.reply_text(
                "Найдено несколько вариантов. Выберите нужный гриб:",
                reply_markup=reply_markup
            )

    async def handle_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()

        if query.data == 'identify':
            await query.edit_message_text("Отправьте мне фото гриба для определения его вида.")
        elif query.data == 'search':
            await query.edit_message_text("Введите название гриба (или часть названия) для поиска.")
        elif query.data.startswith("photo_"):
            mushroom_name = query.data[6:]
            await self._send_mushroom_photo_query(query, context, mushroom_name)

    async def _send_mushroom_photo(self, update, context, mushroom_name):
        """Отправляет фото гриба по названию"""
        try:
            if mushroom_name not in self.mushroom_images:
                await update.message.reply_text(f"Фото гриба '{mushroom_name}' не найдено.")
                return

            photo_path = self.mushroom_images[mushroom_name]
            description = settings.mushroom_descriptions.get(
                mushroom_name,
                f"{mushroom_name}. Информация о съедобности отсутствует"
            )

            with open(photo_path, 'rb') as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=description
                )

        except Exception as e:
            self.logger.error(f"Ошибка отправки фото: {str(e)}")
            await update.message.reply_text("Произошла ошибка при отправке фото.")

    async def _send_mushroom_photo_query(self, query, context, mushroom_name):
        """Отправляет фото гриба по названию (для обработчика кнопок)"""
        try:
            if mushroom_name not in self.mushroom_images:
                await query.edit_message_text(f"Фото гриба '{mushroom_name}' не найдено.")
                return

            photo_path = self.mushroom_images[mushroom_name]
            description = settings.mushroom_descriptions.get(
                mushroom_name,
                f"{mushroom_name}. Информация о съедобности отсутствует"
            )

            with open(photo_path, 'rb') as photo_file:
                await query.message.reply_photo(
                    photo=photo_file,
                    caption=description
                )

        except Exception as e:
            self.logger.error(f"Ошибка отправки фото: {str(e)}")
            await query.edit_message_text("Произошла ошибка при отправке фото.")

    async def run(self):
        """Запуск бота в режиме polling"""
        self.logger.info("Бот запущен и ожидает сообщений...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        # Бесконечный цикл
        while True:
            await asyncio.sleep(3600)
