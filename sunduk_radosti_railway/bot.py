import logging
from datetime import date, time, datetime
from pathlib import Path

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import (
    BASE_DIR,
    COUNTDOWN_START,
    MORNING_HOUR,
    MORNING_MINUTE,
    OWNER_CHAT_ID,
    TARGET_DATE,
    TIMEZONE,
    TOKEN,
)
from storage import load_state, save_state
from texts import (
    MENU_ARCHIVE,
    MENU_ARCHIVE_ADD,
    MENU_CEM,
    MENU_TRAININGS,
    MORNING_WISHES,
    START_TEXT,
)
from trainings import TRAINING_VIDEOS


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(MENU_ARCHIVE_ADD), KeyboardButton(MENU_CEM)],
            [KeyboardButton(MENU_ARCHIVE), KeyboardButton(MENU_TRAININGS)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери, что открыть ✨",
    )


def days_word(number: int) -> str:
    number = abs(number) % 100
    last_digit = number % 10
    if 11 <= number <= 19:
        return "дней"
    if last_digit == 1:
        return "день"
    if 2 <= last_digit <= 4:
        return "дня"
    return "дней"


def is_training_available(video: dict, today: date | None = None) -> bool:
    today = today or datetime.now(TIMEZONE).date()
    return today >= date.fromisoformat(video["available_from"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    chat_id = update.effective_chat.id
    state.setdefault("users", [])
    state.setdefault("chat_ids", [])
    state.setdefault("archive", [])
    state.setdefault("training_messages", {})

    if chat_id not in state["users"]:
        state["users"].append(chat_id)
    if chat_id not in state["chat_ids"]:
        state["chat_ids"].append(chat_id)
    save_state(state)

    await update.message.reply_text(
        START_TEXT,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


async def morning(context: ContextTypes.DEFAULT_TYPE) -> None:
    today = datetime.now(TIMEZONE).date()
    if today < COUNTDOWN_START or today > TARGET_DATE:
        return

    days_left = (TARGET_DATE - today).days
    wish = MORNING_WISHES[(today - COUNTDOWN_START).days % len(MORNING_WISHES)]

    if days_left > 0:
        text = (
            "<b>Доброе утрооо ☀️</b>\n\n"
            "До тёплой Испании осталось...\n"
            f"⏳ <b>{days_left} {days_word(days_left)}</b> ⏳\n\n"
            f"{wish}"
        )
    else:
        text = (
            "<b>Доброе утрооо ☀️</b>\n\n"
            "<b>Сегодня тот самый день!</b> 🇪🇸\n\n"
            "Тёплая Испания уже ждёт 💗"
        )

    state = load_state()
    for chat_id in state.get("chat_ids", []):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                reply_markup=main_menu(),
            )
        except Exception as error:
            print(f"Ошибка утреннего сообщения для {chat_id}: {error}")


async def show_trainings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    today = datetime.now(TIMEZONE).date()
    buttons = []

    for lesson_key, video in TRAINING_VIDEOS.items():
        prefix = "▶️" if is_training_available(video, today) else "🔒"
        buttons.append([
            InlineKeyboardButton(
                f"{prefix} {video['title']}",
                callback_data=f"training:{lesson_key}",
            )
        ])

    await update.effective_message.reply_text(
        "<b>Йога и тренировки</b> 🧘‍♀️\n\n"
        "Нажми на доступный урок, и бот пришлёт видео сюда.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def send_training_to_chat(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    lesson_key: str,
) -> None:
    video = TRAINING_VIDEOS[lesson_key]
    feedback_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💌 Оставить впечатления", callback_data="lesson_feedback")]
    ])

    state = load_state()
    stored_message_id = (
        state.get("training_messages", {})
        .get(str(chat_id), {})
        .get(lesson_key)
    )

    sent_message = None
    if stored_message_id:
        try:
            sent_message = await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=chat_id,
                message_id=stored_message_id,
                reply_markup=feedback_keyboard,
            )
        except Exception as error:
            print(f"Не удалось скопировать старое видео {lesson_key}: {error}")

    if sent_message is None:
        if "file_id" in video:
            sent_message = await context.bot.send_video(
                chat_id=chat_id,
                video=video["file_id"],
                caption=video["caption"],
                parse_mode="HTML",
                reply_markup=feedback_keyboard,
                supports_streaming=True,
            )
        else:
            video_path = BASE_DIR / video["file"]
            if not video_path.exists():
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"Видео «{video['title']}» отмечено как доступное, "
                        f"но файл <code>{video_path}</code> не найден рядом с ботом."
                    ),
                    parse_mode="HTML",
                )
                return
            with video_path.open("rb") as file:
                sent_message = await context.bot.send_video(
                    chat_id=chat_id,
                    video=file,
                    caption=video["caption"],
                    parse_mode="HTML",
                    reply_markup=feedback_keyboard,
                    supports_streaming=True,
                    write_timeout=300,
                    read_timeout=300,
                    connect_timeout=300,
                    pool_timeout=300,
                )

    message_id = getattr(sent_message, "message_id", None)
    if message_id:
        state = load_state()
        state.setdefault("training_messages", {}).setdefault(str(chat_id), {})[lesson_key] = message_id
        save_state(state)


