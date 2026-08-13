import json
from datetime import date, time, datetime
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.ext import MessageHandler, filters

TOKEN = "8479252342:AAEEpFfheLieyIUC1hex2WVjf2EzQ7mQJyE"

TARGET_DATE = date(2026, 8, 27)
TIMEZONE = ZoneInfo("Europe/Sofia")


def load_state():
    with open("state.json", "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open("state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


daily_wishes = {
    "2026-08-13": "",
    "2026-08-14": "Хии, неожиданно? Люблю тебя очень! Скучаю, и жду, когда ты вернешься назад",
    "2026-08-15": (
    "Желаю тебе сегодня приятнейшего дня... со мной! "
    '<tg-emoji emoji-id="5235734531629129786">🥁</tg-emoji>'
),
    
    "2026-08-16": (
    "Любимая, а что если сегодня... я, ты, суши на закате... Свидание?)"
    '<tg-emoji emoji_id": "5453930874699542906">🥰</tg-emoji>''<tg-emoji emoji_id": "5453930874699542906">🥰</tg-emoji>''<tg-emoji emoji_id": "5453930874699542906">🥰</tg-emoji>'
),
    
    "2026-08-17": "Цем цем цем мое солнышко! Желаю легкого дня!",
    
    "2026-08-18": (
    "Желаю тебе сегодня милого и доброго дня.. И моих теплых обнимашек",
    '<tg-emoji emoji_id": "5348213226825854167">🥴</tg-emoji>'
),    
    
    "2026-08-19": "Желаю приятных разговоров... и спокойной работы",
    
    "2026-08-20": "Желаю сегодня вкусно и правильно покушать",
    
    "2026-08-21": "Желаю любименькой сегодня сил и энергии! Ты выу! Помнишь? Всегда знай! Я восхищаюсь и люблю тебя!",
    
    "2026-08-22": (
    "Останется чуть-чуть... и мы будем в теплой Испании"
    '<tg-emoji emoji_id": "5242677827299450340">🐷</tg-emoji>''<tg-emoji emoji_id": "5242677827299450340">🐷</tg-emoji>'
), 
    
    "2026-08-23": "Желаю ту-ту-туу... прокатиться с любимой за лате и чизкейком. Обещаю вести идеально!",
    
    "2026-08-24": "Желаю наслаждаться каждой минуткой, ведь осталось чуть-чуть работы этим летом",
    
    "2026-08-25": (
    "Желаю нам завтра легко и быстро собрать багаж! Помню, что не любишь, но ИСПАНИЯ, любимая!!"
    '<tg-emoji emoji-id="5235734531629129786">🥁</tg-emoji>''<tg-emoji emoji-id="5235734531629129786">🥁</tg-emoji>''<tg-emoji emoji-id="5235734531629129786">🥁</tg-emoji>''<tg-emoji emoji-id="5235734531629129786">🥁</tg-emoji>'
),
    
    "2026-08-26": "Лююююбимая! А завтра мы летииим! Благодарна жизни за тебя! Спасибо! Я счастлива с тобой путешестовать! Желаю нам спокойного и классного дня тут!",
}
training_videos = {
    "2026-05-16": {
        "title": "Йога вступительная 🪷",
        "file_id": "BAACAgQAAxkBAAIBmWoIBgABf0KucHctNDiRsmfGB2JDjgACHB4AAh3mQFAWIimEQyoofjsE",
        "caption": (
            "ЙОГА ВСТУПИТЕЛЬНАЯ\n"
            "🔓 Урок 0\n\n"
            "Теперь доступно!\n\n"
            "Это вступительный урок, чтобы познакомить тебя с каким-то базовыми аспектами и проверить твою готовность 🌿\n\n"
            "⏰ <b>Когда лучше выполнять?</b>\n"
            "В любое время, но желательно, чтобы прошло 2–3 часа после еды.\n"
            "(Впрочем, как и для любой тренировки)\n\n"
            '<tg-emoji emoji-id="5336864029149257027">🪷</tg-emoji> '
            "Здесь я стараюсь всё объяснять максимально подробно.\n"
            "Дальше этого будет чуть меньше, но главное и важное я буду рассказывать всегда ✨\n\n"
            "💗 В этом уроке я затрону базовые переходы и акценты в йоге.\n"
            "А дальше мы будем двигаться уже чуть активнее 🌙\n\n"
            '<tg-emoji emoji-id="5336864029149257027">🪷</tg-emoji> '
            "И я очень жду от тебя обратную связь!\n"
            "Расскажи все! Что почувствовала, что понравилось, что было сложно и как ты себя ощущаешь 💗"
        )
    },
    "2026-05-18": {
        "title": "25 минут - Легкость в теле",
        "file_id": "BAACAgQAAxkBAAIBtmoJ3N-0AAHjBysgXNWDs44ngzFsXgACqyAAArwVUVCHFCqtu3coWTsE",
        "caption": (
            "Сегодня тебя ждёт тренировка на лёгкость в теле!\n\n"
            "⏰ <b>Когда лучше выполнять?</b>\n"
            "В любое время, но желательно, чтобы прошло 2–3 часа после еды.\n"
            "Тренировка для того, чтобы хорошенько разогнать энергию в теле, почувстовать себя гибче, свободнее и легче :)\n\n"
            "Я еще не профессиональный тренер, поэтому представляй, что ты просто занимаешься со мной) Я рядом, я с тобой! И мы вместе занимаемся!)"
            "И я очень жду от тебя обратную связь!\n"
        )
    },
    "2026-05-20": {
        "title": "20 минут - утренняя йога - энергия на день",
        "file": "video_2.mp4",
        "caption": (
            "Сегодня тебя ждёт тренировка на лёгкость в теле 🌿\n\n"
            "Не спеши. Дыши. Почувствуй себя.\n\n"
            "Я рядом, включай видео 💗"
        )
    },
    "2026-05-30": {
        "title": "Раскрытие грудного отдела и шеи 🫶",
        "file": "video_3.mp4",
        "caption": "Тренировка на сегодня: Раскрытие грудного отдела и шеи 🫶"
    },
    "2026-05-30": {
        "title": "Йога детокс для иммунной системы 🍃",
        "file": "video_4.mp4",
        "caption": "Тренировка на сегодня: Йога детокс для иммунной системы 🍃"
    },
    "2026-05-30": {
        "title": "Сила спины с мячиком 🎾",
        "file": "video_5.mp4",
        "caption": "Тренировка на сегодня: Сила спины с мячиком 🎾"
    },
    "2026-05-30": {
        "title": "Вечерняя йога 🌙",
        "file": "video_6.mp4",
        "caption": "Тренировка на сегодня: Вечерняя йога 🌙"
    },
    "2026-05-24": {
        "title": "Гибкость и сила позвоночника 🌀",
        "file": "video_7.mp4",
        "caption": "Тренировка на сегодня: Гибкость и сила позвоночника 🌀"
    },
    "2026-05-25": {
        "title": "Йога на тазобедренные суставы 🧘‍♀️",
        "file": "video_8.mp4",
        "caption": "Тренировка на сегодня: Йога на тазобедренные суставы 🧘‍♀️"
    },
    "2026-05-26": {
        "title": "Для осанки ✨",
        "file": "video_9.mp4",
        "caption": "Тренировка на сегодня: Для осанки ✨"
    },
    "2026-05-27": {
        "title": "Йога среднего уровня 🔥",
        "file": "video_10.mp4",
        "caption": "Тренировка на сегодня: Йога среднего уровня 🔥"
    },
    "2026-05-28": {
        "title": "Бонусная — Йога YIN 🤍",
        "file": "video_11.mp4",
        "caption": "Бонусная тренировка: Йога YIN 🤍"
    },
}

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    chat_id = update.effective_chat.id

    if "users" not in state:
        state["users"] = []

    if chat_id not in state["users"]:
        state["users"].append(chat_id)

    if "chat_ids" not in state:
        state["chat_ids"] = []

    if chat_id not in state["chat_ids"]:
        state["chat_ids"].append(chat_id)

    if "archive" not in state:
        state["archive"] = []

    if state.get("start_date") is None:
        state["start_date"] = str(datetime.now(TIMEZONE).date())

    save_state(state)

    await update.message.reply_text(
        'Привет, моя дорогая Света '
        '<tg-emoji emoji-id="5235734531629129786">✨</tg-emoji>\n\n'
        'В этом сундуке будут происходить чудеса... и очень много всего полезного. Так что уведомления не отключай и можешь даже себе закрепить этот бот куда-то)\n\n'
        '<b>Что тебя тут ждёт?</b>\n\n'
        '🔔 Каждое утро будет приходить напоминание, сколько дней осталось до тёплой Испании\n\n'
        '🧘‍♀️ Здесь же тебя ждут 10 дней тренировок + йога со мной. Но чуть позже, имей терпение... пока считаем дни!)\n\n'
        '🎁 А после 10.06, на всё лето... тебе будет нужен этот бот! Будет выдвавать загадки и подарочки! Все лето, представляешь!?\n\n'
        'Так что не теряй его! Будет классно! Цем!\n\n'
        '<tg-emoji emoji-id="5240175914360250771">😺</tg-emoji>\n\n',
        parse_mode="HTML"
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


async def morning(context: ContextTypes.DEFAULT_TYPE):
    state = load_state()

    today = datetime.now(TIMEZONE).date()
    days_left = (TARGET_DATE - today).days

    wish = daily_wishes.get(today.isoformat(), "").strip()

    if days_left > 0:
        text = (
            'Доброе утроооо ☀️'
            '<tg-emoji emoji-id="5256215937878609569">🐤</tg-emoji>\n\n'
            'До Испании вместе осталось...\n'
            f'⏳ <b>{days_left} {days_word(days_left)}</b> ⏳'
            + (f'\n\n{wish}' if wish else '')
        )
    elif days_left == 0:
        text = (
            'Доброе утроооо ☀️'
            '<tg-emoji emoji-id="5256215937878609569">🐤</tg-emoji>\n\n'
            '<b>Сегодня тот самый день!</b> 🇪🇸\n\n'
            'Ураааа, любимаяяя! Мы летим вместе отдыхааать!! ✈️💗'
        )
    else:
        return

    chat_ids = state.get("chat_ids", [])

    morning_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Хочу написать что-то в ответ!",
                callback_data="morning_reply"
            )
        ],
        [
            InlineKeyboardButton(
                "Кусь 💩",
                callback_data="morning_brat"
            )
        ]
    ])

    for chat_id in chat_ids:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                reply_markup=morning_keyboard
            )
            print(f"Утро отправлено: {chat_id}")
        except Exception as e:
            print(f"Ошибка утреннего сообщения для {chat_id}: {e}")


