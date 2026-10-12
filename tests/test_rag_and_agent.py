import pytest
from src.rag import ConversationalRAG, ContextWindowManager, inspect_code_file, query_documentation_rag
from src.agent_service import process_agent_request

def test_conversational_rag_indexing():
    rag = ConversationalRAG()
    assert len(rag.chunks) > 10

    doc_chunks = [c for c in rag.chunks if c.chunk_type == "doc"]
    code_chunks = [c for c in rag.chunks if c.chunk_type == "code"]

    assert len(doc_chunks) > 0
    assert len(code_chunks) > 0
    assert any("ARCHITECTURE.md" in c.file_path for c in doc_chunks)
    assert any("src/models/registry.py" in c.file_path for c in code_chunks)

def test_context_window_query_reformulation():
    mgr = ContextWindowManager(max_context_chars=7000, max_history_turns=4)

    # Coreference expansion
    history = [
        {"sender": "user", "text": "Can you explain the Kubernetes zero downtime rollback?"},
        {"sender": "agent", "text": "The rollback mechanism uses dual layers: Kubernetes container rollback and atomic pointer swap."}
    ]
    reformulated = mgr.reformulate_conversational_query("how does it work?", history=history)
    assert "how does it work?" in reformulated
    assert any(w in reformulated.lower() for w in ["kubernetes", "rollback", "mechanism", "pointer"])

def test_context_window_history_budget():
    mgr = ContextWindowManager(max_context_chars=7000, max_history_turns=4)
    long_history = [
        {"sender": "user", "text": f"User turn {i}: " + "x" * 500}
        for i in range(10)
    ]
    budgeted = mgr.format_history_within_budget(long_history, max_chars=2000)
    total_chars = sum(len(m["content"]) for m in budgeted)
    assert total_chars <= 2500
    assert len(budgeted) < len(long_history)

def test_inspect_code_file_tool():
    res = inspect_code_file("src/models/registry.py", max_lines=30)
    assert res["status"] == "success"
    assert res["file"] == "src/models/registry.py"
    assert res["displayedLines"] == 30
    assert "class ModelRegistry" in res["content"] or "Model Registry" in res["content"]

    # Non-existent file
    bad_res = inspect_code_file("src/non_existent_file.py")
    assert bad_res["status"] == "error"

@pytest.mark.asyncio
async def test_agent_service_react_loop_and_recommendations():
    # Test model battle response contains recommendations and clean mermaid
    req = {"prompt": "Run model battle arena tournament and compare LightGBM vs ETS vs Naive"}
    res = await process_agent_request(req)

    assert res["action"] == "RUN_MODEL_BATTLE"
    assert len(res["reactSteps"]) == 3
    assert res["contextWindow"]["estimatedTokens"] > 0
    assert "Recommended Next Inquiries" in res["message"]
    assert "```mermaid" in res["message"] or "flowchart" in res["message"]
    assert len(res["suggestedActions"]) > 0

    # Test price shock simulation response contains recommendations
    drift_req = {"prompt": "Simulate a price shock drift in Dairy and evaluate PSI"}
    drift_res = await process_agent_request(drift_req)

    assert drift_res["action"] == "EXECUTE_DRIFT_SIMULATION"
    assert any(k in drift_res["message"] for k in ["0.396", "PSI", "psi", "drift"])
    assert any(k in drift_res["message"].lower() for k in ["recommend", "next", "inquiries", "inquiry", "retrain"])
