import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import io
import tempfile
from app.services import MushroomClassifier
from app.config import settings, logger
import asyncio


class TelegramBot:
    def __init__(self, token: str, classifier: MushroomClassifier):
        self.token = token
        self.classifier = classifier
        self.logger = logging.getLogger("app.telegram_bot")
        self.app = Application.builder().token(self.token).build()

        # Регистрируем обработчики
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Привет! Отправь мне фото гриба, и я попробую определить его вид.")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        except Exception as e:
            self.logger.error(f"Ошибка обработки фото: {str(e)}", exc_info=True)
            await update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

    async def run(self):
        """Запуск бота в режиме polling"""
        self.logger.info("Бот запущен и ожидает сообщений...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        # Бесконечный цикл
        while True:
            await asyncio.sleep(3600)
