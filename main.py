from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import json
import os
import tempfile
from bs4 import BeautifulSoup
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.vectorstores import VectorStoreRetriever
from typing import List, Optional
load_dotenv()

mcp = FastMCP("docs")

USER_AGENT = "docs-app/1.0"
SERPER_URL="https://google.serper.dev/search"

docs_urls = {
    "langchain": "python.langchain.com/docs",
    "llama-index": "docs.llamaindex.ai/en/stable",
    "openai": "platform.openai.com/docs",
}

async def search_web(query: str) -> dict | None:
    payload = json.dumps({"q": query, "num": 2})

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SERPER_URL, headers=headers, data=payload, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"organic": []}
  
async def fetch_url(url: str):
  async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            return text
        except httpx.TimeoutException:
            return "Timeout error"

@mcp.tool()  
async def get_docs(query: str, library: str):
  """
  Search the latest docs for a given query and library.
  Supports langchain, openai, and llama-index.

  Args:
    query: The query to search for (e.g. "Chroma DB")
    library: The library to search in (e.g. "langchain")

  Returns:
    Text from the docs
  """
  if library not in docs_urls:
    raise ValueError(f"Library {library} not supported by this tool")
  
  query = f"site:{docs_urls[library]} {query}"
  results = await search_web(query)
  if len(results["organic"]) == 0:
    return "No results found"
  
  text = ""
  for result in results["organic"]:
    text += await fetch_url(result["link"])
  return text


@mcp.tool()
async def setup_chroma_db(texts: List[str], metadatas: Optional[List[dict]] = None, persist_directory: Optional[str] = None):
    """
    Set up a ChromaDB vector database with LangChain integration.
    
    Args:
        texts: List of text strings to be embedded and stored in the vector database.
        metadatas: Optional list of metadata dictionaries corresponding to each text.
        persist_directory: Optional directory path to persist the vector database.
                          If None, an in-memory database will be created.
    
    Returns:
        Dict containing retriever info and success status.
    """
    # Create Document objects from texts
    documents = []
    for i, text in enumerate(texts):
        metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
        documents.append(Document(page_content=text, metadata=metadata))
    
    # Set up embeddings - using OpenAI embeddings as a common choice
    embeddings = OpenAIEmbeddings()
    
    # Create temporary directory if persist_directory is not provided
    if not persist_directory:
        temp_dir = tempfile.mkdtemp()
        persist_directory = temp_dir
    
    # Create and persist the Chroma vector store
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    # Persist the database
    vectorstore.persist()
    
    # Create a retriever from the vector store
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
    
    return {
        "status": "success",
        "message": f"ChromaDB vector database created successfully with {len(documents)} documents",
        "persist_directory": persist_directory,
        "retriever_type": type(retriever).__name__,
        "retriever_search_type": "similarity",
        "embedding_model": type(embeddings).__name__
    }

@mcp.tool()
async def query_chroma_db(query: str, persist_directory: str, top_k: int = 3):
    """
    Query a ChromaDB vector database using LangChain integration.
    
    Args:
        query: The query string to search for in the vector database.
        persist_directory: Directory path where the vector database is persisted.
        top_k: Number of top results to return (default: 3).
    
    Returns:
        List of retrieved documents with their content and metadata.
    """
    # Set up embeddings - must use the same embeddings as when creating the database
    embeddings = OpenAIEmbeddings()
    
    # Load the existing Chroma vector store
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Create a retriever from the vector store
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )
    
    # Retrieve documents similar to the query
    documents = retriever.get_relevant_documents(query)
    
    # Format the results
    results = []
    for i, doc in enumerate(documents):
        results.append({
            "rank": i + 1,
            "content": doc.page_content,
            "metadata": doc.metadata
        })
    
    return {
        "query": query,
        "results": results,
        "total_results": len(results)
    }

@mcp.tool()
async def chroma_db_demo(sample_texts: Optional[List[str]] = None):
    """
    Demonstrate the ChromaDB vector database with LangChain integration.
    
    Args:
        sample_texts: Optional list of sample texts to use for demonstration.
                     If not provided, default sample texts will be used.
    
    Returns:
        Results of setting up and querying the ChromaDB vector database.
    """
    # Use provided texts or default sample texts
    if not sample_texts:
        sample_texts = [
            "LangChain is a framework for developing applications powered by language models.",
            "Vector databases are essential for semantic search applications.",
            "ChromaDB is an open-source embedding database designed for AI applications.",
            "Embeddings convert text, images, or other data into vector representations.",
            "Retrieval Augmented Generation (RAG) combines retrieval systems with generative models."
        ]
    
    # Create metadata for each text
    sample_metadatas = [
        {"source": "langchain_docs", "topic": "framework"},
        {"source": "vector_db_article", "topic": "search"},
        {"source": "chroma_docs", "topic": "database"},
        {"source": "embeddings_paper", "topic": "vectors"},
        {"source": "rag_tutorial", "topic": "architecture"}
    ]
    
    # Set up the ChromaDB vector database
    setup_result = await setup_chroma_db(
        texts=sample_texts,
        metadatas=sample_metadatas
    )
    
    # Get the persist directory from the setup result
    persist_directory = setup_result["persist_directory"]
    
    # Query the database with different queries
    query_results = {}
    
    # Query 1: Framework related
    query_results["framework"] = await query_chroma_db(
        query="What is LangChain framework?",
        persist_directory=persist_directory,
        top_k=2
    )
    
    # Query 2: Database related
    query_results["database"] = await query_chroma_db(
        query="Tell me about ChromaDB",
        persist_directory=persist_directory,
        top_k=2
    )
    
    # Return combined results
    return {
        "setup": setup_result,
        "queries": query_results
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