async def send_training_video(context: ContextTypes.DEFAULT_TYPE):
    state = load_state()

    today = datetime.now(TIMEZONE).date()
    today_str = today.isoformat()

    video_data = training_videos.get(today_str)

    if not video_data:
        print("На сегодня тренировки нет")
        return

    chat_ids = state.get("chat_ids", [])

    feedback_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💌 Оставить свои впечатления",
                callback_data="lesson_feedback"
            )
        ]
    ])

    for chat_id in chat_ids:
        try:
            if "file_id" in video_data:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=video_data["file_id"],
                    caption=video_data["caption"],
                    parse_mode="HTML",
                    reply_markup=feedback_keyboard,
                    supports_streaming=True
                )

            else:
                with open(video_data["file"], "rb") as video:
                    await context.bot.send_video(
                        chat_id=chat_id,
                        video=video,
                        caption=video_data["caption"],
                        parse_mode="HTML",
                        reply_markup=feedback_keyboard,
                        supports_streaming=True,
                        write_timeout=300,
                        read_timeout=300,
                        connect_timeout=300,
                        pool_timeout=300
                    )

            print(f"Видео отправлено: {chat_id}")

        except Exception as e:
            print(f"Ошибка видео для {chat_id}: {e}")


async def test_morning(update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(TIMEZONE).date()
    days_left = (TARGET_DATE - today).days

    wish = daily_wishes.get(today.isoformat(), "").strip()

    if days_left > 0:
        text = (
            "🔬 ТЕСТ УТРА\n\n"
            'Доброе утроооо ☀️'
            '<tg-emoji emoji-id="5256215937878609569">🐤</tg-emoji>\n\n'
            'До Испании вместе осталось...\n'
            f'⏳ <b>{days_left} {days_word(days_left)}</b> ⏳'
            + (f'\n\n{wish}' if wish else '')
        )
    elif days_left == 0:
        text = (
            "🔬 ТЕСТ УТРА\n\n"
            '<b>Сегодня тот самый день!</b> 🇪🇸\n\n'
            'Ураааа, любимаяяя! Мы летим вместе отдыхааать!! ✈️💗'
        )
    else:
        text = "Отсчёт уже завершён 🇪🇸"

    morning_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Хочу написать что-то в ответ!",
                callback_data="test_morning_reply"
            )
        ]
    ])

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=morning_keyboard
    )


