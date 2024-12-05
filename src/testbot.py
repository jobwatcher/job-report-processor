# TUTORIAL: a simple indexing pipeline and RAG chain

import os 

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore
from logger import app_logger
from colorama import Fore

logger = app_logger.getChild('testbot')
logger.info(Fore.YELLOW + "Starting testbot")

load_dotenv()
# Verify API key is available
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# INDEXING PART ---------------------
logger.info(Fore.GREEN + "Starting indexing phase..")
llm = ChatOpenAI(model="gpt-4o-mini")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# from tutorial. WE ARE USING REDIS -- SEE VECTOR_DB BRANCH OF INDEEDOPTIMIZER
# from langchain_core.vectorstores import InMemoryVectorStore
# vector_store = InMemoryVectorStore(embeddings)

REDIS_URL="redis://redis:6379"
config = RedisConfig(
    index_name="newsgroups",
    redis_url=REDIS_URL,
    # metadata_schema=[
    #     {"name": "category", "type": "tag"},
    # ],
)
vector_store = RedisVectorStore(embeddings, config=config)

import bs4
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict

# Load and chunk contents of the blog
# different loaders can be used here
loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("post-content", "post-title", "post-header")
        )
    ),
)
docs = loader.load()
logger.info(Fore.GREEN + f"Loaded {len(docs)} documents")
logger.info(Fore.GREEN + f"Total characters: {len(docs[0].page_content)}")
logger.info(Fore.GREEN + f"First 100 characters: {docs[0].page_content[:100]}")

# splitting the documents into chunks
# Our loaded document is over 42k characters which is too long to fit into the context window of many models. 
# Even for those models that could fit the full post in their context window, models can struggle to find information in very long inputs.
# This is the recommended text splitter for generic text use cases.
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True,)
all_splits = text_splitter.split_documents(docs)
logger.info(Fore.GREEN + f"Split into {len(all_splits)} chunks")

# Index chunks
document_ids = vector_store.add_documents(documents=all_splits)
logger.info(Fore.GREEN + f"Added {len(document_ids)} documents_ids")
logger.info(Fore.GREEN + f"Some Document IDs: {document_ids[:3]}")

# Define prompt for question-answering
prompt = hub.pull("rlm/rag-prompt")

# Define state for application
class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


# Define application steps (NODES)
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}


# Compile application into a single graph object - connecting the retrieval and generation steps into a single sequence
graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()

# example_messages = prompt.invoke(
#     {"context": "(context goes here)", "question": "(question goes here)"}
# ).to_messages()
# assert len(example_messages) == 1
# logger.info(Fore.GREEN + f"Example messages: {example_messages[0].content}")

response = graph.invoke({"question": "what was miller's paper about?"})
logger.info(Fore.GREEN + f"Context: {response['context']}")
logger.info(Fore.GREEN + f"Answer: {response['answer']}")

for step in graph.stream(
    {"question": "what was miller's paper about?"}, stream_mode="updates"
):
    print(f"{step}\n\n----------------\n")

