"""
Data Retrieval Agent — AutoGen AssistantAgent (free/OSS)

Grounded on local exports of SharePoint (JSON), Azure DevOps (JSON), and D365 (CSV).
Embeddings via HuggingFace sentence-transformers (all-MiniLM-L6-v2); vector store via ChromaDB.
Hybrid RAG: LlamaIndex BM25 + ChromaDB semantic search with Reciprocal Rank Fusion.

AutoGen Integration:
  The DataRetriever is an AutoGen AssistantAgent with registered tools for hybrid
  knowledge base queries. In the free stack, we use a MockModelClient that simulates
  the LLM component (since we don't need an LLM for structured retrieval).

STEP UP: In production, replace:
  - MockModelClient → Azure OpenAI model client
  - ChromaDB → Azure AI Search
  - HuggingFace local embeddings → Azure OpenAI text-embedding-ada-002
"""
import json
import os
import sys
import logging
import time
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer

# ---------- LlamaIndex imports for BM25 Hybrid RAG ----------
try:
    from llama_index.core import Document as LlamaDocument
    from llama_index.core.schema import TextNode
    from llama_index.retrievers.bm25 import BM25Retriever
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False

# ---------- Config ----------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from config import (
        DATA_DIR, SHAREPOINT_FILE, D365_FILE, DEVOPS_FILE,
        CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME
    )
except ImportError:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    SHAREPOINT_FILE = os.path.join(DATA_DIR, "mock_sharepoint.json")
    D365_FILE = os.path.join(DATA_DIR, "mock_d365.csv")
    DEVOPS_FILE = os.path.join(DATA_DIR, "mock_devops.json")
    CHROMA_DB_PATH = os.path.join(DATA_DIR, "chroma_db")
    CHROMA_COLLECTION_NAME = "project_data"
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

logger = logging.getLogger("IntelligentDeliveryAgent")

# ---------- Initialize local embedding model ----------
logger.info(f"[Retrieval Agent] Loading embedding model: {EMBEDDING_MODEL_NAME}")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# ---------- Initialize ChromaDB ----------
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

# ---------- BM25 Document Store (populated at ingest time) ----------
_bm25_nodes = []  # Holds TextNode objects for BM25 retriever

# ---------- Ingestion Metadata ----------
_ingestion_stats = {
    "total_documents": 0,
    "sharepoint_docs": 0,
    "devops_docs": 0,
    "d365_docs": 0,
    "last_ingested": None
}


