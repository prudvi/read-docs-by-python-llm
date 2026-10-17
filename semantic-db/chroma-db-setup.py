import json
import re
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "newspaper_extraction_output"
MARKDOWN_PATH = OUTPUT_DIR / "complete_newspaper_layout.md"
MANIFEST_PATH = OUTPUT_DIR / "extraction_manifest.json"
DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "newspaper_layout"


def clean_text(text: str) -> str:
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    cleaned = re.sub(r"<!\-\-.*?\->", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def is_noise(text: str) -> bool:
    if not text:
        return True
    if text.startswith("<!--") or text.endswith("-->"):
        return True
    if re.fullmatch(r"[A-F0-9-]{8,}", text):
        return True
    if text.strip() in {"CM", "YK", "A", "BG-BGE"}:
        return True
    if len(text.split()) <= 2 and not any(char.isalnum() for char in text):
        return True
    return False


def chunk_markdown(text: str, max_chars: int = 1200) -> list[str]:
    paragraphs = re.split(r"\n{2,}", text)
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        cleaned = clean_text(paragraph)
        if not cleaned or is_noise(cleaned):
            continue

        if current and len(current) + len(cleaned) + 2 <= max_chars:
            current = f"{current}\n\n{cleaned}"
        else:
            if current:
                chunks.append(current)
            current = cleaned

    if current:
        chunks.append(current)

    return chunks


def load_markdown_chunks(markdown_path: Path) -> list[dict]:
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    content = markdown_path.read_text(encoding="utf-8")
    chunks = chunk_markdown(content)

    records = []
    for index, chunk in enumerate(chunks, start=1):
        records.append(
            {
                "id": f"chunk_{index:03d}",
                "document": chunk,
                "metadata": {
                    "source": markdown_path.name,
                    "chunk_index": index,
                    "chunk_length": len(chunk),
                },
            }
        )

    return records


def main() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading newspaper markdown from: {MARKDOWN_PATH}")
    records = load_markdown_chunks(MARKDOWN_PATH)

    if not records:
        raise RuntimeError("No content was extracted from the markdown file.")

    print(f"Loaded {len(records)} chunks from the newspaper layout.")

    client = chromadb.PersistentClient(path=str(DB_DIR))
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
    )

    collection.upsert(
        documents=[record["document"] for record in records],
        ids=[record["id"] for record in records],
        metadatas=[record["metadata"] for record in records],
    )

    print(f"Stored {len(records)} chunks in Chroma collection '{COLLECTION_NAME}'.")
    print(f"Chroma database path: {DB_DIR}")


if __name__ == "__main__":
    main()

