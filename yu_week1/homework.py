import json
from dataclasses import dataclass

from dotenv import load_dotenv
from gitsource import GithubRepositoryDataReader, chunk_documents
from minsearch import Index
from openai import OpenAI
from toyaikit.chat.runners import OpenAIResponsesRunner
from toyaikit.llm import OpenAIClient
from toyaikit.tools import Tools


MODEL = "gpt-5.4-mini"
QUESTION = "How does the agentic loop keep calling the model until it stops?"
AGENT_QUESTION = "How does the agentic loop work, and how is it different from plain RAG?"


INSTRUCTIONS = """
You're a course teaching assistant.
Answer the student's question using only the provided context.
If the context does not contain the answer, say "I don't know."
""".strip()

AGENT_INSTRUCTIONS = """
You're a course teaching assistant. Answer the student's question using the
search tool. Make multiple searches with different keywords before answering.
""".strip()

PROMPT_TEMPLATE = """
QUESTION: {question}

CONTEXT:
{context}
""".strip()


@dataclass
class RAGResult:
    answer: str
    input_tokens: int
    output_tokens: int


class LessonRAG:
    def __init__(self, index, llm_client, model=MODEL, num_results=5):
        self.index = index
        self.llm_client = llm_client
        self.model = model
        self.num_results = num_results

    def search(self, query):
        return self.index.search(query, num_results=self.num_results)

    def build_context(self, search_results):
        parts = []

        for doc in search_results:
            location = doc["filename"]
            if "start" in doc:
                location = f"{location}#start={doc['start']}"

            parts.append(
                f"FILE: {location}\n"
                f"CONTENT:\n{doc['content']}"
            )

        return "\n\n---\n\n".join(parts)

    def build_prompt(self, query, search_results):
        context = self.build_context(search_results)
        return PROMPT_TEMPLATE.format(question=query, context=context)

    def llm(self, prompt):
        return self.llm_client.responses.create(
            model=self.model,
            input=[
                {"role": "developer", "content": INSTRUCTIONS},
                {"role": "user", "content": prompt},
            ],
        )

    def rag(self, query):
        search_results = self.search(query)
        prompt = self.build_prompt(query, search_results)
        response = self.llm(prompt)
        usage = response.usage

        return RAGResult(
            answer=response.output_text,
            input_tokens=getattr(usage, "input_tokens", 0),
            output_tokens=getattr(usage, "output_tokens", 0),
        )


def load_lesson_documents():
    reader = GithubRepositoryDataReader(
        repo_owner="DataTalksClub",
        repo_name="llm-zoomcamp",
        commit_id="8c1834d",
        allowed_extensions={"md"},
        filename_filter=lambda path: "/lessons/" in path,
    )

    files = reader.read()
    return [file.parse() for file in files]


def build_index(documents):
    index = Index(
        text_fields=["content"],
        keyword_fields=["filename"],
    )
    index.fit(documents)
    return index


def count_search_calls(messages):
    return sum(
        1
        for message in messages
        if getattr(message, "type", None) == "function_call"
        and getattr(message, "name", None) == "search"
    )


def main():
    load_dotenv()

    documents = load_lesson_documents()

    print("Q1 lesson pages:", len(documents))

    lesson_index = build_index(documents)
    search_results = lesson_index.search(QUESTION, num_results=5)
    print("Q2 first result:", search_results[0]["filename"])

    openai_client = OpenAI()
    page_rag = LessonRAG(index=lesson_index, llm_client=openai_client)
    page_result = page_rag.rag(QUESTION)
    print("Q3 answer:", page_result.answer)
    print("Q3 input tokens:", page_result.input_tokens)

    chunks = chunk_documents(documents, size=2000, step=1000)
    print("Q4 chunks:", len(chunks))

    chunk_index = build_index(chunks)
    chunk_rag = LessonRAG(index=chunk_index, llm_client=openai_client)
    chunk_result = chunk_rag.rag(QUESTION)
    print("Q5 answer:", chunk_result.answer)
    print("Q5 input tokens:", chunk_result.input_tokens)
    print("Q5 fewer input tokens:", page_result.input_tokens - chunk_result.input_tokens)

    def search(query: str) -> list[dict]:
        """
        Search the LLM Zoomcamp lesson chunks for content matching the query.
        """
        results = chunk_index.search(query, num_results=5)
        cleaned = []

        for doc in results:
            cleaned.append(
                {
                    "filename": doc["filename"],
                    "start": doc.get("start", 0),
                    "content": doc["content"],
                }
            )

        return cleaned

    agent_tools = Tools()
    agent_tools.add_tool(search)

    runner = OpenAIResponsesRunner(
        tools=agent_tools,
        developer_prompt=AGENT_INSTRUCTIONS,
        llm_client=OpenAIClient(model=MODEL),
    )

    agent_result = runner.loop(prompt=AGENT_QUESTION)
    search_call_count = count_search_calls(agent_result.all_messages)

    print("Q6 answer:", agent_result.last_message)
    print("Q6 search calls:", search_call_count)
    print("Q6 token usage:", agent_result.tokens)

    answers = {
        "q1_lesson_pages": len(documents),
        "q2_first_result": search_results[0]["filename"],
        "q3_input_tokens": page_result.input_tokens,
        "q4_chunks": len(chunks),
        "q5_input_tokens": chunk_result.input_tokens,
        "q5_fewer_input_tokens": page_result.input_tokens - chunk_result.input_tokens,
        "q6_search_calls": search_call_count,
    }

    print("\nSummary")
    print(json.dumps(answers, indent=2))


if __name__ == "__main__":
    main()
