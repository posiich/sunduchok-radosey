"""Личный Telegram-бот: архив, цемы и сообщения участникам.
Установка: pip install python-telegram-bot>=21,<23
Запуск: установите переменную окружения BOT_TOKEN и выполните python love_bot_updated.py
"""
import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram import Update, ReplyKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
STATE_FILE = Path(__file__).with_name('state.json')
TIMEZONE = ZoneInfo('Europe/Sofia')
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

BUTTON_WRITE = '💌 Просто написать!'
BUTTON_ADD = '📦 Пополнить архив милостей'
BUTTON_CEM = '😽 Отправить цем!'
BUTTON_ARCHIVE = '💗 Посмотреть архив'
KEYBOARD = ReplyKeyboardMarkup([[BUTTON_WRITE, BUTTON_ADD], [BUTTON_CEM, BUTTON_ARCHIVE]], resize_keyboard=True, is_persistent=True)

PROMPTS = [
    'Пиши сообщение, а я отнесу любимой 💌',
    'Ну рассказывай! Я уже приготовил крылышки для доставки 🕊️',
    'Что передать твоему любимому человеку? 💗',
    'Пиши скорее, тут кое-кто очень ждёт весточку 🥹',
    'Давай свои самые тёплые слова, доставлю бережно ✨',
    'Тааак! Давай-давай, любимая уже ждет!',
    'Есть что сказать любимой? Я весь внимание 😽',
    'Твоё сообщение уже почти летит. Осталось его написать 💌',
    'Пиши! У меня сегодня экспресс-доставка нежностей 🐾',
    'Слушаю-смотрю-жду! Что отправим любимой? 🌷',
]


def load_state():
    if not STATE_FILE.exists():
        return {'users': [], 'chat_ids': [], 'archive': [], 'waiting': {}, 'prompt_bags': {}}
    with STATE_FILE.open(encoding='utf-8') as f:
        state = json.load(f)
    state.setdefault('users', [])
    state.setdefault('chat_ids', [])
    state.setdefault('archive', [])
    state.setdefault('waiting', {})
    state.setdefault('prompt_bags', {})
    return state


def save_state(state):
    temp = STATE_FILE.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    temp.replace(STATE_FILE)


def register(state, chat_id):
    if chat_id not in state['users']:
        state['users'].append(chat_id)
    if chat_id not in state['chat_ids']:
        state['chat_ids'].append(chat_id)


def next_prompt(state, chat_id):
    key = str(chat_id)
    bag = state['prompt_bags'].get(key, [])
    if not bag:
        bag = list(range(len(PROMPTS)))
        random.shuffle(bag)
        previous = state.get('last_prompt', {}).get(key)
        if previous is not None and bag[-1] == previous and len(bag) > 1:
            bag[0], bag[-1] = bag[-1], bag[0]
    index = bag.pop()
    state['prompt_bags'][key] = bag
    state.setdefault('last_prompt', {})[key] = index
    return PROMPTS[index]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    register(state, update.effective_chat.id)
    save_state(state)
    await update.message.reply_text('Привет, любимая! 💗\n\nЗдесь можно писать друг другу, сохранять весточки и собирать цемы. Выбирай кнопку на панельке 😽', reply_markup=KEYBOARD)


async def write(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    chat_id = update.effective_chat.id
    register(state, chat_id)
    state['waiting'][str(chat_id)] = 'write'
    prompt = next_prompt(state, chat_id)
    save_state(state)
    await update.effective_message.reply_text(prompt)


async def archive_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    chat_id = update.effective_chat.id
    register(state, chat_id)
    state['waiting'][str(chat_id)] = 'archive'
    save_state(state)
    await update.effective_message.reply_text('Напиши любое сообщение, и оно будет у нас в архиве! Жду)')


async def cem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    chat_id = update.effective_chat.id
    register(state, chat_id)
    state['waiting'][str(chat_id)] = 'cem'
    save_state(state)
    await update.effective_message.reply_text('Отправь милую/любую фотографию себя 😽\nИ она сохранится у нас!')


async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton('💌 Смотреть сообщения', callback_data='archive_messages')],
        [InlineKeyboardButton('😽 Смотреть цемы', callback_data='archive_cems')],
    ])
    await update.effective_message.reply_text('Что хочешь посмотреть в нашем архиве?', reply_markup=keyboard)


