# ============================================================
# IMPORTS
# ============================================================

import os
import json

import numpy as np
import faiss

from pypdf import PdfReader

from sentence_transformers import (
    SentenceTransformer,
    CrossEncoder,
)

from sklearn.metrics.pairwise import cosine_similarity

from google import genai

from app.config import GEMINI_API_KEY


# ============================================================
# MODELS
# ============================================================

# Embedding model
model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# Reranking model
reranker_model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# Gemini client
gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# BASIC TEXT FUNCTIONS
# ============================================================

def load_text_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    return text


def clean_text(text):
    text = text.strip()

    while "\n\n" in text:
        text = text.replace("\n\n", "\n")

    return text


def chunk_text(text, chunk_size=100):
    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]

        chunk = " ".join(chunk)

        chunks.append(chunk)

    return chunks


# ============================================================
# OLD KEYWORD SEARCH
# ============================================================

def search_chunks(query, chunks):
    query_words = query.lower().split()

    best_chunk = None
    best_score = 0

    for chunk in chunks:
        chunk_lower = chunk.lower()

        score = 0

        for word in query_words:
            if word in chunk_lower:
                score += 1

        if score > best_score:
            best_score = score
            best_chunk = chunk

    return best_chunk, best_score


# ============================================================
# SEMANTIC SEARCH
# ============================================================

def semantic_search(query, chunks):
    chunk_embeddings = model.encode(chunks)

    query_embedding = model.encode([query])

    similarities = cosine_similarity(
        query_embedding,
        chunk_embeddings,
    )[0]

    best_index = similarities.argmax()

    best_chunk = chunks[best_index]
    best_score = similarities[best_index]

    return best_chunk, best_score


def semantic_search_top_k(
    query,
    chunks,
    top_k=3,
):
    chunk_embeddings = model.encode(chunks)

    query_embedding = model.encode([query])

    similarities = cosine_similarity(
        query_embedding,
        chunk_embeddings,
    )[0]

    ranked_indices = similarities.argsort()[::-1]

    results = []

    for index in ranked_indices[:top_k]:
        results.append({
            "chunk": chunks[index],
            "score": float(similarities[index]),
        })

    return results


# ============================================================
# EMBEDDING STORAGE
# ============================================================

def create_embeddings(chunks):
    embeddings = model.encode(chunks)

    return embeddings


def save_embeddings(
    embeddings,
    file_path,
):
    np.save(
        file_path,
        embeddings,
    )


def load_embeddings(file_path):
    embeddings = np.load(file_path)

    return embeddings


def search_saved_embeddings(
    query,
    chunks,
    chunk_embeddings,
    top_k=3,
):
    query_embedding = model.encode([query])

    similarities = cosine_similarity(
        query_embedding,
        chunk_embeddings,
    )[0]

    ranked_indices = similarities.argsort()[::-1]

    results = []

    for index in ranked_indices[:top_k]:
        results.append({
            "chunk": chunks[index],
            "score": float(similarities[index]),
        })

    return results


# ============================================================
# FAISS
# ============================================================

def create_faiss_index(embeddings):
    embeddings = embeddings.astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    faiss.normalize_L2(embeddings)

    index.add(embeddings)

    return index


def search_faiss(
    query,
    chunks,
    index,
    top_k=3,
):
    query_embedding = model.encode(
        [query]
    ).astype("float32")

    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(
        query_embedding,
        top_k,
    )

    results = []

    for score, index_id in zip(
        scores[0],
        indices[0],
    ):
        if index_id == -1:
            continue

        results.append({
            "chunk": chunks[index_id],
            "score": float(score),
        })

    return results


def save_faiss_index(
    index,
    file_path,
):
    faiss.write_index(
        index,
        file_path,
    )


def load_faiss_index(file_path):
    return faiss.read_index(file_path)


# ============================================================
# PDF LOADING
# ============================================================

def load_pdf(file_path):
    reader = PdfReader(file_path)

    pages = []

    source_name = os.path.basename(
        file_path
    )

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        text = page.extract_text()

        if text:
            pages.append({
                "page": page_number,
                "text": text,
                "source": source_name,
            })

    return pages


def load_all_pdfs(folder_path):
    all_pages = []

    if not os.path.exists(folder_path):
        return all_pages

    for file_name in sorted(
        os.listdir(folder_path)
    ):
        if not file_name.lower().endswith(".pdf"):
            continue

        file_path = os.path.join(
            folder_path,
            file_name,
        )

        print(
            "Loading PDF:",
            file_path,
        )

        pages = load_pdf(file_path)

        all_pages.extend(pages)

    return all_pages


# ============================================================
# PDF CHUNKING WITH OVERLAP
# ============================================================

def chunk_pdf_pages(
    pages,
    chunk_size=100,
    overlap=20,
):
    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative"
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks = []

    step_size = chunk_size - overlap

    for page_data in pages:
        page_number = page_data["page"]
        source = page_data["source"]

        text = clean_text(
            page_data["text"]
        )

        words = text.split()

        for i in range(
            0,
            len(words),
            step_size,
        ):
            chunk_words = words[
                i:i + chunk_size
            ]

            if not chunk_words:
                continue

            chunk_text_value = " ".join(
                chunk_words
            )

            chunks.append({
                "text": chunk_text_value,
                "page": page_number,
                "source": source,
            })

    return chunks