async def archive_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    chat_id = update.effective_chat.id
    state["waiting_for_archive_message"] = chat_id
    state["waiting_for_cem_photo"] = None
    save_state(state)
    await update.effective_message.reply_text(
        "Напиши любое сообщение, и оно отправится в наш архив 💌",
        reply_markup=main_menu(),
    )


async def cem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    chat_id = update.effective_chat.id
    state["waiting_for_cem_photo"] = chat_id
    state["waiting_for_archive_message"] = None
    save_state(state)
    await update.effective_message.reply_text(
        "Отправь милую или любую фотографию себя 😽\nЯ бережно сохраню её в архив.",
        reply_markup=main_menu(),
    )


async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💌 Смотреть сообщения", callback_data="archive_messages")],
        [InlineKeyboardButton("😽 Смотреть цемы", callback_data="archive_cems")],
    ])
    await update.effective_message.reply_text(
        "Что хочешь посмотреть в нашем архиве?",
        reply_markup=keyboard,
    )


async def notify_others_about_archive(context, state, sender_chat_id, archive_index) -> None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🥹 Уии, посмотреть", callback_data=f"view_archive:{archive_index}")]
    ])
    for user_chat_id in state.get("users", []):
        if user_chat_id != sender_chat_id:
            await context.bot.send_message(
                chat_id=user_chat_id,
                text="Вам прилетела милая весточка из архива 💌",
                reply_markup=keyboard,
            )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = load_state()
    chat_id = update.effective_chat.id
    if state.get("waiting_for_cem_photo") != chat_id:
        return

    photo = update.message.photo[-1]
    state.setdefault("archive", []).append({
        "date": datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M"),
        "type": "cem_photo",
        "file_id": photo.file_id,
        "from_chat_id": chat_id,
    })
    archive_index = len(state["archive"]) - 1
    state["waiting_for_cem_photo"] = None
    save_state(state)

    await notify_others_about_archive(context, state, chat_id, archive_index)
    await update.message.reply_text(
        "Готово 😽 Бережно отправлено в архив!",
        reply_markup=main_menu(),
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    chat_id = update.effective_chat.id

    if text == MENU_ARCHIVE_ADD:
        await archive_add(update, context)
        return
    if text == MENU_CEM:
        await cem(update, context)
        return
    if text == MENU_ARCHIVE:
        await archive(update, context)
        return
    if text == MENU_TRAININGS:
        await show_trainings(update, context)
        return

    state = load_state()

    if state.get("waiting_for_lesson_feedback") == chat_id:
        state["waiting_for_lesson_feedback"] = None
        save_state(state)
        await context.bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text=f"Пришли впечатления от тренировки 🌿\n\n{text}",
        )
        await update.message.reply_text("🍓", reply_markup=main_menu())
        return

    if state.get("waiting_for_archive_message") != chat_id:
        return

    state.setdefault("archive", []).append({
        "date": datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M"),
        "type": "text",
        "text": text,
        "from_chat_id": chat_id,
    })
    archive_index = len(state["archive"]) - 1
    state["waiting_for_archive_message"] = None
    save_state(state)

    await notify_others_about_archive(context, state, chat_id, archive_index)
    await update.message.reply_text("Сохранено в архив 💌", reply_markup=main_menu())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    state = load_state()

    if data == "lesson_feedback":
        state["waiting_for_lesson_feedback"] = query.message.chat_id
        save_state(state)
        await query.message.reply_text(
            "Урааа, расскажи свои впечатления! 🥁",
            reply_markup=main_menu(),
        )
        return

    if data.startswith("training:"):
        lesson_key = data.split(":", 1)[1]
        video = TRAINING_VIDEOS.get(lesson_key)
        if not video:
            await query.message.reply_text("Этот урок куда-то укатился 🫣")
            return
        if not is_training_available(video):
            available_date = date.fromisoformat(video["available_from"]).strftime("%d.%m.%Y")
            await query.answer(f"Откроется {available_date} 🔒", show_alert=True)
            return
        await send_training_to_chat(context, query.message.chat_id, lesson_key)
        return

    if data == "archive_messages":
        messages = [item for item in state.get("archive", []) if item.get("type") == "text"]
        if not messages:
            await query.message.reply_text("Сообщений пока нет 💌")
            return
        text = "<b>Наши сообщения 💌</b>\n\n"
        for item in messages[-15:]:
            text += f"💌 {item.get('date', '')}\n{item.get('text', '')}\n\n"
        await query.message.reply_text(text, parse_mode="HTML")
        return

    if data == "archive_cems":
        cems = [item for item in state.get("archive", []) if item.get("type") == "cem_photo"]
        if not cems:
            await query.message.reply_text("Цемов пока нет... подозрительно тихо 😽")
            return
        await query.message.reply_text("<b>Архив цемов 😽</b>", parse_mode="HTML")
        for item in cems[-15:]:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=item["file_id"],
                caption=f"😽 {item.get('date', '')}",
            )
        return

    if data.startswith("view_archive:"):
        archive_index = int(data.split(":", 1)[1])
        archive_items = state.get("archive", [])
        if archive_index >= len(archive_items):
            await query.message.reply_text("Тут ничего не нашлось 🫣")
            return
        item = archive_items[archive_index]
        heart_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❤️", callback_data=f"send_heart:{archive_index}")]
        ])
        if item.get("type") == "cem_photo":
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=item["file_id"],
                caption=f"💌 Любимая пишет...\n\n😽 {item.get('date', '')}",
            )
        else:
            await query.message.reply_text(f"💌 Любимая пишет...\n\n{item.get('text', '')}")
        await query.message.reply_text(
            "Хочешь отреагировать сердечком?",
            reply_markup=heart_keyboard,
        )
        return

    if data.startswith("send_heart:"):
        archive_index = int(data.split(":", 1)[1])
        archive_items = state.get("archive", [])
        if archive_index >= len(archive_items):
            await query.message.reply_text("Весточка потерялась 🫣")
            return
        author_chat_id = archive_items[archive_index].get("from_chat_id")
        if author_chat_id:
            await context.bot.send_message(
                chat_id=author_chat_id,
                text="Твою весточку увидели, улыбнулись и отправили сердечко в ответ ❤️",
            )
        await query.message.reply_text("Сердечко улетело 💌")


