import os
import openai
from supabase import create_client
import PyPDF2

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

def read_pdf(path):
    text = ""
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

def split_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

def upload_pdf(filename):
    print(f"Читаю {filename}...")
    text = read_pdf(filename)
    chunks = split_text(text)
    print(f"Найдено {len(chunks)} частей. Загружаю...")
    for i, chunk in enumerate(chunks):
        embedding = openai.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        ).data[0].embedding
        supabase.table("documents").insert({
            "content": chunk,
            "embedding": embedding
        }).execute()
        print(f"Загружено {i+1}/{len(chunks)}")
    print(f"{filename} — готово!")

upload_pdf("kniga1.pdf")
