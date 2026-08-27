import json

from utils import (
    load_faiss_index,
    load_metadata,
    hybrid_search,
    rerank_results,
)


FAISS_FILE = "data/multi_document.index"
METADATA_FILE = "data/multi_document_metadata.json"
TEST_FILE = "tests/rag_test_questions.json"


# ============================================================
# LOAD KNOWLEDGE BASE
# ============================================================

index = load_faiss_index(
    FAISS_FILE
)

chunks = load_metadata(
    METADATA_FILE
)


# ============================================================
# LOAD TEST QUESTIONS
# ============================================================

with open(
    TEST_FILE,
    "r",
    encoding="utf-8",
) as file:
    test_questions = json.load(file)


total_tests = len(test_questions)

passed_tests = 0


print("\nRAG EVALUATION")
print("=" * 50)


# ============================================================
# RUN TESTS
# ============================================================

for number, test in enumerate(
    test_questions,
    start=1,
):
    question = test["question"]

    expected_source = test[
        "expected_source"
    ]

    expected_keyword = test[
        "expected_keyword"
    ]

    results = hybrid_search(
        question,
        chunks,
        index,
        top_k=10,
        semantic_weight=0.7,
        keyword_weight=0.3,
        threshold=0.20,
    )

    results = rerank_results(
        question,
        results,
        top_k=3,
    )


    print(
        f"\nTest {number}:",
        question,
    )


    # ========================================================
    # TEST FOR UNANSWERABLE QUESTION
    # ========================================================

    if expected_source is None:

        if not results:
            print("PASS ✅")
            passed_tests += 1

        else:
            print("FAIL ❌")
            print(
                "Unexpected retrieval:",
                results[0]["source"],
            )

        continue


    # ========================================================
    # TEST RETRIEVAL
    # ========================================================

    if not results:
        print("FAIL ❌")
        print("No results returned.")
        continue


    best_result = results[0]

    retrieved_source = best_result[
        "source"
    ]

    retrieved_text = best_result[
        "text"
    ].lower()


    source_correct = (
        retrieved_source
        == expected_source
    )

    keyword_correct = (
        expected_keyword.lower()
        in retrieved_text
    )


    if (
        source_correct
        and keyword_correct
    ):
        print("PASS ✅")
        passed_tests += 1

    else:
        print("FAIL ❌")


    print(
        "Expected source:",
        expected_source,
    )

    print(
        "Retrieved source:",
        retrieved_source,
    )

    print(
        "Expected keyword:",
        expected_keyword,
    )

    print(
        "Rerank score:",
        round(
            best_result[
                "rerank_score"
            ],
            4,
        ),
    )


# ============================================================
# FINAL SCORE
# ============================================================

accuracy = (
    passed_tests
    / total_tests
) * 100


print("\n" + "=" * 50)

print(
    "Passed:",
    f"{passed_tests}/{total_tests}",
)

print(
    "Retrieval Accuracy:",
    f"{accuracy:.2f}%",
)