async def videos(update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Сгораю от нетерпения!", callback_data="show_videos")]
    ]

    await update.message.reply_text(
        "Хочешь заглянуть в тренировки? 👀",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def send_game_start(context: ContextTypes.DEFAULT_TYPE):
    state = load_state()

    text = (
        "🎉 <b>ИГРА НАЧИНАЕТСЯ!</b> 🎉\n\n"
        "Мы будем вместе всё лето 🌞\n\n"
        "Начиная с сегодняшнего дня до 1 сентября — 82 дня!\n\n"
        "И чтобы не потерять счёт времени, предлагаю тебе вести обратный отсчёт...\n\n"
        "Каждый день ты будешь находить по одной маленькой ящерке 🦎\n"
        "и вклеивать её в таблицу обратного отсчёта\n\n"
        "Где находить?) А везде! Будь внимательна в течнии всего дня))) Цеееем тебя!"
    )

    for chat_id in state.get("chat_ids", []):
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML"
        )

async def archive_add(update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()

    state["waiting_for_archive_message"] = True
    state["waiting_for_test_reply"] = None
    state["waiting_for_morning_reply"] = None
    state["waiting_for_lesson_feedback"] = None

    save_state(state)

    await update.message.reply_text(
        "Напиши любое сообщение и оно будет у нас в архиве! Жду)",
        parse_mode="HTML"
    )


async def handle_text(update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()

    waiting_answer = state.get("waiting_for_morning_answer")

    if waiting_answer and waiting_answer.get("from_chat_id") == update.effective_chat.id:
        answer_text = update.message.text
        recipient_chat_id = waiting_answer["to_chat_id"]

        state["waiting_for_morning_answer"] = None
        save_state(state)

        await context.bot.send_message(
            chat_id=recipient_chat_id,
            text=f"Тебе прилетела ответочка на ответочку 💌\n\n{answer_text}"
        )

        await update.message.reply_text("💌")
        return

    if state.get("waiting_for_lesson_feedback") == update.effective_chat.id:
        feedback_text = update.message.text

        state["waiting_for_lesson_feedback"] = None
        save_state(state)

        await context.bot.send_message(
            chat_id=6240720190,
            text=f"Пришли впечатления от тренировки 🌿\n\n{feedback_text}"
        )

        await update.message.reply_text("🍓")
        return

    if state.get("waiting_for_test_reply") == update.effective_chat.id:
        state["waiting_for_test_reply"] = None
        save_state(state)

        await update.message.reply_text(
            "Тестовая ответочка получена 😺\n\n"
            "Ничего никому не отправляю!"
        )
        return

    if state.get("waiting_for_morning_reply") == update.effective_chat.id:
        reply_text = update.message.text
        sender_chat_id = update.effective_chat.id

        state["waiting_for_morning_reply"] = None
        save_state(state)

        answer_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💌 Ответить на ответочку",
                    callback_data=f"answer_morning:{sender_chat_id}"
                )
            ]
        ])

        for user_chat_id in state.get("users", []):
            if user_chat_id != sender_chat_id:
                await context.bot.send_message(
                    chat_id=user_chat_id,
                    text=f"Вам прилетела ответочка на утро!\n\n{reply_text}",
                    reply_markup=answer_keyboard
                )

        await update.message.reply_text(
            'Как милоооо, идем активничать! '
            '<tg-emoji emoji-id="5443132326189996902">🧑‍💻</tg-emoji>',
            parse_mode="HTML"
        )
        return

    if not state.get("waiting_for_archive_message"):
        return

    message = update.message.text

    if "archive" not in state:
        state["archive"] = []

    state["archive"].append({
        "date": datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M"),
        "type": "text",
        "text": message,
        "from_chat_id": update.effective_chat.id
    })

    archive_index = len(state["archive"]) - 1

    state["waiting_for_archive_message"] = False
    save_state(state)

    await notify_others_about_archive(
        context=context,
        state=state,
        sender_chat_id=update.effective_chat.id,
        archive_index=archive_index
    )

    await update.message.reply_text("Сохранено в архив 💌")