def _build_all_documents():
    """Builds a list of text documents from all data sources for ingestion."""
    documents = []

    # SharePoint documents
    if os.path.exists(SHAREPOINT_FILE):
        with open(SHAREPOINT_FILE, "r") as f:
            sp_data = json.load(f)
            for item in sp_data:
                text = (
                    f"Project {item['projectId']} ({item['projectName']}): "
                    f"Status is {item['status']}. Managed by {item['manager']}. "
                    f"Client: {item.get('client', 'N/A')}. "
                    f"Technology: {item.get('technology', 'N/A')}. "
                    f"Phase: {item.get('phase', 'N/A')}. "
                    f"Priority: {item.get('priority', 'N/A')}. "
                    f"Team size: {item.get('teamSize', 'N/A')}. "
                    f"Timeline: {item.get('startDate', 'N/A')} to {item.get('endDate', 'N/A')}. "
                    f"{item['description']}"
                )
                documents.append({
                    "id": f"sp_{item['projectId']}",
                    "text": text,
                    "metadata": {
                        "source": "sharepoint",
                        "projectId": item["projectId"],
                        "projectName": item.get("projectName", ""),
                        "status": item.get("status", ""),
                    }
                })

    # D365 Financial documents
    if os.path.exists(D365_FILE):
        df = pd.read_csv(D365_FILE)
        grouped = df.groupby("projectId")
        for project_id, group in grouped:
            total_hours = group["hoursLogged"].sum()
            total_budget_hours = group["budgetedHours"].sum()
            total_cost = group["costActual"].sum()
            total_budget_cost = group["costBudget"].sum()
            resources = group["resourceName"].unique().tolist()
            roles = group["role"].unique().tolist() if "role" in group.columns else []

            text = (
                f"Financials for Project {project_id}: "
                f"Total hours logged {total_hours}/{total_budget_hours}. "
                f"Cost actual ${total_cost:,.0f} vs budget ${total_budget_cost:,.0f}. "
                f"Resources: {', '.join(resources)}. "
                f"Roles: {', '.join(roles)}. "
                f"{'OVER BUDGET' if total_cost > total_budget_cost else 'Within budget'}."
            )
            documents.append({
                "id": f"d365_{project_id}",
                "text": text,
                "metadata": {
                    "source": "d365",
                    "projectId": str(project_id),
                    "overBudget": str(total_cost > total_budget_cost),
                }
            })

            # Also add per-resource entries for detailed queries
            for _, row in group.iterrows():
                resource_text = (
                    f"Timesheet: {row['resourceName']} "
                    f"({row.get('role', 'N/A')}) on Project {project_id}. "
                    f"Hours: {row['hoursLogged']}/{row['budgetedHours']}. "
                    f"Cost: ${row['costActual']:,.0f}/${row['costBudget']:,.0f}."
                )
                week = row.get("weekEnding", "")
                doc_id = f"d365_{project_id}_{row['resourceName'].replace(' ', '_')}_{week}"
                documents.append({
                    "id": doc_id,
                    "text": resource_text,
                    "metadata": {
                        "source": "d365",
                        "projectId": str(project_id),
                        "resourceName": row["resourceName"],
                    }
                })

    # DevOps Sprint documents
    if os.path.exists(DEVOPS_FILE):
        with open(DEVOPS_FILE, "r") as f:
            devops_data = json.load(f)
            for item in devops_data:
                work_items = item.get("workItems", [])
                wi_summary = "; ".join([
                    f"{wi['title']} ({wi['type']}, {wi['state']})"
                    for wi in work_items[:5]
                ])
                text = (
                    f"Sprint data for Project {item['projectId']}: "
                    f"Current sprint is {item.get('sprint', 'N/A')}. "
                    f"Velocity: {item.get('velocity', 0)}/{item.get('totalStoryPoints', 0)} story points. "
                    f"Bugs opened: {item.get('bugsOpened', 0)}, closed: {item.get('bugsClosed', 0)}. "
                    f"Active blockers: {item.get('blockers', 0)}. "
                    f"Completion: {item.get('completedStoryPoints', 0)}/{item.get('totalStoryPoints', 0)}. "
                    f"Key work items: {wi_summary}."
                )
                documents.append({
                    "id": f"devops_{item['projectId']}",
                    "text": text,
                    "metadata": {
                        "source": "devops",
                        "projectId": item["projectId"],
                        "sprint": item.get("sprint", ""),
                    }
                })

    return documents


def ingest_data():
    """Reads local data and ingests it into ChromaDB + BM25 index."""
    global _bm25_nodes, _ingestion_stats

    documents = _build_all_documents()
    logger.info(f"[Retrieval Agent] Ingesting {len(documents)} documents into ChromaDB and BM25 index...")

    _bm25_nodes = []

    # Count by source
    sp_count = sum(1 for d in documents if d["metadata"]["source"] == "sharepoint")
    devops_count = sum(1 for d in documents if d["metadata"]["source"] == "devops")
    d365_count = sum(1 for d in documents if d["metadata"]["source"] == "d365")

    for doc in documents:
        # ChromaDB ingestion (semantic search)
        embedding = embedding_model.encode(doc["text"]).tolist()
        collection.upsert(
            documents=[doc["text"]],
            embeddings=[embedding],
            metadatas=[doc["metadata"]],
            ids=[doc["id"]]
        )

        # BM25 ingestion (keyword search via LlamaIndex)
        if LLAMA_INDEX_AVAILABLE:
            node = TextNode(
                text=doc["text"],
                id_=doc["id"],
                metadata=doc["metadata"]
            )
            _bm25_nodes.append(node)

    _ingestion_stats = {
        "total_documents": len(documents),
        "sharepoint_docs": sp_count,
        "devops_docs": devops_count,
        "d365_docs": d365_count,
        "last_ingested": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "chromadb_count": collection.count(),
        "bm25_nodes": len(_bm25_nodes),
        "bm25_available": LLAMA_INDEX_AVAILABLE,
    }

    logger.info(
        f"[Retrieval Agent] Ingestion complete. "
        f"ChromaDB: {collection.count()} docs. BM25 nodes: {len(_bm25_nodes)}. "
        f"(SP: {sp_count}, DevOps: {devops_count}, D365: {d365_count})"
    )


