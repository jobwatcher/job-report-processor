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


# Conversational Part ----------------------------
# CHAINS 

# represent the state of our RAG application using a sequence of messages. Specifically, we will have

# User input as a HumanMessage;
# Vector store query as an AIMessage with tool calls;
# Retrieved documents as a ToolMessage;
# Final response as a AIMessage.

from langgraph.graph import END
from langgraph.graph import MessagesState
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode, tools_condition

graph_builder = StateGraph(MessagesState)

@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

# Step 1: Generate an AIMessage that may include a tool-call to be sent.
def query_or_respond(state: MessagesState):
    """Generate tool call for retrieval or respond."""
    llm_with_tools = llm.bind_tools([retrieve])
    response = llm_with_tools.invoke(state["messages"])
    # MessagesState appends messages to state instead of overwriting
    return {"messages": [response]}


# Step 2: Execute the retrieval.
tools = ToolNode([retrieve])


# Step 3: Generate a response using the retrieved content.
def generate(state: MessagesState):
    """Generate answer."""
    # Get generated ToolMessages
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    # Format into prompt
    docs_content = "\n\n".join(doc.content for doc in tool_messages)
    system_message_content = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        f"{docs_content}"
    )
    conversation_messages = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and not message.tool_calls)
    ]
    prompt = [SystemMessage(system_message_content)] + conversation_messages

    # Run
    response = llm.invoke(prompt)
    return {"messages": [response]}

graph_builder.add_node(query_or_respond)
graph_builder.add_node(tools)
graph_builder.add_node(generate)

graph_builder.set_entry_point("query_or_respond")
graph_builder.add_conditional_edges(
    "query_or_respond",
    tools_condition,
    {END: END, "tools": "tools"},
)
graph_builder.add_edge("tools", "generate")
graph_builder.add_edge("generate", END)

graph = graph_builder.compile()

input_message = "What is Task Decomposition?"

for step in graph.stream(
    {"messages": [{"role": "user", "content": input_message}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()

# For persistence ----------------------------

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# Specify an ID for the thread
config = {"configurable": {"thread_id": "abc123"}}

input_message = "What is Task Decomposition?"

for step in graph.stream(
    {"messages": [{"role": "user", "content": input_message}]},
    stream_mode="values",
    config=config,
):
    step["messages"][-1].pretty_print()

input_message = "Can you look up some common ways of doing it?"

for step in graph.stream(
    {"messages": [{"role": "user", "content": input_message}]},
    stream_mode="values",
    config=config,
):
    step["messages"][-1].pretty_print()

# Agents
#  Agents leverage the reasoning capabilities of LLMs to make decisions during execution. 
# Using agents allows you to offload additional discretion over the retrieval process. 
# Although their behavior is less predictable than the above "chain", they are able to execute 
# multiple retrieval steps in service of a query, or iterate on a single search.

from langgraph.prebuilt import create_react_agent

agent_executor = create_react_agent(llm, [retrieve], checkpointer=memory)

config = {"configurable": {"thread_id": "def234"}}

input_message = (
    "What is the standard method for Task Decomposition?\n\n"
    "Once you get the answer, look up common extensions of that method."
)

for event in agent_executor.stream(
    {"messages": [{"role": "user", "content": input_message}]},
    stream_mode="values",
    config=config,
):
    event["messages"][-1].pretty_print()

# Note that the agent:

# Generates a query to search for a standard method for task decomposition;
# Receiving the answer, generates a second query to search for common extensions of it;
# Having received all necessary context, answers the question.