# ============================================================
# PDF EMBEDDINGS
# ============================================================

def create_pdf_embeddings(chunks):
    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = model.encode(texts)

    return embeddings


# ============================================================
# PDF FAISS SEARCH
# ============================================================

def search_pdf_faiss(
    query,
    chunks,
    index,
    top_k=3,
    threshold=0.25,
):
    query_embedding = model.encode(
        [query]
    ).astype("float32")

    faiss.normalize_L2(
        query_embedding
    )

    search_k = min(
        top_k,
        index.ntotal,
    )

    if search_k == 0:
        return []

    scores, indices = index.search(
        query_embedding,
        search_k,
    )

    results = []

    for score, index_id in zip(
        scores[0],
        indices[0],
    ):
        if index_id == -1:
            continue

        if float(score) < threshold:
            continue

        chunk = chunks[index_id]

        results.append({
            "text": chunk["text"],
            "page": chunk["page"],
            "source": chunk["source"],
            "score": float(score),
        })

    return results


# ============================================================
# METADATA STORAGE
# ============================================================

def save_metadata(
    chunks,
    file_path,
):
    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            chunks,
            file,
            ensure_ascii=False,
            indent=2,
        )


def load_metadata(file_path):
    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# KEYWORD SCORING
# ============================================================

def keyword_score(
    query,
    text,
):
    query_words = query.lower().split()

    if not query_words:
        return 0.0

    text_lower = text.lower()

    matched_words = 0

    for word in query_words:
        if word in text_lower:
            matched_words += 1

    return matched_words / len(
        query_words
    )


# ============================================================
# HYBRID SEARCH
# ============================================================

def hybrid_search(
    query,
    chunks,
    index,
    top_k=3,
    semantic_weight=0.7,
    keyword_weight=0.3,
    threshold=0.20,
):
    if not chunks:
        return []

    if index.ntotal == 0:
        return []

    query_embedding = model.encode(
        [query]
    ).astype("float32")

    faiss.normalize_L2(
        query_embedding
    )

    # Retrieve more candidates than the final
    # number required so reranking has options.
    candidate_count = min(
        len(chunks),
        index.ntotal,
        top_k * 5,
    )

    semantic_scores, indices = index.search(
        query_embedding,
        candidate_count,
    )

    combined_results = []

    for semantic_score, index_id in zip(
        semantic_scores[0],
        indices[0],
    ):
        if index_id == -1:
            continue

        chunk = chunks[index_id]

        keyword = keyword_score(
            query,
            chunk["text"],
        )

        combined_score = (
            semantic_weight
            * float(semantic_score)
            +
            keyword_weight
            * float(keyword)
        )

        if combined_score < threshold:
            continue

        combined_results.append({
            "text": chunk["text"],
            "page": chunk["page"],
            "source": chunk["source"],
            "semantic_score": float(
                semantic_score
            ),
            "keyword_score": float(
                keyword
            ),
            "score": float(
                combined_score
            ),
        })

    combined_results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return combined_results[:top_k]


# ============================================================
# RERANKING
# ============================================================

def rerank_results(
    query,
    results,
    top_k=3,
):
    if not results:
        return []

    pairs = []

    for result in results:
        pairs.append([
            query,
            result["text"],
        ])

    rerank_scores = reranker_model.predict(
        pairs
    )

    reranked_results = []

    for result, rerank_score in zip(
        results,
        rerank_scores,
    ):
        updated_result = result.copy()

        updated_result[
            "rerank_score"
        ] = float(rerank_score)

        reranked_results.append(
            updated_result
        )

    reranked_results.sort(
        key=lambda item: item[
            "rerank_score"
        ],
        reverse=True,
    )

    return reranked_results[:top_k]


# ============================================================
# GEMINI RAG GENERATION
# ============================================================

def generate_rag_answer(
    query,
    results,
    conversation_history=None,
):
    if not results:
        return (
            "I could not find this information "
            "in the provided documents."
        )

    if conversation_history is None:
        conversation_history = []

    context_parts = []

    for result in results:
        context_parts.append(
            f"""
Source: {result["source"]}
Page: {result["page"]}
Content:
{result["text"]}
"""
        )

    context = "\n".join(context_parts)

    history_parts = []

    for message in conversation_history[-6:]:
        role = message["role"]
        content = message["content"]

        history_parts.append(
            f"{role}: {content}"
        )

    history_text = "\n".join(history_parts)

    prompt = f"""
You are an enterprise document assistant.

Answer the user's question using ONLY
the supplied document context.

You may use the conversation history only
to understand references such as:
"it", "that", "this", "they", or follow-up questions.

Do NOT use conversation history as a source
of factual information unless that information
came from the provided documents.

Rules:

1. Use only information contained in the document context.
2. Do not use outside knowledge.
3. Do not invent information.
4. If the answer cannot be found in the context, say:
   "I could not find this information in the provided documents."
5. Include the source filename and page number.
6. Use conversation history to understand follow-up questions.

Conversation History:

{history_text}

Document Context:

{context}

Current User Question:

{query}
"""

    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    if not response.text:
        return (
            "I could not generate an answer "
            "from the provided documents."
        )

    return response.text