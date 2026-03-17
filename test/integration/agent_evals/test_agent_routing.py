"""Evaluate Router agent's ability to route queries to appropriate agents."""
import time

import pytest

from .base import AgentEvalTestCase


pytestmark = pytest.mark.requires_llm


class TestAgentRoutingQuality(AgentEvalTestCase):
    """Test Router's routing decisions for every possible route."""

    def _query_and_capture(self, prompt: str, expected_agent: str) -> dict:
        """Send a prompt to the router, capture full metadata, and return result dict."""
        start_time = time.time()
        response = self._post("/api/ai/agents/query", data={"query": prompt, "agent_type": "router"}, json=True)
        if response.status_code == 500:
            time.sleep(5)
            response = self._post("/api/ai/agents/query", data={"query": prompt, "agent_type": "router"}, json=True)
        query_duration = time.time() - start_time

        self._assert_status_code_is(response, 200)
        result = response.json()
        agent_resp = result.get("response", {})
        metadata = agent_resp.get("metadata", {}) if isinstance(agent_resp, dict) else {}

        self._test_metrics.update({
            "query_duration_ms": int(query_duration * 1000),
            "prompt": prompt,
            "agent_response": agent_resp.get("content", "") if isinstance(agent_resp, dict) else str(agent_resp),
            "agent_type": agent_resp.get("agent_type", "router") if isinstance(agent_resp, dict) else "unknown",
            "expected_agent": expected_agent,
            "routing_method": metadata.get("method", ""),
        })

        # Orchestrator plan — agents_used + execution_type
        if metadata.get("agents_used"):
            self._test_metrics["orchestrator_agents_used"] = metadata["agents_used"]
            self._test_metrics["orchestrator_execution_type"] = metadata.get("execution_type", "unknown")

        # Router handoff info (source_agent → target_agent)
        handoff = metadata.get("handoff_info", {})
        if handoff:
            self._test_metrics["handoff_info"] = handoff

        if result.get("usage"):
            self._test_metrics["agent_tokens_input"] = result["usage"].get("input_tokens", 0)
            self._test_metrics["agent_tokens_output"] = result["usage"].get("output_tokens", 0)

        return result

    # ── Direct answer (router replies without delegating) ────────────────────

    def test_routes_galaxy_platform_question_directly(self):
        """Router should answer basic Galaxy platform questions directly (no handoff)."""
        prompt = "What is a Galaxy workflow and how do I create one?"
        result = self._query_and_capture(prompt, expected_agent="router")
        agent_type = result["response"]["agent_type"]
        assert agent_type == "router", (
            f"Expected direct answer from router, got handoff to '{agent_type}'"
        )

    # ── tool_recommendation ──────────────────────────────────────────────────

    def test_routes_tool_query_to_tool_recommendation(self):
        """Router should delegate tool discovery queries to tool_recommendation."""
        prompt = "What Galaxy tool should I use for RNA-seq alignment?"
        result = self._query_and_capture(prompt, expected_agent="tool_recommendation")
        assert result["response"]["agent_type"] == "tool_recommendation"

    def test_routes_tool_discovery_to_tool_recommendation(self):
        """'Is there a tool that does X?' should go to tool_recommendation."""
        prompt = "Is there a Galaxy tool that converts BAM files to FASTQ format?"
        result = self._query_and_capture(prompt, expected_agent="tool_recommendation")
        assert result["response"]["agent_type"] == "tool_recommendation"

    # ── error_analysis ───────────────────────────────────────────────────────

    def test_routes_pasted_error_to_error_analysis(self):
        """Router should delegate queries with pasted error details to error_analysis."""
        prompt = (
            "My HISAT2 alignment job failed with this error:\n"
            "Error: could not open file '/data/genome.fa': No such file or directory\n"
            "Exit code: 1\n"
            "What went wrong and how do I fix it?"
        )
        result = self._query_and_capture(prompt, expected_agent="error_analysis")
        assert result["response"]["agent_type"] == "error_analysis"

    # ── custom_tool ──────────────────────────────────────────────────────────

    def test_routes_tool_creation_to_custom_tool(self):
        """Router should delegate tool creation requests to custom_tool."""
        prompt = "I want to create a Galaxy tool that wraps the samtools flagstat command."
        result = self._query_and_capture(prompt, expected_agent="custom_tool")
        assert result["response"]["agent_type"] == "custom_tool"

    # ── history_analyzer ─────────────────────────────────────────────────────

    def test_routes_history_summary_to_history_analyzer(self):
        """Router should delegate history summarization to history_analyzer."""
        prompt = "Can you summarize what analysis I ran in my Galaxy history?"
        result = self._query_and_capture(prompt, expected_agent="history_analyzer")
        assert result["response"]["agent_type"] == "history_analyzer"

    def test_routes_methods_section_to_history_analyzer(self):
        """Router should delegate methods section requests to history_analyzer."""
        prompt = "Generate a methods section for my paper based on my Galaxy analysis history."
        result = self._query_and_capture(prompt, expected_agent="history_analyzer")
        assert result["response"]["agent_type"] == "history_analyzer"

    # ── orchestrator ─────────────────────────────────────────────────────────

    def test_routes_workflow_design_to_orchestrator(self):
        """Router should delegate complex multi-step workflows to orchestrator."""
        prompt = (
            "I want to build a complete RNA-seq analysis pipeline from FASTQ to "
            "differential expression results. Can you help me design this workflow?"
        )
        result = self._query_and_capture(prompt, expected_agent="orchestrator")
        assert result["response"]["agent_type"] == "orchestrator"

    def test_routes_find_failed_job_to_orchestrator(self):
        """'What failed in my history?' requires history lookup then error analysis — orchestrator."""
        prompt = "What failed in my Galaxy history and why?"
        result = self._query_and_capture(prompt, expected_agent="orchestrator")
        agent_type = result["response"]["agent_type"]
        assert agent_type == "orchestrator", (
            f"Expected orchestrator (needs history lookup + error analysis), got '{agent_type}'"
        )
        # Verify the orchestrator planned both sub-agents
        agents_used = self._test_metrics.get("orchestrator_agents_used", [])
        assert "history_analyzer" in agents_used, (
            f"Orchestrator should include history_analyzer in plan, got: {agents_used}"
        )

    def test_routes_next_step_advice_to_orchestrator(self):
        """'What should I do next?' needs history context + recommendations — orchestrator."""
        prompt = "Based on my current Galaxy analysis, what should I do next?"
        result = self._query_and_capture(prompt, expected_agent="orchestrator")
        assert result["response"]["agent_type"] == "orchestrator"
