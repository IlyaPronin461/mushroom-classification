import logging
import os
import tempfile
import asyncio
import io
from PIL import Image
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    InlineQueryHandler,
    ChosenInlineResultHandler,
)
from telegram.constants import ParseMode
from app.services import MushroomClassifier
from app.config import settings, logger

from telegram import ReplyKeyboardMarkup, KeyboardButton


class TelegramBot:
    class FakeMessage:
        def __init__(self, text, user):
            self.text = text
            self.from_user = user
            self.chat = user  # Обычно chat также связан с пользователем
            self.message_id = 1  # Минимально необходимый идентификатор сообщения

        # Изменяем reply_text для возврата объекта с message_id
        async def reply_text(self, text, parse_mode=None, reply_markup=None):
            # В реальном боте этот метод отправляет текст. Здесь мы просто создаем объект для тестирования.
            print(f"Replying with text: {text}")

            # Возвращаем объект с атрибутом message_id
            return TelegramBot.FakeReply(message_id=self.message_id)

    class FakeReply:
        def __init__(self, message_id):
            self.message_id = message_id  # Имитация атрибута message_id, который нужен в handle_text

    def __init__(self, token: str, classifier: MushroomClassifier):
        self.token = token
        self.classifier = classifier
        self.logger = logging.getLogger("app.telegram_bot")
        self.app = Application.builder().token(self.token).build()
        self.user_states = {}  # Для хранения состояний пользователей

        # Загружаем изображения грибов
        self.mushroom_images = self._load_mushroom_images()

        # Регистрируем обработчики
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.send_help_message))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.app.add_handler(CallbackQueryHandler(self.handle_button))
        self.app.add_handler(InlineQueryHandler(self.handle_inline_query))
        self.app.add_handler(ChosenInlineResultHandler(self.handle_chosen_inline_result))

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

    def _find_similar_mushrooms(self, query: str, limit: int = 5):
        """Находит грибы, названия которых содержат запрос (с ограничением количества)"""
        self.logger.debug(f"Поиск грибов по запросу: '{query}'")
        query = query.lower().strip()
        matches = []

        for name in self.mushroom_images.keys():
            if query in name.lower():
                matches.append(name)
                if len(matches) >= limit:
                    break

        self.logger.debug(f"Найдено совпадений: {len(matches)}")
        return sorted(matches)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start с обычной клавиатурой"""
        keyboard = [
            [KeyboardButton("/start"), KeyboardButton("/help")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        welcome_text = (
            "🍄 <b>Грибной Эксперт</b> 🍄\n\n"
            "Я помогу вам определить грибы по фото или найти информацию по названию.\n\n"
            "Выберите действие или используйте команды ниже:"
        )
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

        # inline кнопки для действия (определение гриба по фото и поиск по названию)
        inline_keyboard = [
            [InlineKeyboardButton("🔍 Определить гриб по фото", callback_data='identify')],
            [InlineKeyboardButton("📖 Найти гриб по названию", callback_data='search')]
        ]
        reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

        # Отправляем сообщение с кнопками для действия
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=reply_markup_inline,
            parse_mode=ParseMode.HTML
        )

    # В обработчике inline-запроса
    async def handle_inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик inline-запросов для подсказок в реальном времени"""
        query = update.inline_query.query
        if not query:
            return

        matches = self._find_similar_mushrooms(query, limit=10)
        results = []

        self.logger.debug(f"Обрабатываем inline запрос с текстом: '{query}'")

        for idx, name in enumerate(matches):
            results.append(
                InlineQueryResultArticle(
                    id=str(idx),
                    title=name.capitalize(),
                    input_message_content=InputTextMessageContent(
                        message_text=f"🍄 {name.capitalize()}",
                        parse_mode=ParseMode.HTML
                    ),
                    description=f"Нажмите, чтобы узнать больше о {name}"
                )
            )

        self.logger.debug(f"Найдено {len(results)} результатов по запросу '{query}'")

        try:
            await update.inline_query.answer(results, cache_time=1)
        except Exception as e:
            self.logger.error(f"Ошибка при обработке inline-запроса: {str(e)}")

        # Теперь вызовем handle_text, как будто пользователь ввел название гриба вручную
        if results:
            chosen_name = results[0].input_message_content.message_text.strip("🍄 ").lower()
            self.logger.debug(f"Выбранный гриб: {chosen_name}")

            user_id = update.inline_query.from_user.id

            # Создаем фиктивный объект update для вызова handle_text
            fake_message = self.FakeMessage(chosen_name, update.inline_query.from_user)
            fake_update = type('FakeUpdate', (object,),
                               {'message': fake_message, 'from_user': update.inline_query.from_user})

            # Логируем вызов handle_text
            self.logger.debug(f"Передаем выбранный гриб в handle_text: {chosen_name}")
            # Передаем fake_update и context в handle_text
            await self.handle_text(fake_update, context)

    async def handle_chosen_inline_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора гриба из inline-результатов"""
        try:
            result = update.chosen_inline_result
            query = result.query.strip().lower()

            # Получаем выбранный гриб (result_id соответствует индексу в matches)
            result_id = int(result.result_id)
            matches = self._find_similar_mushrooms(query, limit=10)

            if not matches or result_id >= len(matches):
                self.logger.error(f"Не найден гриб по ID: {result_id} (запрос: {query})")
                return

            mushroom_name = matches[result_id]
            self.logger.info(f"Пользователь выбрал гриб: {mushroom_name}")

            # Отправляем фото гриба
            if mushroom_name in self.mushroom_images:
                photo_path = self.mushroom_images[mushroom_name]

                caption = (
                    f"🍄 <b>{mushroom_name.capitalize()}</b>\n\n"
                )

                try:
                    with open(photo_path, 'rb') as photo_file:
                        await context.bot.send_photo(
                            chat_id=result.from_user.id,
                            photo=photo_file,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    self.logger.info(f"Фото гриба {mushroom_name} отправлено пользователю")
                except Exception as e:
                    self.logger.error(f"Ошибка при отправке фото: {str(e)}")
                    await context.bot.send_message(
                        chat_id=result.from_user.id,
                        parse_mode=ParseMode.HTML
                    )
            else:
                self.logger.error(f"Фото для гриба {mushroom_name} не найдено")
                await context.bot.send_message(
                    chat_id=result.from_user.id,
                    text=f"❌ Фото гриба '{mushroom_name}' не найдено в базе."
                )

        except Exception as e:
            self.logger.error(f"Ошибка в handle_chosen_inline_result: {str(e)}", exc_info=True)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        try:
            message = await update.message.reply_text("🔬 Анализирую изображение...")

            photo_file = await update.message.photo[-1].get_file()
            photo_bytes = await photo_file.download_as_bytearray()
            image = Image.open(io.BytesIO(photo_bytes))

            if image.mode != "RGB":
                image = image.convert("RGB")

            with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
                image.save(temp_file, format="JPEG")
                predictions = self.classifier.predict(temp_file.name)

                response = "🍄 <b>Результаты анализа:</b>\n\n"

                for i, pred in enumerate(predictions[:5], 1):
                    class_name = pred['class_name']
                    description = settings.mushroom_descriptions.get(
                        class_name,
                        f"{class_name}. Информация о съедобности отсутствует"
                    )
                    response += (
                        f"{i}. <b>{class_name.capitalize()}</b>\n"
                        f"<i>{description}</i>\n"
                        f"Точность: {pred['confidence']:.1f}%\n\n"
                    )

                response += (
                    "\n⚠️ <b>Внимание!</b> Бот не является профессиональным микологом. "
                    "Всегда перепроверяйте информацию перед употреблением грибов в пищу."
                )

                await message.edit_text(response, parse_mode=ParseMode.HTML)

                # Предлагаем посмотреть фото для первого результата
                first_pred = predictions[0]['class_name']
                if first_pred in self.mushroom_images:
                    await self._send_mushroom_photo(update, context, first_pred)

            # Добавляем кнопку "Назад"
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Что дальше?",
                reply_markup=reply_markup
            )

        except Exception as e:
            self.logger.error(f"Ошибка обработки фото: {str(e)}", exc_info=True)
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке фото. Попробуйте отправить другое изображение."
            )

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений (поиск гриба по названию)"""
        try:
            user_id = update.message.from_user.id
            query = update.message.text.strip()

            # Логируем полученный запрос
            self.logger.debug(f"Получен текстовый запрос: '{query}' от пользователя {user_id}")

            # Если это команды /start или /help, обрабатываем их отдельно
            if query == "/start":
                await self.start_command(update, context)
                return  # Прерываем выполнение функции, так как команда /start обработана
            elif query == "/help":
                await self.send_help_message(update, context)
                return  # Прерываем выполнение функции, так как команда /help обработана

            # Если запрос содержит название гриба
            if query.startswith("🍄 "):
                query = query[2:].strip()  # Убираем символ "🍄" если он есть

            # Если пользователь в режиме поиска (нажал "Найти гриб по названию")
            if self.user_states.get(user_id) == 'searching':
                matches = self._find_similar_mushrooms(query, limit=5)

                self.logger.debug(f"Найдено {len(matches)} грибов по запросу '{query}'")

                if not matches:
                    await update.message.reply_text(
                        "❌ Пока не найдено грибов с таким названием. Продолжайте вводить..."
                    )
                    return

                # Формируем кнопки для подсказок
                buttons = []
                for name in matches:
                    display_name = name.capitalize()
                    buttons.append([InlineKeyboardButton(display_name, callback_data=f"select_{name}")])

                # Добавляем кнопку "Назад"
                buttons.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')])

                reply_markup = InlineKeyboardMarkup(buttons)

                # Отправляем сообщение с кнопками
                response = (
                    f"🔍 <b>Возможные варианты:</b>\n\n"
                    "Выберите нужный гриб из списка ниже:"
                )

                if 'last_suggestion_msg_id' in context.user_data:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=update.message.chat_id,
                            message_id=context.user_data['last_suggestion_msg_id'],
                            text=response,
                            reply_markup=reply_markup,
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        self.logger.error(f"Ошибка обновления подсказки: {str(e)}")
                        msg = await update.message.reply_text(
                            response,
                            reply_markup=reply_markup,
                            parse_mode=ParseMode.HTML
                        )
                        context.user_data['last_suggestion_msg_id'] = msg.message_id
                else:
                    msg = await update.message.reply_text(
                        response,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML
                    )
                    context.user_data['last_suggestion_msg_id'] = msg.message_id

                # Если введено полное совпадение - показываем результат
                if query.lower() in [m.lower() for m in matches]:
                    await self._send_mushroom_details(update, context, query)
                    context.user_data.pop('last_suggestion_msg_id', None)
                    self.user_states.pop(user_id, None)

            else:
                # Обычный обработчик текста
                matches = self._find_similar_mushrooms(query)

                self.logger.debug(f"Найдено {len(matches)} грибов по запросу '{query}' в обычном режиме.")

                if not matches:
                    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await update.message.reply_text(
                        "❌ Грибы с таким названием не найдены. Попробуйте уточнить запрос.\n\n"
                        "Например: 'белый', 'лисичка', 'опенок'",
                        reply_markup=reply_markup
                    )
                    return

                if len(matches) == 1:
                    await self._send_mushroom_details(update, context, matches[0])
                else:
                    buttons = []
                    for name in matches[:10]:
                        display_name = name.capitalize()
                        buttons.append([InlineKeyboardButton(display_name, callback_data=f"select_{name}")])

                    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")])

                    reply_markup = InlineKeyboardMarkup(buttons)

                    response = (
                        f"🔎 <b>Найдено {len(matches)} вариантов по запросу '{query}':</b>\n\n"
                        "Выберите нужный гриб из списка:"
                    )

                    await update.message.reply_text(
                        response,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML
                    )

        except Exception as e:
            self.logger.error(f"Ошибка обработки текста: {str(e)}", exc_info=True)
            await update.message.reply_text("❌ Произошла ошибка при обработке запроса.")

    async def send_help_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправка сообщения с инструкциями по использованию бота"""
        help_text = (
            "🍄 <b>Грибной Эксперт - Помощь</b> 🍄\n\n"
            "Этот бот поможет вам определить грибы по фотографии или найти информацию о грибах по названию.\n\n"
            "<b>Как пользоваться:</b>\n\n"
            "1. Для начала работы с ботом нажмите кнопку <b>'/start'</b> или выберите команду из меню.\n"
            "2. Вы можете отправить фотографию гриба, выбрав команду <b>'🔍 Определить гриб по фото'</b>, и бот постарается определить его.\n"
            "3. Если хотите найти гриб по названию, выберите команду <b>'📖 Найти гриб по названию'</b>.\n"
            "4. Напишите название гриба, и бот предложит возможные совпадения.\n\n"
            "<b>Команды:</b>\n"
            "/start - Начать работу с ботом\n"
            "/help - Получить помощь\n"
            "📸 Отправьте фото гриба, чтобы получить информацию о нем.\n"
            "🔎 Напишите название гриба, чтобы найти его в базе данных."
        )

        # Добавляем кнопки для навигации
        keyboard = [[KeyboardButton("/start"), KeyboardButton("/help")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        # Отправляем сообщение с инструкциями
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    async def handle_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id

        if query.data == 'identify':
            await query.edit_message_text(
                "📸 <b>Определение гриба по фото</b>\n\n"
                "Отправьте мне четкое фото гриба (лучше всего сфотографировать шляпку и ножку).\n\n"
                "Для возврата в меню используйте /start",
                parse_mode=ParseMode.HTML
            )
            self.user_states[user_id] = 'identifying'

        elif query.data == 'search':
            bot_username = context.bot.username
            keyboard = [
                [InlineKeyboardButton("🔍 Начать поиск", switch_inline_query_current_chat="")],
                [InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"🔎 <b>Поиск гриба по названию</b>\n\n"
                f"Нажмите кнопку <b>'Начать поиск'</b> ниже, и поле ввода сообщения автоматически подготовится к поиску. Либо же можете написать названия гриба обычным сообщением, а я попробую предложить вам возможные варианты!\n\n"
                f"Или введите вручную:\n"
                f"<code>@{bot_username} название_гриба</code>\n\n"
                f"Например: <code>@{bot_username} мухом</code>\n\n"
                f"Я буду показывать подсказки по мере ввода!",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            self.user_states[user_id] = 'searching'

        elif query.data.startswith("select_"):
            mushroom_name = query.data[7:]
            await self._send_mushroom_details_query(query, context, mushroom_name)
            self.user_states.pop(user_id, None)

        elif query.data == 'back_to_start':
            await self.start_command(query, context)
            self.user_states.pop(user_id, None)

    async def _send_mushroom_details(self, update, context, mushroom_name):
        """Отправляет детальную информацию о грибе"""
        try:
            if mushroom_name not in self.mushroom_images:
                await update.message.reply_text(f"❌ Информация о грибе '{mushroom_name}' не найдена.")
                return

            # Получаем путь к изображению гриба
            photo_path = self.mushroom_images[mushroom_name]

            formatted_desc = (
                f"🍄 <b>{mushroom_name.capitalize()}</b>\n\n"
            )

            # Отправляем фото гриба и описание
            with open(photo_path, 'rb') as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=formatted_desc,
                    parse_mode=ParseMode.HTML
                )

            # Кнопка "Назад"
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Что дальше?",
                reply_markup=reply_markup
            )

        except Exception as e:
            self.logger.error(f"Ошибка отправки деталей гриба: {str(e)}")
            await update.message.reply_text("❌ Произошла ошибка при отправке информации о грибе.")

    async def _send_mushroom_details_query(self, query, context, mushroom_name):
        """Отправляет детальную информацию о грибе (для обработчика кнопок)"""
        try:
            if mushroom_name not in self.mushroom_images:
                await query.edit_message_text(f"❌ Информация о грибе '{mushroom_name}' не найдена.")
                return

            photo_path = self.mushroom_images[mushroom_name]

            formatted_desc = (
                f"🍄 <b>{mushroom_name.capitalize()}</b>\n\n"
            )

            await query.message.reply_photo(
                photo=open(photo_path, 'rb'),
                caption=formatted_desc,
                parse_mode=ParseMode.HTML
            )

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Что дальше?",
                reply_markup=reply_markup
            )

        except Exception as e:
            self.logger.error(f"Ошибка отправки деталей гриба: {str(e)}")
            await query.edit_message_text("❌ Произошла ошибка при отправке информации о грибе.")

    async def _send_mushroom_photo(self, update, context, mushroom_name):
        """Отправляет фото гриба"""
        try:
            if mushroom_name in self.mushroom_images:
                with open(self.mushroom_images[mushroom_name], 'rb') as photo_file:
                    await update.message.reply_photo(
                        photo=photo_file,
                        caption=f"🍄 {mushroom_name.capitalize()}"
                    )
        except Exception as e:
            self.logger.error(f"Ошибка отправки фото гриба: {str(e)}")

    async def run(self):
        """Запуск бота в режиме polling"""
        self.logger.info("Бот запущен и ожидает сообщений...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        while True:
            await asyncio.sleep(3600)
