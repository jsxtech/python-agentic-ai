"""Offline unit tests for the second-round audit fixes.

No network/API calls are made.
"""
import os

import config
from config import parse_score, safe_resolved_path

# --- config.parse_score ----------------------------------------------------

def test_parse_score_bare_number():
    assert parse_score("8") == 8.0


def test_parse_score_with_prose():
    assert parse_score("Score: 8 out of 10") == 8.0


def test_parse_score_fraction_form():
    assert parse_score("8/10") == 8.0


def test_parse_score_clamps_high():
    assert parse_score("42", high=10.0) == 10.0


def test_parse_score_default_when_no_number():
    assert parse_score("no number here", default=5.0) == 5.0


def test_parse_score_none():
    assert parse_score(None, default=3.0) == 3.0


# --- config.safe_resolved_path --------------------------------------------

def test_safe_resolved_path_relative_inside():
    resolved = safe_resolved_path("a.txt")
    assert resolved is not None
    assert resolved.startswith(os.path.realpath(config.SANDBOX_DIR))


def test_safe_resolved_path_traversal_none():
    assert safe_resolved_path("../config.py") is None


def test_safe_resolved_path_symlink_escape_none(tmp_path):
    # A symlink inside the sandbox pointing outside must resolve to None.
    os.makedirs(config.SANDBOX_DIR, exist_ok=True)
    link = os.path.join(config.SANDBOX_DIR, "test_escape_link")
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink("/etc/hostname", link)
    try:
        assert safe_resolved_path("test_escape_link") is None
    finally:
        os.remove(link)


# --- calculate nested-power DoS -------------------------------------------

def test_calculate_blocks_nested_power():
    from agent import calculate
    assert calculate("(10**1000)**1000").startswith("Error")


def test_calculate_allows_signed_base_power():
    from agent import calculate
    assert calculate("(-2)**3") == "-8"


# --- Negotiation acceptance detection -------------------------------------

def test_negotiation_accept_positive():
    from social_agents import NegotiationAgent
    assert NegotiationAgent._is_acceptance("Yes, I accept your proposal.") is True
    assert NegotiationAgent._is_acceptance("We agree to these terms") is True


def test_negotiation_accept_rejects_negations():
    from social_agents import NegotiationAgent
    assert NegotiationAgent._is_acceptance("This is unacceptable") is False
    assert NegotiationAgent._is_acceptance("I cannot accept that") is False


# --- MonitoringAgent anomaly with zero baseline ---------------------------

def test_monitor_zero_baseline_no_false_anomaly():
    from social_agents import MonitoringAgent
    m = MonitoringAgent()
    m.collect_metrics("x", 0)
    m.collect_metrics("x", 0)
    m.collect_metrics("x", 1)  # tiny change on zero baseline
    # With the absolute floor, a change of 1 should not be flagged.
    assert m.detect_anomaly("x") is False


def test_monitor_detects_real_anomaly():
    from social_agents import MonitoringAgent
    m = MonitoringAgent()
    for v in (50, 52, 48):
        m.collect_metrics("cpu", v)
    m.collect_metrics("cpu", 500)  # large spike
    assert m.detect_anomaly("cpu") is True


def test_monitor_metrics_bounded():
    from social_agents import MonitoringAgent
    m = MonitoringAgent(max_samples=10)
    for i in range(50):
        m.collect_metrics("cpu", i)
    assert len(m.metrics["cpu"]) == 10


# --- AgentWorkflow guards --------------------------------------------------

def test_workflow_empty_nodes():
    from agent_advanced import AgentWorkflow
    wf = AgentWorkflow()
    result = wf.execute("input")
    assert result == {"result": "input", "path": []}


def test_workflow_cycle_terminates(monkeypatch):
    from agent_advanced import AgentWorkflow
    wf = AgentWorkflow()
    wf.add_node("a", "t", {"instruction": "x"})
    wf.add_node("b", "t", {"instruction": "y"})
    wf.add_edge("a", "b")
    wf.add_edge("b", "a")  # cycle
    # Stub node execution so no API call happens.
    monkeypatch.setattr(wf, "_execute_node", lambda node, data: data)
    result = wf.execute("start")
    # Must terminate; each node visited at most once.
    assert result["path"] == ["a", "b"]


# --- EmotionalAgent neutral label -----------------------------------------

def test_emotional_neutral_label():
    from cognitive_agents import EmotionalAgent
    e = EmotionalAgent()  # defaults 0.5/0.5/0.5
    assert e.get_emotion_label() == "neutral"


def test_emotional_happy_label():
    from cognitive_agents import EmotionalAgent
    e = EmotionalAgent()
    e.emotional_state = {"valence": 0.9, "arousal": 0.9, "dominance": 0.5}
    assert e.get_emotion_label() == "excited/happy"


# --- AgentMonitor health uses error_rate ----------------------------------

def test_monitor_health_error_rate_wired():
    from agent_testing import AgentMonitor
    mon = AgentMonitor()
    mon.log_performance(1.0)
    mon.log_error("boom")  # 1 error / 2 ops = 50% > 10% threshold
    health = mon.get_health()
    assert "error_rate" in health
    assert health["status"] in ("degraded", "critical")


def test_monitor_alert_once(capsys):
    from agent_testing import AgentMonitor
    mon = AgentMonitor()
    for _ in range(15):
        mon.log_error("e")
    out = capsys.readouterr().out
    # "High error rate detected" alert should appear exactly once.
    assert out.count("High error rate detected") == 1


# --- RAG add_document extension -------------------------------------------

def test_rag_rejects_non_txt(tmp_path):
    from rag_agent import RAGAgent
    rag = RAGAgent(knowledge_dir=str(tmp_path))
    assert rag.add_document("notes.md", "x").startswith("Error")
    assert "Added" in rag.add_document("notes.txt", "x")