async def archive(update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💌 Смотреть сообщения", callback_data="archive_messages")],
        [InlineKeyboardButton("😽 Смотреть цемы", callback_data="archive_cems")]
    ]

    await update.message.reply_text(
        "Что хочешь посмотреть в нашем архиве?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cem(update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()

    state["waiting_for_cem_photo"] = True
    save_state(state)

    await update.message.reply_text(
        "Отправь милую/любую фотографию себя 😽\n"
        "И она сохранится у нас!"
    )


async def handle_photo(update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()

    if not state.get("waiting_for_cem_photo"):
        return

    photo = update.message.photo[-1]

    if "archive" not in state:
        state["archive"] = []

    state["archive"].append({
        "date": datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M"),
        "type": "cem_photo",
        "file_id": photo.file_id,
        "from_chat_id": update.effective_chat.id
    })

    archive_index = len(state["archive"]) - 1

    state["waiting_for_cem_photo"] = False
    save_state(state)

    await notify_others_about_archive(
        context=context,
        state=state,
        sender_chat_id=update.effective_chat.id,
        archive_index=archive_index
    )

    await update.message.reply_text(
        "Готово 😽\n"
        "Бережно-бережно отправлено в архив!"
    )


async def notify_others_about_archive(context, state, sender_chat_id, archive_index):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🥹 Уии, посмотреть",
                callback_data=f"view_archive:{archive_index}"
            )
        ]
    ])

    for user_chat_id in state.get("users", []):
        if user_chat_id != sender_chat_id:
            await context.bot.send_message(
                chat_id=user_chat_id,
                text="Вам прилетела милая весточка из архива 💌",
                reply_markup=keyboard
            )


