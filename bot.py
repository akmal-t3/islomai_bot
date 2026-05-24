import asyncio
import os
import anthropic
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from supabase import create_client
import openai

# ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY
claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


# EMBEDDINGS
def get_embedding(text):
    response = openai.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


# SUPABASE SEARCH
def search_books(question):
    embedding = get_embedding(question)

    result = supabase.rpc("match_documents", {
        "query_embedding": embedding,
        "match_count": 3
    }).execute()

    if result.data:
        return "\n\n".join([r["content"] for r in result.data])

    return ""


# START COMMAND
async def start(update: Update, context):
    await update.message.reply_text(
        "Ассаляму алейкум! 🌙\n"
        "Я исламский ИИ-помощник.\n"
        "Задайте любой вопрос об исламе!"
    )


# MAIN HANDLER
async def handle_message(update: Update, context):
    user_text = update.message.text

    await update.message.reply_text("⏳ Ищу ответ в книгах...")

    # FIX: run blocking code in thread
    book_content = await asyncio.to_thread(search_books, user_text)

    if book_content:
        system = f"""Ты исламский учёный-ассистент.
Отвечай на вопросы ТОЛЬКО на основе этих текстов из книг:

{book_content}

Отвечай на том же языке что и вопрос.
Если в текстах нет ответа — скажи что не нашёл в базе знаний."""
    else:
        system = """Ты исламский учёный-ассистент.
Отвечай на основе Корана, Сунны и мнений учёных.
Отвечай на том же языке что и вопрос."""

    # Claude request
    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=[
            {"role": "user", "content": user_text}
        ]
    )

    await update.message.reply_text(response.content[0].text)


# APP SETUP
app = Application.builder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
