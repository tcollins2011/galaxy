"""Evaluate ToolRecommendation agent's accuracy for tool suggestions."""
import time

import pytest

from .base import AgentEvalTestCase


pytestmark = pytest.mark.requires_llm


class TestToolRecommendationAccuracy(AgentEvalTestCase):
    """Test tool recommendation quality."""

    def test_recommends_fastqc_for_qc(self):
        """Should recommend FastQC for quality control."""
        prompt = "I need to check the quality of my FASTQ files. What tool should I use?"

        start_time = time.time()
        response = self._post(
            "/api/ai/agents/query", data={"query": prompt, "agent_type": "tool_recommendation"}, json=True
        )
        query_duration = time.time() - start_time

        result = response.json()
        content = result["response"]["content"].lower()

        self._test_metrics.update({
            "query_duration_ms": int(query_duration * 1000),
            "prompt": prompt,
            "agent_response": result["response"]["content"],
            "expected_tool": "fastqc",
        })

        if "usage" in result:
            self._test_metrics["agent_tokens_input"] = result["usage"].get("input_tokens", 0)
            self._test_metrics["agent_tokens_output"] = result["usage"].get("output_tokens", 0)

        assert "fastqc" in content or "fast qc" in content

    def test_recommends_alignment_tools(self):
        """Should recommend alignment tools for mapping."""
        prompt = "I need to align RNA-seq reads to a reference genome."

        start_time = time.time()
        response = self._post(
            "/api/ai/agents/query", data={"query": prompt, "agent_type": "tool_recommendation"}, json=True
        )
        query_duration = time.time() - start_time

        result = response.json()
        content = result["response"]["content"].lower()

        self._test_metrics.update({
            "query_duration_ms": int(query_duration * 1000),
            "prompt": prompt,
            "agent_response": result["response"]["content"],
            "expected_tools": ["hisat2", "star", "bowtie", "bwa"],
        })

        if "usage" in result:
            self._test_metrics["agent_tokens_input"] = result["usage"].get("input_tokens", 0)
            self._test_metrics["agent_tokens_output"] = result["usage"].get("output_tokens", 0)

        alignment_tools = ["hisat2", "star", "bowtie", "bwa"]
        assert any(tool in content for tool in alignment_tools)
