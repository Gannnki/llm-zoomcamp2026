import pandas as pd

df_ground_truth = pd.read_csv("data/ground_truth-new.csv")
ground_truth = df_ground_truth.to_dict(orient="records")

ground_truth[10]

from ingest import load_faq_data, build_index

documents = load_faq_data()

documents_llm = []

for doc in documents:
    if doc["course"] == "llm-zoomcamp":
        documents_llm.append(doc)

documents = documents_llm
index = build_index(documents)

doc_idx = {}

for doc in documents:
    doc_idx[doc["id"]] = doc

q = ground_truth[10]

doc_idx[q['document']]

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_client = OpenAI()

from evaluation_utils import RAGWithUsage

assistant = RAGWithUsage(
    index=index,
    llm_client=openai_client,
    course='llm-zoomcamp',
)

answer = assistant.rag(q['question'])

assistant.total_cost()

print(answer)

doc_id = q["document"]
original_doc = doc_idx[doc_id]
answer_orig = original_doc["answer"]

print(answer_orig)

rag_result = {
    "question": q['question'],
    "answer_llm": answer,
    "answer_orig": answer_orig,
    "document": doc_id,
}

print(rag_result)

def generate_rag_answer(rec):
    question = rec["question"]
    doc_id = rec["document"]
    original_doc = doc_idx[doc_id]

    answer_llm = assistant.rag(question)
    answer_orig = original_doc["answer"]

    result = {
        "question": question,
        "answer_llm": answer_llm,
        "answer_orig": answer_orig,
        "document": doc_id,
    }

    return result

record = generate_rag_answer(q)
print("Generated RAG answer for the record:")
print(record)

assistant.total_cost()

assistant.reset_usage()

assistant.total_cost()

from concurrent.futures import ThreadPoolExecutor
from evaluation_utils import map_progress

with ThreadPoolExecutor(max_workers=6) as pool:
    results = map_progress(pool, ground_truth, generate_rag_answer)

print("First 10 results:")
print(results[:10])

df_results = pd.DataFrame(results)

print(df_results.head())

assistant.total_cost()

df_results.to_csv("data/rag-answers-new.csv", index=False)
print("Results saved to data/rag-answers-new.csv")