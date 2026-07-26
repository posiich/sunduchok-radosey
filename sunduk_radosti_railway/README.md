# Сундук радости

Telegram-бот с архивом, цемами, йогой, тренировками и ежедневным отсчётом до Испании.

## Railway Variables

Добавьте по отдельности:

- `BOT_TOKEN` — новый токен из BotFather
- `OWNER_CHAT_ID` — `6240720190`
- `TIMEZONE` — `Europe/Sofia`
- `MORNING_HOUR` — `9`
- `MORNING_MINUTE` — `20`

Railway запускает проект командой `python bot.py` из `railway.json`.

## Локальный запуск

1. Скопируйте `.env.example` в `.env`.
2. Вставьте новый токен.
3. Выполните:

```bash
python3 -m pip install -r requirements.txt
python3 bot.py
```
