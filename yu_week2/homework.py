from embedder import Embedder
import numpy as np

embed = Embedder()

# Q1 : Embed a query
q1 = "How does approximate nearest neighbor search work?"
v1 = embed.encode(q1)
print(v1[0])

# Q2 similarity

from gitsource import GithubRepositoryDataReader

reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id="8c1834d",
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)

documents = [file.parse() for file in reader.read()]
print(len(documents))

for i in documents:
    if i['filename'] == '02-vector-search/lessons/07-sqlitesearch-vector.md':
        print('Found it!')
        v_doc = embed.encode(i['content'])
        similarity = np.dot(v_doc, v1)
        print(f"Similarity between query and document: {similarity}")

# Q3 : Chunking and searching
from gitsource import chunk_documents
chunks = chunk_documents(documents, size=2000, step=1000)

chunk_texts = [chunk["content"] for chunk in chunks]
X = embed.encode_batch(chunk_texts)

scores = X.dot(v1)
best_idx = scores.argmax()
best_chunk = chunks[best_idx]

print(scores[best_idx])
print(best_chunk["filename"])

# Q4 Vector search with minsearch 
q2 = 'What metric do we use to evaluate a search engine?'
v2 = embed.encode(q2)

from minsearch import VectorSearch, Index

# Build vector index over the chunks
vindex = VectorSearch(keyword_fields=["filename"])
vindex.fit(X, chunks)

results = vindex.search(v2, num_results=5)
print(results[0]["filename"])

# Q5 Text search vs vector search
q3 = 'How do I store vectors in PostgreSQL?'

v3 = embed.encode(q3)
vector_results = vindex.search(v3, num_results=5)

# Text search building an index over the chunks
text_index = Index(
    text_fields=["content"],
    keyword_fields=["filename"],
)
text_index.fit(chunks)
text_results = text_index.search(q3, num_results=5)

# Extract filenames from results
vector_files = [result["filename"] for result in vector_results]
text_files = [result["filename"] for result in text_results]

print("Vector results:")
for filename in vector_files:
    print(filename)

print("\nText results:")
for filename in text_files:
    print(filename)

print("\nIn vector but not text:")
for filename in vector_files:
    if filename not in text_files:
        print(filename)


# Q6 hybrid search
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

q4 = 'How do I give the model access to tools?'

v4 = embed.encode(q4)
vector_results = vindex.search(v4, num_results=5)

# Text search building an index over the chunks
text_index = Index(
    text_fields=["content"],
    keyword_fields=["filename"],
)
text_index.fit(chunks)
text_results = text_index.search(q4, num_results=5)

hybrid_results = rrf([vector_results, text_results])

print("\nHybrid results:")
for result in hybrid_results:
    print(result["filename"], result["start"])

print("\nQ6 answer:")
print(hybrid_results[0]["filename"])