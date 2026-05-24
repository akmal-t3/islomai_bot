import os
import anthropic
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

SYSTEM_PROMPT = """
Ты исламский учёный-ассистент. Отвечай на вопросы об исламе
на основе Корана, Сунны и мнений учёных.
Определяй язык вопроса автоматически и отвечай на том же языке.
Русский, английский, арабский, таджикский — все языки поддерживаются.
Цитируй источники: аяты Корана, хадисы, мнения улемов.
"""

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

async def start(update: Update, context):
    await update.message.reply_text(
        "Ассаляму алейкум! 🌙\n"
        "Я исламский ИИ-помощник.\n"
        "Задайте любой вопрос об исламе на русском, английском, арабском или таджикском языке."
    )

async def handle_message(update: Update, context):
    user_text = update.message.text
    await update.message.reply_text("⏳ Ищу ответ...")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_text}]
    )

    answer = response.content[0].text
    await update.message.reply_text(answer)

app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