def get_ingestion_stats() -> dict:
    """Returns metadata about the last data ingestion."""
    return _ingestion_stats.copy()


def _chromadb_search(query: str, top_k: int = 5, source_filter: str = None) -> list:
    """
    Performs semantic search using ChromaDB.

    Args:
        query: The search query text
        top_k: Number of results to return
        source_filter: Optional filter by data source ('sharepoint', 'd365', 'devops')
    """
    query_embedding = embedding_model.encode(query).tolist()

    where_filter = None
    if source_filter:
        where_filter = {"source": source_filter}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter
    )

    scored_results = []
    if results["documents"] and results["documents"][0]:
        for i, doc_text in enumerate(results["documents"][0]):
            distance = results["distances"][0][i] if results.get("distances") else 1.0
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            scored_results.append({
                "text": doc_text,
                "score": 1.0 / (1.0 + distance),  # Convert distance to similarity
                "source": "semantic",
                "metadata": metadata
            })
    return scored_results


def _bm25_search(query: str, top_k: int = 5) -> list:
    """Performs BM25 keyword search using LlamaIndex BM25Retriever."""
    if not LLAMA_INDEX_AVAILABLE or not _bm25_nodes:
        logger.warning("[Retrieval Agent] BM25 search unavailable (LlamaIndex not installed or no nodes ingested).")
        return []

    try:
        bm25_retriever = BM25Retriever.from_defaults(
            nodes=_bm25_nodes,
            similarity_top_k=top_k
        )
        results = bm25_retriever.retrieve(query)
        scored_results = []
        for node_with_score in results:
            scored_results.append({
                "text": node_with_score.node.get_content(),
                "score": node_with_score.score if node_with_score.score else 0.5,
                "source": "bm25",
                "metadata": node_with_score.node.metadata if hasattr(node_with_score.node, 'metadata') else {}
            })
        return scored_results
    except Exception as e:
        logger.warning(f"[Retrieval Agent] BM25 search failed: {e}")
        return []


def _reciprocal_rank_fusion(semantic_results: list, bm25_results: list, k: int = 60) -> list:
    """
    Reciprocal Rank Fusion (RRF) to merge semantic and BM25 results.
    RRF score = sum( 1 / (k + rank) ) for each result list.
    """
    rrf_scores = {}

    # Score from semantic results
    for rank, result in enumerate(semantic_results):
        doc_key = result["text"][:100]  # Use first 100 chars as key
        rrf_scores[doc_key] = rrf_scores.get(doc_key, {
            "text": result["text"], "score": 0.0,
            "metadata": result.get("metadata", {})
        })
        rrf_scores[doc_key]["score"] += 1.0 / (k + rank + 1)

    # Score from BM25 results
    for rank, result in enumerate(bm25_results):
        doc_key = result["text"][:100]
        rrf_scores[doc_key] = rrf_scores.get(doc_key, {
            "text": result["text"], "score": 0.0,
            "metadata": result.get("metadata", {})
        })
        rrf_scores[doc_key]["score"] += 1.0 / (k + rank + 1)

    # Sort by fused score descending
    fused = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
    return fused


