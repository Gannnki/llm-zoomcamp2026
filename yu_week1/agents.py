

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_client = OpenAI()

def search(query):
    boost_dict = {"question": 3.0, "section": 0.5}
    filter_dict = {"course": "llm-zoomcamp"}

    return index.search(
        query,
        num_results=5,
        boost_dict=boost_dict,
        filter_dict=filter_dict
    )

response = openai_client.responses.create(
    model="gpt-5.4-mini",
    input=messages,
    tools=[search_tool],
)

response.output