from ingest import load_faq_data
documents = load_faq_data()

documents[10]

documents_llm = []

for doc in documents:
    if doc["course"] == "llm-zoomcamp":
        documents_llm.append(doc)

len(documents_llm)

documents = documents_llm

doc = documents[0]
print(doc["id"])
print(doc["question"])
print(doc["answer"])

from pydantic import BaseModel

class Questions(BaseModel):
    questions: list[str]

data_gen_instructions = """
You emulate a student who's taking our course.
Formulate 5 questions this student might ask based on a FAQ record. The record
should contain the answer to the questions, and the questions should be complete and not too short.
If possible, use as fewer words as possible from the record.

The output should resemble how people ask questions
on the internet. Not too formal, not too short, not too long.
""".strip()

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_client = OpenAI()

import json
user_prompt = json.dumps(doc)

user_prompt

messages = [
    {"role": "developer", "content": data_gen_instructions},
    {"role": "user", "content": user_prompt}
]

response = openai_client.responses.parse(
    model="gpt-5.4-mini",
    input=messages,
    text_format=Questions
)

response.output_parsed.questions

doc

from evaluation_utils import llm_structured

result, usage = llm_structured(
    openai_client,
    data_gen_instructions,
    user_prompt,
    Questions
)

print(result.questions)

usage

from evaluation_utils import calc_price

calc_price(usage)

records = []

for q in result.questions:
    records.append({
        "question": q,
        "document": doc["id"]
    })

records

import pandas as pd

pd.DataFrame(records)

from evaluation_utils import llm_structured_retry

def generate_ground_truth(doc):
    user_prompt = json.dumps(doc)

    out, usage = llm_structured_retry(
        openai_client,
        data_gen_instructions,
        user_prompt,
        Questions
    )

    results = []

    for q in out.questions:
        results.append({
            "question": q,
            "document": doc["id"]
        })

    return results, usage

generate_ground_truth(doc)

from tqdm.auto import tqdm

ground_truth = []
usages = []

for doc in tqdm(documents[:5]):
    records, usage = generate_ground_truth(doc)
    ground_truth.extend(records)
    usages.append(usage)

from concurrent.futures import ThreadPoolExecutor
from evaluation_utils import map_progress

with ThreadPoolExecutor(max_workers=6) as pool:
    results = map_progress(pool, documents, generate_ground_truth)

ground_truth = []
usages = []

for records, usage in results:
    ground_truth.extend(records)
    usages.append(usage)

len(ground_truth)

ground_truth[10]

from evaluation_utils import calc_price

total_cost = 0.0

for usage in usages:
    cost = calc_price(usage)
    total_cost = total_cost + cost["total_cost"]

total_cost

from evaluation_utils import calc_total_price

calc_total_price(usages)

df_ground_truth = pd.DataFrame(ground_truth)

df_ground_truth.to_csv("data/ground_truth.csv", index=False)

len(df_ground_truth)