async def button_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    state = load_state()
    data = query.data

    if data == "morning_reply":
        state["waiting_for_morning_reply"] = query.message.chat_id
        save_state(state)

        await query.message.reply_text("Хиии, что сегодня скажешь?))")
        return

    if data == "test_morning_reply":
        state["waiting_for_test_reply"] = query.message.chat_id
        save_state(state)

        await query.message.reply_text(
            "Хиии, что сегодня скажешь?))\n\n"
            "Это тест, другим ничего не уйдёт."
        )
        return
    
    if data.startswith("answer_morning:"):
        recipient_chat_id = int(data.split(":")[1])

        state["waiting_for_morning_answer"] = {
            "from_chat_id": query.message.chat_id,
            "to_chat_id": recipient_chat_id
        }
        save_state(state)

        await query.message.reply_text(
            "Пиши ответочку на ответочку, я передам 💌"
        )
        return

    if data == "lesson_feedback":
        state["waiting_for_lesson_feedback"] = query.message.chat_id
        save_state(state)

        await query.message.reply_text(
            "Урааа, расскажи свои впечатления!"
            '<tg-emoji emoji-id="5235734531629129786">🥁</tg-emoji>',
            parse_mode="HTML"
        )
        return

    if data.startswith("react_morning:"):
        sender_chat_id = int(data.split(":")[1])

        await context.bot.send_message(
            chat_id=sender_chat_id,
            text="Твоё сообщение прочитано и это было ооочень приятно 🌞"
        )

        await query.message.reply_text("Реакция улетела ❤️")
        return

    if data == "show_videos":
        buttons = []
        today = datetime.now(TIMEZONE).date()

        for video_date_str, video in training_videos.items():
            video_date = date.fromisoformat(video_date_str)

            if today < video_date:
                title = f"🔒 {video['title']}"
            else:
                title = f" {video['title']}"

            buttons.append([
                InlineKeyboardButton(title, callback_data=video_date_str)
            ])

        await query.edit_message_text(
            "Вот список тренировок 💪\n\n"
            "Но пока рановато открывать их 🫣",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data == "archive_messages":
        archive_items = state.get("archive", [])
        messages = [item for item in archive_items if item.get("type") == "text"]

        if not messages:
            await query.edit_message_text("Ай-яй-яй... сообщений пока нет...")
            return

        text = "<b>Наши сообщения 💌</b>\n\n"

        for item in messages[-15:]:
            text += f"💌 {item.get('date', '')}\n{item.get('text', '')}\n\n"

        await query.edit_message_text(text, parse_mode="HTML")
        return

    if data == "archive_cems":
        archive_items = state.get("archive", [])
        cems = [item for item in archive_items if item.get("type") == "cem_photo"]

        if not cems:
            await query.edit_message_text("Цемов пока нет... подозрительно тихо")
            return

        await query.edit_message_text(
            "<b>Архив цемов 😽</b>",
            parse_mode="HTML"
        )

        for item in cems[-15:]:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=item["file_id"],
                caption=f"😽 {item.get('date', '')}"
            )

        return

    if data.startswith("view_archive:"):
        archive_index = int(data.split(":")[1])
        archive_items = state.get("archive", [])

        if archive_index >= len(archive_items):
            await query.message.reply_text("Ой-йой! Тут ничего не было, тебе показалось)")
            return

        item = archive_items[archive_index]

        heart_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❤️",
                    callback_data=f"send_heart:{archive_index}"
                )
            ]
        ])

        if item.get("type") == "cem_photo":
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=item["file_id"],
                caption=(
                    f"💌 Любимая пишет...\n\n"
                    f"😽 {item.get('date', '')}"
                )
            )
        else:
            await query.message.reply_text(
                f"💌 Любимая пишет...\n\n"
                f"{item.get('text', '')}"
            )

        await query.message.reply_text(
            "Хочешь отреагировать сердечком?)",
            reply_markup=heart_keyboard
        )
        return

    if data.startswith("send_heart:"):
        archive_index = int(data.split(":")[1])
        archive_items = state.get("archive", [])

        if archive_index >= len(archive_items):
            await query.message.reply_text("Ой, весточка потерялась 🫣")
            return

        item = archive_items[archive_index]
        author_chat_id = item.get("from_chat_id")

        if not author_chat_id:
            await query.message.reply_text("Не получилось найти, кому отправить сердечко 🫣")
            return

        await context.bot.send_message(
            chat_id=author_chat_id,
            text="Твою весточку получили, увидели, оооочень улыбнулись! И отправили сердечко в ответ) ❤️"
        )

        await query.message.reply_text("Клааасс, спасибо за реакцию! Цем тебя!) ")
        return

    if data == "later_archive":
        await query.message.reply_text(
            'Хорошо, оно будет ждать своего часа '
            '<tg-emoji emoji-id="5443132326189996902">🧑‍💻</tg-emoji>',
            parse_mode="HTML"
        )
        return

    if data in training_videos:
        video = training_videos.get(data)
        video_date = date.fromisoformat(data)
        today = datetime.now(TIMEZONE).date()

        if today < video_date:
            await query.answer(
                "Какая нетерпеливая!) Не тыкай! Еще рано! 😏",
                show_alert=True
            )
            return

        await query.edit_message_text(
            f"{video['title']} 💪\n\n"
            "Скоро здесь появится тренировка"
        )
        return


