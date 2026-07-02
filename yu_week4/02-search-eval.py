import pandas as pd

df_ground_truth = pd.read_csv("data/ground_truth-new.csv") #-data.csv")

print(df_ground_truth.head())

ground_truth = df_ground_truth.to_dict(orient="records")

print(ground_truth[10])

from ingest import load_faq_data, build_index

documents = load_faq_data()

documents_llm = []

for doc in documents:
    if doc["course"] == "llm-zoomcamp":
        documents_llm.append(doc)

documents = documents_llm
index = build_index(documents)

boost = {'question': 3.0}

index.search(
    "What is the course about?",
    num_results=5,
    boost_dict=boost
)

def text_search(query):
    boost_dict = {"question": 3.0, "section": 0.5}

    return index.search(
        query,
        num_results=5,
        boost_dict=boost_dict
    )

q = ground_truth[0]
q

doc_id = q['document']
doc_id

results = text_search(q['question'])
results

for d in results:
    print(f'{d["id"]} == {doc_id}: {d["id"] == doc_id}')

relevance = []

for d in results:
    relevance.append(int(d["id"] == doc_id))

print(relevance)

def compute_relevance_text(q):
    doc_id = q["document"]
    results = text_search(query=q["question"])

    relevance = []
    for d in results:
        relevance.append(int(d["id"] == doc_id))

    return relevance

q = ground_truth[0]
print(q["question"])
compute_relevance_text(q)
# [1, 0, 0, 0, 0]

q = ground_truth[11]
print(q["question"])
print(compute_relevance_text(q))
# [0, 0, 1, 0, 0]

[0, 0, 1, 0, 0]

q = ground_truth[50]
print(q["question"])
print(compute_relevance_text(q))
# [0, 0, 0, 0, 0]

[0, 0, 0, 0, 0]

from tqdm.auto import tqdm

def compute_relevance_total_text(ground_truth):
    relevance_total = []

    for q in tqdm(ground_truth):
        relevance = compute_relevance_text(q)
        relevance_total.append(relevance)

    return relevance_total

relevance = compute_relevance_total_text(ground_truth)

print(relevance[:15])

def compute_relevance(q, search_function):
    doc_id = q["document"]
    results = search_function(query=q["question"])

    relevance = []
    for d in results:
        relevance.append(int(d["id"] == doc_id))

    return relevance

def compute_relevance_total(ground_truth, search_function):
    relevance_total = []

    for q in tqdm(ground_truth):
        relevance = compute_relevance(q, search_function)
        relevance_total.append(relevance)

    return relevance_total

relevance_total = compute_relevance_total(ground_truth, text_search)

sample = relevance_total[:15]

print(sample)

cnt = 0

for line in sample:
    if 1 in line:
        cnt = cnt + 1

print(cnt / len(sample))

def hit_rate(relevance):
    cnt = 0

    for line in relevance:
        if 1 in line:
            cnt = cnt + 1

    return cnt / len(relevance)

print(hit_rate(relevance))

total_score = 0.0

for line in sample:
    for rank in range(len(line)):
        if line[rank] == 1:
            score = 1 / (rank + 1)
            total_score = total_score + score
            break

print(total_score / len(sample))

def mrr(relevance):
    total_score = 0.0

    for line in relevance:
        for rank in range(len(line)):
            if line[rank] == 1:
                score = 1 / (rank + 1)
                total_score = total_score + score
                break

    return total_score / len(relevance)

print(mrr(sample))

print(mrr(relevance))

def evaluate(ground_truth, search_function):
    relevance_total = compute_relevance_total(ground_truth, search_function)

    return {
        "hit_rate": hit_rate(relevance_total),
        "mrr": mrr(relevance_total),
    }

print(evaluate(ground_truth, text_search))

def text_search_v2(query):
    boost_dict = {"question": 2.0, "section": 0.5}

    return index.search(
        query,
        num_results=5,
        boost_dict=boost_dict
    )

print(evaluate(ground_truth, text_search_v2))

def search_boost(query, question_boost):
    boost_dict = {"question": question_boost, "section": 0.5}

    return index.search(
        query,
        num_results=5,
        boost_dict=boost_dict,
    )

for boost in [0.5, 1.0, 3.0, 5.0, 10.0]:
    result = evaluate(
        ground_truth,
        lambda query, boost=boost: search_boost(query, boost)
    )
    print(f"boost={boost}: {result}")

def search_boosts(query, question_boost, answer_boost, section_boost):
    boost_dict = {
        "question": question_boost,
        "section": section_boost,
        "answer": answer_boost,
    }

    return index.search(
        query,
        num_results=5,
        boost_dict=boost_dict,
    )

results = []

for question_boost in [1.0, 2.0, 5.0]:
    for answer_boost in [1.0, 2.0, 4.0, 10.0]:
        for section_boost in [0.1, 0.2, 0.5]:
            print(f"Evaluating question_boost={question_boost}, answer_boost={answer_boost}, section_boost={section_boost}...")
            result = evaluate(
                ground_truth,
                lambda query, question_boost=question_boost, answer_boost=answer_boost, section_boost=section_boost: search_boosts(
                    query,
                    question_boost,
                    answer_boost,
                    section_boost
                )
            )

            results.append({
                "question": question_boost,
                "answer": answer_boost,
                "section": section_boost,
                "hit_rate": result["hit_rate"],
                "mrr": result["mrr"],
            })

df_results = pd.DataFrame(results)
df_results.sort_values("mrr", ascending=False).head(10)