def hybrid_query_knowledge_base(query: str, top_k: int = 3, source_filter: str = None) -> str:
    """
    Hybrid RAG: Combines LlamaIndex BM25 keyword search with ChromaDB
    semantic search using Reciprocal Rank Fusion (RRF).

    Args:
        query: The search query text
        top_k: Number of fused results to return
        source_filter: Optional source filter ('sharepoint', 'd365', 'devops')

    Returns:
        Concatenated text of top-k fused results.
    """
    logger.info(f"[Hybrid RAG] Running hybrid search for: '{query}' (filter={source_filter})")

    # 1. ChromaDB semantic search
    semantic_results = _chromadb_search(query, top_k=top_k + 2, source_filter=source_filter)
    logger.info(f"[Hybrid RAG] Semantic search returned {len(semantic_results)} results.")

    # 2. LlamaIndex BM25 keyword search
    bm25_results = _bm25_search(query, top_k=top_k + 2)
    logger.info(f"[Hybrid RAG] BM25 search returned {len(bm25_results)} results.")

    # 3. Reciprocal Rank Fusion
    fused_results = _reciprocal_rank_fusion(semantic_results, bm25_results)
    logger.info(f"[Hybrid RAG] RRF fused into {len(fused_results)} unique results.")

    if not fused_results:
        return "No relevant information found in knowledge base."

    # Return top_k fused results
    top_results = fused_results[:top_k]
    return "\n".join([r["text"] for r in top_results])


def query_knowledge_base(query: str, top_k: int = 3) -> str:
    """Backward-compatible wrapper. Now uses hybrid search internally."""
    return hybrid_query_knowledge_base(query, top_k)


# ---------- AutoGen Agent Setup ----------

class MockModelClient:
    """
    Mock model client for AutoGen AssistantAgent (free stack).

    In the free tier, we don't need an LLM for structured retrieval —
    the tools themselves contain the logic. This mock satisfies AutoGen's
    requirement for a model client.

    STEP UP: Replace with AzureOpenAIChatCompletionClient:
        from autogen_ext.models import AzureOpenAIChatCompletionClient
        model_client = AzureOpenAIChatCompletionClient(
            model="gpt-4o",
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
        )
    """
    def __init__(self):
        self.model_info = {
            "function_calling": True,
            "vision": False,
            "name": "mock-free-tier",
            "json_output": True,
        }


def get_retrieval_agent():
    """
    Creates an AutoGen AssistantAgent with the hybrid RAG tool registered.
    The agent can be invoked to perform knowledge-base queries.

    AutoGen Integration Pattern:
      - AssistantAgent wraps the retrieval logic
      - Tools are registered for function-calling
      - In free stack, MockModelClient bypasses LLM requirement
      - In production (Step Up), AzureOpenAIChatCompletionClient would
        allow the agent to reason about which tools to call

    STEP UP: Replace MockModelClient with Azure OpenAI model client
    and enable multi-turn agent conversations via AutoGen GroupChat.
    """
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_ext.models.openai import OpenAIChatCompletionClient
    except ImportError:
        logger.warning("[AutoGen] AutoGen not installed. Returning None for retrieval agent.")
        return None

    # Load Groq API Key
    from src.config import GROQ_API_KEY
    
    # Configure AutoGen to use Groq's OpenAI-compatible endpoint
    model_client = OpenAIChatCompletionClient(
        model="qwen/qwen3.8-27b",
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "unknown"
        }
    )

    retriever = AssistantAgent(
        name="DataRetriever",
        description=(
            "A data retrieval agent for the Intelligent Client Delivery system. "
            "Has access to a hybrid knowledge base (BM25 + semantic search) "
            "containing SharePoint project pages, Azure DevOps sprint data, "
            "and D365 Project Operations timesheets. Uses Reciprocal Rank Fusion "
            "to combine keyword and vector search results."
        ),
        model_client=model_client,
        tools=[hybrid_query_knowledge_base]
    )

    logger.info("[AutoGen] DataRetriever AssistantAgent created with Groq LLM and hybrid RAG tool.")
    return retriever


# ---------- Module Initialization ----------
# Auto-ingest data when the module is first imported
ingest_data()

if __name__ == "__main__":
    print("=== Testing Hybrid RAG ===")
    result = hybrid_query_knowledge_base("budget for Project Beta")
    print(result)
    print("\n=== Testing Source-Filtered Search ===")
    result = hybrid_query_knowledge_base("Project Alpha", source_filter="sharepoint")
    print(result)
    print("\n=== Testing AutoGen Agent Creation ===")
    agent = get_retrieval_agent()
    print(f"Agent: {agent}")
    print(f"\n=== Ingestion Stats ===")
    print(json.dumps(get_ingestion_stats(), indent=2))