async def test(update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(TIMEZONE).date()
    days_left = (TARGET_DATE - today).days

    wish = daily_wishes.get(today.isoformat(), "").strip()

    if days_left > 0:
        text = (
            '🔬 ТЕСТ\n\n'
            'Доброе утроооо ☀️'
            '<tg-emoji emoji-id="5256215937878609569">🐤</tg-emoji>\n\n'
            'До Испании вместе осталось...\n'
            f'⏳ <b>{days_left} {days_word(days_left)}</b> ⏳'
            + (f'\n\n{wish}' if wish else '')
        )
    elif days_left == 0:
        text = (
            '🔬 ТЕСТ\n\n'
            '<b>Сегодня тот самый день!</b> 🇪🇸\n\n'
            'Ураааа, любимаяяя! Мы летим вместе отдыхааать!! ✈️💗'
        )
    else:
        text = "Отсчёт уже завершён 🇪🇸"

    test_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Хочу написать что-то в ответ!",
                callback_data="test_morning_reply"
            )
        ]
    ])

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=test_keyboard
    )


async def get_video_id(update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        await update.message.reply_text(update.message.video.file_id)
    elif update.message.document:
        await update.message.reply_text(update.message.document.file_id)

async def send_video_now(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пробую отправить сегодняшнюю тренировку 🎥")
    await send_training_video(context)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("test_morning", test_morning))
    app.add_handler(CommandHandler("videos", videos))
    app.add_handler(CommandHandler("archive_add", archive_add))
    app.add_handler(CommandHandler("archive", archive))
    app.add_handler(CommandHandler("cem", cem))

    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, get_video_id))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CommandHandler("send_video_now", send_video_now))
    
    app.job_queue.run_daily(
        morning,
        time=time(hour=7, minute=7, tzinfo=TIMEZONE)
    )

    app.job_queue.run_daily(
        send_training_video,
        time=time(hour=8, minute=31, tzinfo=TIMEZONE)
    )

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
