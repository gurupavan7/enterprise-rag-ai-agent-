import os

from config import APP_NAME, APP_VERSION
from utils import (
    load_text_file,
    clean_text,
    chunk_text,
    create_embeddings,
    create_faiss_index,
    save_faiss_index,
    load_faiss_index,
    search_faiss
)

print("Application:", APP_NAME)
print("Version:", APP_VERSION)

document = load_text_file(
    "data/company_policy.txt"
)

cleaned_document = clean_text(document)

chunks = chunk_text(
    cleaned_document,
    chunk_size=20
)

faiss_file = "data/company_policy.index"

if os.path.exists(faiss_file):
    print("\nLoading existing FAISS index...")

    index = load_faiss_index(
        faiss_file
    )

else:
    print("\nCreating FAISS index...")

    chunk_embeddings = create_embeddings(
        chunks
    )

    index = create_faiss_index(
        chunk_embeddings
    )

    save_faiss_index(
        index,
        faiss_file
    )

    print("FAISS index saved successfully!")

print("Vectors stored:", index.ntotal)

query = input("\nAsk a question: ")

results = search_faiss(
    query,
    chunks,
    index,
    top_k=3
)

print("\nTop matching chunks:")

for rank, result in enumerate(results, start=1):
    print(f"\nRank {rank}")
    print("Score:", round(result["score"], 4))
    print("Chunk:", result["chunk"])