async def test_morning(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    today = datetime.now(TIMEZONE).date()
    days_left = (TARGET_DATE - today).days
    if today < COUNTDOWN_START:
        text = "Отсчёт начнётся 27 июля 🇪🇸"
    elif days_left > 0:
        wish = MORNING_WISHES[(today - COUNTDOWN_START).days % len(MORNING_WISHES)]
        text = (
            "<b>Доброе утрооо ☀️</b>\n\n"
            "До тёплой Испании осталось...\n"
            f"⏳ <b>{days_left} {days_word(days_left)}</b> ⏳\n\n{wish}"
        )
    elif days_left == 0:
        text = "<b>Сегодня тот самый день!</b> 🇪🇸\n\nТёплая Испания уже ждёт 💗"
    else:
        text = "Отсчёт уже завершён 🇪🇸"
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_menu())



async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.exception("Необработанная ошибка Telegram-бота", exc_info=context.error)


def main() -> None:
    if not TOKEN:
        raise RuntimeError(
            "Не найден BOT_TOKEN. Перед запуском укажи переменную окружения BOT_TOKEN."
        )

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("archive_add", archive_add))
    app.add_handler(CommandHandler("archive", archive))
    app.add_handler(CommandHandler("cem", cem))
    app.add_handler(CommandHandler("videos", show_trainings))
    app.add_handler(CommandHandler("test_morning", test_morning))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    app.job_queue.run_daily(
        morning,
        time=time(hour=MORNING_HOUR, minute=MORNING_MINUTE, tzinfo=TIMEZONE),
    )

    LOGGER.info("Бот запущен. Ожидаю сообщения...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
