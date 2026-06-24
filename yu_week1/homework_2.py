from gitsource import GithubRepositoryDataReader
from dotenv import load_dotenv
load_dotenv()

reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id="8c1834d",
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)

files = reader.read()

documents = []

for file in files:
    doc = file.parse()
    documents.append(doc)

print(len(documents))

from ingest import load_faq_data, build_index

from rag_helper import RAGBase
from openai import OpenAI

index = build_index(documents)

openai_client = OpenAI()

assistant = RAGBase(
    index=index,
    llm_client=openai_client,
)

answer = assistant.rag("How does the agentic loop keep calling the model until it stops?")
print(answer)



