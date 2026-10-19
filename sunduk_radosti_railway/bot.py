"""Личный Telegram-бот: архив, цемы и сообщения участникам.
Установка: pip install python-telegram-bot>=21,<23
Запуск: установите переменную окружения BOT_TOKEN и выполните python bot.py
"""
import json
import logging
import os
import random
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
STATE_FILE = Path('/data/state.json')
OLD_STATE_FILE = Path(__file__).with_name('state.json')


def migrate_old_archive():
    """One-time, non-destructive migration from GitHub state.json to Volume."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not OLD_STATE_FILE.exists():
        return
    if STATE_FILE.exists():
        with STATE_FILE.open(encoding='utf-8') as f:
            current = json.load(f)
    else:
        current = {}
    if current.get('_legacy_archive_imported'):
        return
    with OLD_STATE_FILE.open(encoding='utf-8') as f:
        old = json.load(f)
    for field in ('users', 'chat_ids'):
        current[field] = list(dict.fromkeys(current.get(field, []) + old.get(field, [])))
    current.setdefault('archive', [])
    # Preserve new entries, adding only old entries not already present.
    # Match on stored fields; old entries sometimes have no from_chat_id.
    for item in old.get('archive', []):
        if item not in current['archive']:
            current['archive'].append(item)
    current.setdefault('waiting', {})
    current.setdefault('prompt_bags', {})
    current['_legacy_archive_imported'] = True
    save_state(current)


TIMEZONE = ZoneInfo('Europe/Sofia')
logging.basicConfig(level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
log = logging.getLogger(__name__)

BUTTON_WRITE = '💌 Просто написать!'
BUTTON_ADD = '📦 Пополнить архив милостей'
BUTTON_CEM = '😽 Отправить цем!'
BUTTON_ARCHIVE = '💗 Посмотреть архив'
BUTTON_PROPOSAL = '💡 Сделать предложение!'
BUTTON_VIEW_MESSAGES = '💌 Смотреть сообщения'
BUTTON_VIEW_CEMS = '😽 Смотреть цемы'
KEYBOARD = ReplyKeyboardMarkup([[BUTTON_WRITE, BUTTON_ADD], [BUTTON_CEM, BUTTON_ARCHIVE], [BUTTON_PROPOSAL]], resize_keyboard=True, is_persistent=True)

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
    state.setdefault('proposals', {})
    state.setdefault('proposal_drafts', {})
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


def archive_choice_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BUTTON_VIEW_MESSAGES, callback_data='archive_messages')],
        [InlineKeyboardButton(BUTTON_VIEW_CEMS, callback_data='archive_cems')],
    ])


def archive_author_label(item, viewer_id):
    """Old entries without from_chat_id have no verifiable author."""
    author_id = item.get('from_chat_id')
    if author_id is None:
        return ''
    return 'Ты: ' if str(author_id) == str(viewer_id) else 'Любимая: '


async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        'Что хочешь посмотреть в нашем архиве? 💗',
        reply_markup=archive_choice_keyboard(),
    )


async def show_archive_category(update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str):
    state = load_state()
    items = [item for item in state.get('archive', []) if item.get('type') == kind]
    chat_id = update.effective_chat.id
    title = '💌 Наши сообщения' if kind == 'text' else '😽 Наши цемы'
    await context.bot.send_message(chat_id=chat_id, text=f'{title}: {len(items)}')
    if not items:
        await context.bot.send_message(chat_id=chat_id, text='Пока здесь пусто 💗')
        return
    for item in items:
        author = archive_author_label(item, chat_id)
        try:
            if kind == 'text':
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"💌 {item.get('date', '')}\n\n{author}{item.get('text', '')}",
                )
            else:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=item['file_id'],
                    caption=f"😽 {item.get('date', '')}\n{author}".rstrip(),
                )
        except (TelegramError, KeyError) as exc:
            log.exception('Cannot send archived entry: %s', exc)
            await context.bot.send_message(chat_id=chat_id, text='Не удалось показать одну запись из архива.')


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


PROPOSAL_REPLIES = [
    'Твой ответ уже доставлен! 💌',
    'Уии, обратная связь улетела адресату 🕊️',
    'Передала твой выбор! 💗',
    'Готово, твой ответ уже ждут! ✨',
    'Письмо с ответом отправлено 😽',
    'Доставлено бережно и с любовью 🌷',
    'Твой голос учтён, адресат уведомлён 💞',
    'Ответ отправлен, всё по плану! 🐾',
    'Есть контакт! Твой выбор доставлен 💌',
    'Ура, ответ уже у автора предложения! 🥹',
]


def proposal_draft_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('✅ Отправить предложение', callback_data='proposal_publish')],
        [InlineKeyboardButton('❌ Отменить', callback_data='proposal_cancel')],
    ])


async def begin_proposal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = load_state()
    register(state, chat_id)
    state['waiting'].pop(str(chat_id), None)
    state['proposal_drafts'][str(chat_id)] = {'stage': 'text', 'text': '', 'options': []}
    save_state(state)
    await update.effective_message.reply_text(
        'Следующим сообщением напиши текст для своего предложения'
    )


async def proposal_input(update: Update, context: ContextTypes.DEFAULT_TYPE, state):
    msg = update.effective_message
    chat_id = str(update.effective_chat.id)
    draft = state['proposal_drafts'][chat_id]
    if not msg.text or not msg.text.strip():
        await msg.reply_text('Напиши текстом, пожалуйста 💌')
        return
    value = msg.text.strip()
    if draft['stage'] == 'text':
        if len(value) > 1000:
            await msg.reply_text('Сократи предложение до 1000 символов 💗')
            return
        draft['text'] = value
        draft['stage'] = 'options'
        save_state(state)
        await msg.reply_text(
            'Какие будут кнопочки к твоему предложению?)\n'
            'Например: «Я согласнааа!» или «Не солгласна, я кусь сейчас!»\n\n'
            'Можно создать от 1 до 4 кнопок, пиши мне их по одному.. И без премиум-эмодзи🙄 '
        )
        return
    if len(value) > 64:
        await msg.reply_text('Название кнопки должно быть не длиннее 64 символов 😽')
        return
    if value in draft['options']:
        await msg.reply_text('Такая кнопка уже есть. Придумай другую 💌')
        return
    if len(draft['options']) >= 4:
        await msg.reply_text('Максимум четыре кнопки. Нажми «Отправить предложение».', reply_markup=proposal_draft_keyboard())
        return
    draft['options'].append(value)
    save_state(state)
    count = len(draft['options'])
    summary = '\n'.join(f'{i}. {option}' for i, option in enumerate(draft['options'], 1))
    await msg.reply_text(
        f'Готовые варианты ({count}/4):\n{summary}\n\n'
        + ('Все четыре готовы! Отправляем?' if count == 4 else 'Напиши ещё один вариант или нажми «Отправить предложение». '),
        reply_markup=proposal_draft_keyboard(),
    )


async def proposal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ''
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    state = load_state()
    if data in ('proposal_cancel', 'proposal_publish'):
        draft = state['proposal_drafts'].get(str(chat_id))
        if not draft:
            await query.answer('Черновик уже закрыт', show_alert=True)
            return
        if data == 'proposal_cancel':
            state['proposal_drafts'].pop(str(chat_id), None)
            save_state(state)
            await query.answer()
            await query.edit_message_text('Предложение отменено 💗')
            return
        if not draft['text'] or not draft['options']:
            await query.answer('Сначала напиши предложение и хотя бы один вариант ответа', show_alert=True)
            return
        proposal_id = uuid.uuid4().hex[:12]
        proposal = {
            'author': chat_id,
            'text': draft['text'],
            'options': draft['options'][:4],
            'responses': {},
        }
        state['proposals'][proposal_id] = proposal
        state['proposal_drafts'].pop(str(chat_id), None)
        save_state(state)
        await query.answer()
        await query.edit_message_text('Предложение создано! 💌')
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(label, callback_data=f'proposal_vote:{proposal_id}:{i}')]
            for i, label in enumerate(proposal['options'])
        ])
        delivered = 0
        for recipient in set(state['users']) | set(state['chat_ids']):
            if str(recipient) == str(chat_id):
                continue
            try:
                await context.bot.send_message(recipient, proposal['text'], reply_markup=keyboard)
                delivered += 1
            except TelegramError:
                log.exception('Не удалось доставить предложение участнику')
        await context.bot.send_message(chat_id, f'💌 Предложение отправлено {delivered} участникам!')
        return
    if data.startswith('proposal_vote:'):
        try:
            _, proposal_id, option_index_text = data.split(':')
            option_index = int(option_index_text)
        except (ValueError, TypeError):
            await query.answer('Некорректная кнопка', show_alert=True)
            return
        proposal = state['proposals'].get(proposal_id)
        if not proposal or not 0 <= option_index < len(proposal['options']):
            await query.answer('Это предложение уже недоступно', show_alert=True)
            return
        if str(proposal['author']) == str(chat_id):
            await query.answer('Это твоё предложение 💗', show_alert=True)
            return
        if str(user_id) in proposal['responses']:
            await query.answer('Ты уже ответила на это предложение 💗', show_alert=True)
            return
        option = proposal['options'][option_index]
        proposal['responses'][str(user_id)] = option
        save_state(state)
        await query.answer()
        await context.bot.send_message(chat_id, random.choice(PROPOSAL_REPLIES))
        try:
            await context.bot.send_message(
                proposal['author'],
                f'💌 На твоё предложение:\n«{proposal["text"]}»\n\n'
                f'Ответили: «{option}» 💗',
            )
        except TelegramError:
            log.exception('Не удалось доставить ответ автору предложения')
        return


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return
    chat_id = update.effective_chat.id
    state = load_state()
    # Кнопки панели обрабатываются до режима ожидания сообщения.
    if msg.text == BUTTON_PROPOSAL:
        await begin_proposal(update, context)
        return
    if str(chat_id) in state['proposal_drafts']:
        await proposal_input(update, context, state)
        return
    # Old reply-keyboard buttons remain usable in existing Telegram chats.
    if msg.text == BUTTON_VIEW_MESSAGES:
        await show_archive_category(update, context, 'text')
        await msg.reply_text('Основное меню 💗', reply_markup=KEYBOARD)
        return
    if msg.text == BUTTON_VIEW_CEMS:
        await show_archive_category(update, context, 'cem_photo')
        await msg.reply_text('Основное меню 💗', reply_markup=KEYBOARD)
        return
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
    query = update.callback_query
    if query is None:
        return
    log.info('Archive button pressed: %s', query.data)
    await query.answer()
    data = query.data or ''
    if data.startswith('proposal_'):
        await proposal_callback(update, context)
        return

    if data in ('archive_messages', 'archive_cems'):
        kind = 'text' if data == 'archive_messages' else 'cem_photo'
        # Keep the two choices below the original message.
        # Show content in separate messages, using the same delivery path that worked.
        await show_archive_category(update, context, kind)
        return

    if data.startswith('view_archive:') or data.startswith('send_heart:'):
        state = load_state()
        items = state['archive']
        try:
            index = int(data.split(':', 1)[1])
            item = items[index] if 0 <= index < len(items) else None
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
            else:
                await query.message.reply_text('У этой старой записи не сохранился отправитель 🥺')
            return
        if item.get('type') == 'cem_photo':
            await context.bot.send_photo(query.message.chat_id, item['file_id'], caption=f"💌 Любимая пишет...\n\n😽 {item.get('date', '')}")
        else:
            await query.message.reply_text(f"💌 Любимая пишет...\n\n{item.get('text', '')}")
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('❤️', callback_data=f'send_heart:{index}')]])
        await query.message.reply_text('Хочешь отреагировать сердечком?)', reply_markup=keyboard)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error('Telegram update processing failed', exc_info=context.error)


async def setup_commands(app: Application):
    # Убираем старые команды из синего меню Telegram.
    await app.bot.delete_my_commands()


def main():
    if not TOKEN:
        raise RuntimeError('Укажите BOT_TOKEN в переменных окружения.')
    migrate_old_archive()
    app = Application.builder().token(TOKEN).post_init(setup_commands).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('write', write))
    app.add_handler(CommandHandler('archive_add', archive_add))
    app.add_handler(CommandHandler('cem', cem))
    app.add_handler(CommandHandler('archive', archive))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(on_error)
    app.add_handler(MessageHandler(~filters.COMMAND & ~filters.StatusUpdate.ALL, handle_message))
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
