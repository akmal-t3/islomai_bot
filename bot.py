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


# EMBEDDINGS (FIXED)
def get_embedding(text):
    try:
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    except Exception as e:
        print("❌ EMBEDDING ERROR:", e)
        return None


# SUPABASE SEARCH (SAFE)
def search_books(question):
    embedding = get_embedding(question)

    if embedding is None:
        return ""

    try:
        result = supabase.rpc("match_documents", {
            "query_embedding": embedding,
            "match_count": 3
        }).execute()

        if result.data:
            return "\n\n".join([r["content"] for r in result.data])

    except Exception as e:
        print("❌ SUPABASE ERROR:", e)

    return ""


# START
async def start(update: Update, context):
    await update.message.reply_text(
        "Ассаляму алейкум! 🌙\n"
        "Я исламский ИИ-помощник.\n"
        "Задайте любой вопрос об исламе!"
    )


# MAIN HANDLER (FIXED)
async def handle_message(update: Update, context):
    user_text = update.message.text

    await update.message.reply_text("⏳ Ищу ответ в книгах...")

    # safe thread execution
    try:
        book_content = await asyncio.to_thread(search_books, user_text)
    except Exception as e:
        print("❌ THREAD ERROR:", e)
        book_content = ""

    if book_content:
        system = f"""Ты исламский учёный-ассистент.
Отвечай ТОЛЬКО на основе текстов:

{book_content}

Если ответа нет — скажи что не нашёл в базе."""
    else:
        system = """Ты исламский учёный-ассистент.
Отвечай на основе Корана и Сунны."""

    # Claude safe call
    try:
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": user_text}]
        )

        await update.message.reply_text(response.content[0].text)

    except Exception as e:
        print("❌ CLAUDE ERROR:", e)
        await update.message.reply_text("Ошибка AI сервиса. Попробуй позже.")


# APP
app = Application.builder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