async def notify_archive(context, state, sender, index):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('🥹 Уии, посмотреть', callback_data=f'view_archive:{index}')]])
    for recipient in set(state['users']):
        if recipient == sender:
            continue
        try:
            await context.bot.send_message(recipient, 'Вам прилетела милая весточка из архива 💌', reply_markup=keyboard)
        except TelegramError as exc:
            log.warning('Не удалось уведомить %s: %s', recipient, exc)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return
    chat_id = update.effective_chat.id
    state = load_state()
    # Кнопки панели обрабатываются до режима ожидания сообщения.
    if msg.text == BUTTON_WRITE:
        await write(update, context)
        return
    if msg.text == BUTTON_ADD:
        await archive_add(update, context)
        return
    if msg.text == BUTTON_CEM:
        await cem(update, context)
        return
    if msg.text == BUTTON_ARCHIVE:
        await archive(update, context)
        return
    mode = state['waiting'].get(str(chat_id))
    if not mode:
        return

    if mode == 'write':
        # copy_message отправляет оригинальное содержимое без отметки «Переслано»
        # и без текста от бота; поддерживает текст, фото, видео, голосовые и т.д.
        recipients = set(state['users']) | set(state['chat_ids'])
        recipients.discard(chat_id)
        if not recipients:
            await msg.reply_text('Пока некому доставить сообщение. Другой участник должен сначала открыть бота и нажать /start.')
            return
        success = 0
        for recipient in recipients:
            try:
                await context.bot.copy_message(chat_id=recipient, from_chat_id=chat_id, message_id=msg.message_id)
                success += 1
            except TelegramError as exc:
                log.warning('Не удалось доставить сообщение %s: %s', recipient, exc)
        if success:
            state['waiting'].pop(str(chat_id), None)
            save_state(state)
            # Подтверждение только отправителю после успешной доставки.
            await msg.reply_text('💌')
        else:
            await msg.reply_text('Не получилось доставить сообщение. Попробуй ещё раз.')
        return

    if mode == 'archive':
        if not msg.text:
            await msg.reply_text('Для архива отправь текстовое сообщение 💌')
            return
        state['archive'].append({
            'date': datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M'),
            'type': 'text', 'text': msg.text, 'from_chat_id': chat_id,
        })
        index = len(state['archive']) - 1
        state['waiting'].pop(str(chat_id), None)
        save_state(state)
        await notify_archive(context, state, chat_id, index)
        await msg.reply_text('Сохранено в архив 💌')
        return

    if mode == 'cem':
        if not msg.photo:
            await msg.reply_text('Для цема отправь фотографию 😽')
            return
        state['archive'].append({
            'date': datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M'),
            'type': 'cem_photo', 'file_id': msg.photo[-1].file_id,
            'from_chat_id': chat_id,
        })
        index = len(state['archive']) - 1
        state['waiting'].pop(str(chat_id), None)
        save_state(state)
        await notify_archive(context, state, chat_id, index)
        await msg.reply_text('Готово 😽\nБережно-бережно отправлено в архив!')


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    query = update.callback_query
    await query.answer()
    state = load_state()
    data = query.data
    items = state['archive']

    if data == 'archive_messages':
        messages = [item for item in items if item.get('type') == 'text'][-15:]
        if not messages:
            await query.edit_message_text('Ай-яй-яй... сообщений пока нет...')
            return
        await query.edit_message_text('Наши сообщения 💌')
        for item in messages:
            await context.bot.send_message(query.message.chat_id, f"💌 {item.get('date', '')}\n{item.get('text', '')}")
        return
    if data == 'archive_cems':
        cems = [item for item in items if item.get('type') == 'cem_photo'][-15:]
        if not cems:
            await query.edit_message_text('Цемов пока нет... подозрительно тихо')
            return
        await query.edit_message_text('Архив цемов 😽')
        for item in cems:
            await context.bot.send_photo(query.message.chat_id, item['file_id'], caption=f"😽 {item.get('date', '')}")
        return
    if data.startswith('view_archive:') or data.startswith('send_heart:'):
        try:
            index = int(data.split(':', 1)[1])
            item = items[index] if index >= 0 else None
        except (ValueError, IndexError):
            item = None
        if item is None:
            await query.message.reply_text('Ой, весточка потерялась 🫣')
            return
        if data.startswith('send_heart:'):
            recipient = item.get('from_chat_id')
            if recipient:
                await context.bot.send_message(recipient, 'Твою весточку получили, увидели, оооочень улыбнулись! И отправили сердечко в ответ) ❤️')
                await query.message.reply_text('Клааасс, спасибо за реакцию! Цем тебя!)')
            return
        if item.get('type') == 'cem_photo':
            await context.bot.send_photo(query.message.chat_id, item['file_id'], caption=f"💌 Любимая пишет...\n\n😽 {item.get('date', '')}")
        else:
            await query.message.reply_text(f"💌 Любимая пишет...\n\n{item.get('text', '')}")
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('❤️', callback_data=f'send_heart:{index}')]])
        await query.message.reply_text('Хочешь отреагировать сердечком?)', reply_markup=keyboard)


async def setup_commands(app: Application):
    # Убираем старые команды из синего меню Telegram.
    await app.bot.delete_my_commands()


def main():
    if not TOKEN:
        raise RuntimeError('Укажите BOT_TOKEN в переменных окружения.')
    app = Application.builder().token(TOKEN).post_init(setup_commands).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('write', write))
    app.add_handler(CommandHandler('archive_add', archive_add))
    app.add_handler(CommandHandler('cem', cem))
    app.add_handler(CommandHandler('archive', archive))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(~filters.COMMAND & ~filters.StatusUpdate.ALL, handle_message))
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
