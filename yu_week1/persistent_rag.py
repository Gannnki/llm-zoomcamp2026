from sqlitesearch import TextSearchIndex
from rag_helper import RAGBase
from openai import OpenAI
from dotenv import load_dotenv

sqlite_index = TextSearchIndex(
    text_fields=["question", "section", "answer"],
    keyword_fields=["course"],
    db_path="faq.db"
)

print(sqlite_index.count())

load_dotenv()
openai_client = OpenAI()

assistant = RAGBase(
    index=sqlite_index,
    llm_client=openai_client,
)

answer = assistant.rag("Can I still join the course after it started?")
print(answer)