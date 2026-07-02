import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import frontmatter
import requests
from dotenv import load_dotenv
from gitsource import GithubRepositoryDataReader, chunk_documents
from minsearch import Index, VectorSearch
from pydantic import BaseModel

from evaluation_utils import llm_structured_retry


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO_ROOT))

from yu_week2.embedder import Embedder

GROUND_TRUTH_PATH = REPO_ROOT / "cohorts/2026/04-evaluation/ground-truth.csv"

LESSON_FILENAMES_FOR_Q1 = [
    "01-agentic-rag/lessons/01-intro.md",
    "01-agentic-rag/lessons/02-environment.md",
    "01-agentic-rag/lessons/03-rag.md",
]


class Questions(BaseModel):
    questions: list[str]


data_gen_instructions = """
You emulate a student who is taking our LLM course.
You are given one lesson page from the course.
Formulate 5 questions this student might ask that are answered by this page.

Rules:
- The page should contain the answer to each question.
- Make the questions complete and not too short.
- Use as few words as possible from the page; don't copy its phrasing.
- The questions should resemble how people actually ask things online:
  not too formal, not too short, not too long.
- Ask about the content of the lesson, not about its formatting or filename.
""".strip()


def load_documents():
    reader = GithubRepositoryDataReader(
        repo_owner="DataTalksClub",
        repo_name="llm-zoomcamp",
        commit_id="8c1834d",
        allowed_extensions={"md"},
        filename_filter=lambda path: "/lessons/" in path,
    )

    try:
        return [file.parse() for file in reader.read()]
    except requests.exceptions.RequestException:
        return load_documents_from_git_commit()


def load_documents_from_git_commit(commit_id="8c1834d"):
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", commit_id],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    documents = []
    filenames = [
        filename
        for filename in result.stdout.splitlines()
        if "/lessons/" in filename and filename.endswith(".md")
    ]

    for filename in filenames:
        content_result = subprocess.run(
            ["git", "show", f"{commit_id}:{filename}"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        content = content_result.stdout.strip()
        post = frontmatter.loads(content)
        data = post.to_dict()
        data["filename"] = filename
        documents.append(data)

    return documents


def generate_questions_for_doc(openai_client, doc):
    user_prompt = json.dumps(
        {
            "filename": doc["filename"],
            "content": doc["content"],
        }
    )

    result, usage = llm_structured_retry(
        openai_client,
        data_gen_instructions,
        user_prompt,
        Questions,
    )

    records = [
        {
            "question": question,
            "filename": doc["filename"],
        }
        for question in result.questions
    ]
    return records, usage


def token_count(usage):
    if hasattr(usage, "input_tokens"):
        return usage.input_tokens
    return usage.prompt_tokens


def run_q1(documents):
    load_dotenv()

    if os.getenv("RUN_Q1") != "1":
        print("Q1: skipped - set RUN_Q1=1 to generate questions with the LLM")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("Q1: skipped - OPENAI_API_KEY is not set")
        return

    from openai import OpenAI

    openai_client = OpenAI()
    docs_by_filename = {doc["filename"]: doc for doc in documents}

    usages = []
    generated_records = []

    for filename in LESSON_FILENAMES_FOR_Q1:
        records, usage = generate_questions_for_doc(
            openai_client,
            docs_by_filename[filename],
        )
        generated_records.extend(records)
        usages.append(usage)

    average_input_tokens = sum(token_count(usage) for usage in usages) / len(usages)

    print("Q1 generated records:", len(generated_records))
    print("Q1 input tokens:", [token_count(usage) for usage in usages])
    print("Q1 average input tokens:", average_input_tokens)


def build_text_index(chunks):
    index = Index(
        text_fields=["content"],
        keyword_fields=["filename"],
    )
    index.fit(chunks)
    return index


def build_vector_index(chunks):
    embedder = Embedder(path=REPO_ROOT / "models/Xenova/all-MiniLM-L6-v2")
    chunk_texts = [chunk["content"] for chunk in chunks]
    chunk_vectors = embedder.encode_batch(chunk_texts)

    index = VectorSearch(keyword_fields=["filename"])
    index.fit(chunk_vectors, chunks)

    return index, embedder


def rrf(result_lists, k=60, num_results=5):
    scores = {}
    docs = {}

    for results in result_lists:
        for rank, doc in enumerate(results):
            key = (doc["filename"], doc["start"])
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            docs[key] = doc

    ranked = sorted(scores, key=scores.get, reverse=True)
    return [docs[key] for key in ranked[:num_results]]


def compute_relevance(record, search_function):
    expected_filename = record["filename"]
    results = search_function(query=record["question"])
    return [int(result["filename"] == expected_filename) for result in results]


def hit_rate(relevance_total):
    return sum(1 for relevance in relevance_total if 1 in relevance) / len(relevance_total)


def mrr(relevance_total):
    total_score = 0.0

    for relevance in relevance_total:
        for rank, value in enumerate(relevance):
            if value == 1:
                total_score += 1 / (rank + 1)
                break

    return total_score / len(relevance_total)


def evaluate(ground_truth, search_function):
    relevance_total = [
        compute_relevance(record, search_function)
        for record in ground_truth
    ]

    return {
        "hit_rate": hit_rate(relevance_total),
        "mrr": mrr(relevance_total),
    }


def main():
    documents = load_documents()
    print("Documents:", len(documents))

    run_q1(documents)

    df_ground_truth = pd.read_csv(GROUND_TRUTH_PATH)
    ground_truth = df_ground_truth.to_dict(orient="records")
    print("Ground truth records:", len(ground_truth))

    chunks = chunk_documents(documents, size=2000, step=1000)
    print("Chunks:", len(chunks))

    text_index = build_text_index(chunks)
    vector_index, embedder = build_vector_index(chunks)

    def text_search(query, num_results=5):
        return text_index.search(query, num_results=num_results)

    def vector_search(query, num_results=5):
        query_vector = embedder.encode(query)
        return vector_index.search(query_vector, num_results=num_results)

    def hybrid_search(query, k=60):
        text_results = text_search(query, num_results=10)
        vector_results = vector_search(query, num_results=10)
        return rrf([text_results, vector_results], k=k)

    first_question = ground_truth[0]["question"]

    q2_result = text_search(first_question)[0]
    print("Q2 first text result:", q2_result["filename"])

    q3_result = vector_search(first_question)[0]
    print("Q3 first vector result:", q3_result["filename"])

    text_metrics = evaluate(ground_truth, text_search)
    print("Q4 text search metrics:", text_metrics)

    vector_metrics = evaluate(ground_truth, vector_search)
    print("Q5 vector search metrics:", vector_metrics)

    hybrid_results = []
    for k in [1, 50, 100, 200]:
        metrics = evaluate(
            ground_truth,
            lambda query, k=k: hybrid_search(query=query, k=k),
        )
        hybrid_results.append((k, metrics))
        print(f"Q6 hybrid search metrics for k={k}:", metrics)

    best_k, best_metrics = max(
        hybrid_results,
        key=lambda item: (item[1]["mrr"], -item[0]),
    )
    print("Q6 best k:", best_k)
    print("Q6 best metrics:", best_metrics)


if __name__ == "__main__":
    main()
