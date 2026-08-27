import os

from utils import (
    load_all_pdfs,
    chunk_pdf_pages,
    create_pdf_embeddings,
    create_faiss_index,
    save_faiss_index,
    load_faiss_index,
    save_metadata,
    load_metadata,
    hybrid_search,
    rerank_results,
    generate_rag_answer,
)


# ============================================================
# FILE PATHS
# ============================================================

documents_folder = "data/documents"

faiss_file = "data/multi_document.index"

metadata_file = "data/multi_document_metadata.json"


# ============================================================
# LOAD OR CREATE KNOWLEDGE BASE
# ============================================================

if (
    os.path.exists(faiss_file)
    and os.path.exists(metadata_file)
):
    print(
        "Loading existing multi-document index..."
    )

    index = load_faiss_index(
        faiss_file
    )

    chunks = load_metadata(
        metadata_file
    )

else:
    print(
        "Creating multi-document index..."
    )

    pages = load_all_pdfs(
        documents_folder
    )

    if not pages:
        print(
            "No PDF documents found."
        )
        raise SystemExit

    chunks = chunk_pdf_pages(
        pages,
        chunk_size=50,
        overlap=10,
    )

    embeddings = create_pdf_embeddings(
        chunks
    )

    index = create_faiss_index(
        embeddings
    )

    save_faiss_index(
        index,
        faiss_file
    )

    save_metadata(
        chunks,
        metadata_file
    )

    print(
        "Multi-document index saved successfully!"
    )


# ============================================================
# VERIFY INDEX
# ============================================================

print(
    "PDF chunks:",
    len(chunks),
)

print(
    "Vectors stored:",
    index.ntotal,
)


if index.ntotal != len(chunks):
    raise RuntimeError(
        "FAISS index and metadata do not match. "
        "Delete the saved index and metadata, "
        "then rebuild them."
    )


# ============================================================
# CONVERSATION MEMORY
# ============================================================

conversation_history = []


print("\nEnterprise RAG Assistant is ready.")
print("Type 'exit' to stop.")


# ============================================================
# CONVERSATION LOOP
# ============================================================

while True:

    query = input(
        "\nYou: "
    ).strip()


    # --------------------------------------------------------
    # EXIT COMMAND
    # --------------------------------------------------------

    if query.lower() in {
        "exit",
        "quit",
        "bye",
    }:
        print(
            "\nAI: Goodbye!"
        )
        break


    # --------------------------------------------------------
    # EMPTY QUESTION
    # --------------------------------------------------------

    if not query:
        print(
            "\nPlease enter a question."
        )
        continue


    # ========================================================
    # STAGE 1 — HYBRID RETRIEVAL
    # ========================================================

    results = hybrid_search(
        query,
        chunks,
        index,
        top_k=10,
        semantic_weight=0.7,
        keyword_weight=0.3,
        threshold=0.20,
    )


    # ========================================================
    # STAGE 2 — RERANKING
    # ========================================================

    results = rerank_results(
        query,
        results,
        top_k=3,
    )


    # ========================================================
    # STAGE 3 — GENERATION
    # ========================================================

    if not results:

        answer = (
            "I could not find this information "
            "in the provided documents."
        )

    else:

        answer = generate_rag_answer(
            query,
            results,
            conversation_history,
        )


    # ========================================================
    # FINAL ANSWER
    # ========================================================

    print("\nAI:")
    print(answer)


    # ========================================================
    # SAVE CONVERSATION MEMORY
    # ========================================================

    conversation_history.append({
        "role": "User",
        "content": query,
    })

    conversation_history.append({
        "role": "Assistant",
        "content": answer,
    })


    # Keep only recent messages
    conversation_history = conversation_history[-12:]


    # ========================================================
    # DEBUG / RETRIEVAL RESULTS
    # ========================================================

    print("\nTop results:")


    for rank, result in enumerate(
        results,
        start=1,
    ):

        print(f"\nRank {rank}")

        print(
            "Hybrid score:",
            round(
                result["score"],
                4,
            ),
        )

        print(
            "Semantic score:",
            round(
                result["semantic_score"],
                4,
            ),
        )

        print(
            "Keyword score:",
            round(
                result["keyword_score"],
                4,
            ),
        )

        print(
            "Rerank score:",
            round(
                result["rerank_score"],
                4,
            ),
        )

        print(
            "Source:",
            result["source"],
        )

        print(
            "Page:",
            result["page"],
        )

        print(
            "Text:",
            result["text"],
        )