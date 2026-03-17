"""Agent evaluation tests for bioinformatics workflows.

Tests Galaxy AI agents (Router, ToolRecommendation, Orchestrator) with
real-world bioinformatics use cases:
- Single-cell RNA-seq cell type identification
- Bulk RNA-seq differential expression
- QC triage for problematic FastQC results
- Low mapping rate troubleshooting
- Metagenomics community composition
- Somatic variant calling
- General onboarding guidance
- Coverage anomalies and artifacts

Uses LLM-as-judge (Claude Opus 4.6) to assess response quality against rubrics.
"""
import json
import os
import time

import pytest

from anthropic import (
    Anthropic,
    APIError,
    APITimeoutError,
    RateLimitError,
)
from galaxy_test.base.populators import DatasetPopulator

from .base import AgentEvalTestCase


# Requires live LLM for evaluation
pytestmark = pytest.mark.requires_llm


class TestBioinformaticsWorkflowEvals(AgentEvalTestCase):
    """Evaluate agent responses for bioinformatics workflows."""

    dataset_populator: DatasetPopulator

    def setUp(self):
        super().setUp()
        self.dataset_populator = DatasetPopulator(self.galaxy_interactor)

    @pytest.mark.asyncio
    async def test_scrna_cell_type_identification(self):
        """7.1 Single-cell RNA-seq: Identify cell types.

        Goal: Evaluate scRNA-seq reasoning (clustering → marker genes → annotation).
        """
        prompt = (
            "I just got my single-cell RNA-seq count matrix back. "
            "How can I figure out what cell types are present?"
        )

        response = await self._query_router(prompt)

        quality_score = await self._evaluate_response(
            response=response,
            rubric=(
                "Response should mention:\n"
                "1. Clustering algorithms (Louvain, Leiden, UMAP/tSNE for visualization)\n"
                "2. Marker gene identification (differential expression between clusters)\n"
                "3. Cell type annotation (manual or automated using reference databases)\n"
                "4. Relevant Galaxy tools (Scanpy, Seurat wrapper tools if available)\n"
                "5. General workflow: QC → normalization → clustering → marker genes → annotation"
            ),
            min_score=0.7,
        )

        assert quality_score >= 0.7, f"Response quality too low: {quality_score}"

    @pytest.mark.asyncio
    async def test_bulk_rnaseq_differential_expression(self):
        """7.2 Bulk RNA-seq: Differential expression.

        Goal: Verify the agent describes a proper DE pipeline.
        """
        prompt = (
            "I have RNA-seq FASTQ files from two conditions. "
            "How do I identify differentially expressed genes between them?"
        )

        response = await self._query_router(prompt)

        quality_score = await self._evaluate_response(
            response=response,
            rubric=(
                "Response should outline:\n"
                "1. QC step (FastQC)\n"
                "2. Alignment/quantification (HISAT2, STAR, or Salmon/kallisto)\n"
                "3. Count aggregation (featureCounts, HTSeq-count)\n"
                "4. Differential expression analysis (DESeq2, edgeR, limma)\n"
                "5. Mention of replicates and experimental design importance\n"
                "6. Optional: Functional enrichment analysis (GO, KEGG)"
            ),
            min_score=0.7,
        )

        assert quality_score >= 0.7, f"Response quality too low: {quality_score}"

    @pytest.mark.asyncio
    async def test_qc_triage_fastqc(self):
        """7.3 QC triage: Problematic FastQC results.

        Goal: Evaluate reasoning on QC-based preprocessing.
        """
        prompt = (
            "My FastQC reports show poor quality at the ends and clear adapter contamination. "
            "What should I do next to clean up the data?"
        )

        response = await self._query_router(prompt)

        quality_score = await self._evaluate_response(
            response=response,
            rubric=(
                "Response should recommend:\n"
                "1. Adapter trimming (Cutadapt, Trim Galore, Trimmomatic)\n"
                "2. Quality trimming (remove low-quality bases at ends)\n"
                "3. Re-run FastQC after trimming to verify improvement\n"
                "4. Specific Galaxy tools for trimming\n"
                "5. Optional: Explanation of quality scores and adapter contamination"
            ),
            min_score=0.7,
        )

        assert quality_score >= 0.7, f"Response quality too low: {quality_score}"

    @pytest.mark.asyncio
    async def test_low_mapping_rate_troubleshooting(self):
        """7.4 Low mapping rate troubleshooting.

        Goal: Test diagnostic insight for alignment problems.
        """
        prompt = (
            "My reads only mapped at about 50%. "
            "What could be causing the low mapping rate, and how can I figure out what's wrong?"
        )

        response = await self._query_router(prompt)

        quality_score = await self._evaluate_response(
            response=response,
            rubric=(
                "Response should suggest investigating:\n"
                "1. Wrong reference genome (species mismatch)\n"
                "2. Adapter/quality issues (check FastQC)\n"
                "3. Contamination (run FastQ Screen or Kraken)\n"
                "4. rRNA contamination (if RNA-seq)\n"
                "5. Library type issues (stranded vs unstranded)\n"
                "6. Diagnostic tools: FastQ Screen, Kraken2, BLAST unmapped reads"
            ),
            min_score=0.7,
        )

        assert quality_score >= 0.7, f"Response quality too low: {quality_score}"

    @pytest.mark.asyncio
    async def test_metagenomics_community_composition(self):
        """7.5 Metagenomics: Identify community composition.

        Goal: Test reasoning about taxonomic profiling + assembly + binning.
        """
        prompt = (
            "I have shotgun metagenomic sequencing data from a soil sample. "
            "How can I figure out what organisms are present and their relative abundances?"
        )

        response = await self._query_router(prompt)

        quality_score = await self._evaluate_response(
            response=response,
            rubric=(
                "Response should mention:\n"
                "1. Taxonomic profiling (Kraken2, MetaPhlAn, Kaiju, or Sylph for quick abundance estimates)\n"
                "2. Assembly-based approach (MEGAHIT, metaSPAdes for contigs)\n"
                "3. Binning (MaxBin, MetaBAT to group contigs into MAGs)\n"
                "4. Annotation of bins (CheckM for quality, prokka/DRAM for genes)\n"
                "5. Trade-offs: profiling (fast) vs assembly (detailed)\n"
                "6. Galaxy tools if available (or general workflow)"
            ),
            min_score=0.7,
        )

        assert quality_score >= 0.7, f"Response quality too low: {quality_score}"

    @pytest.mark.asyncio
    async def test_somatic_variant_calling(self):
        """7.6 Somatic variant calling (tumor/normal).

        Goal: Ensure the agent outlines an appropriate variant-calling pipeline.
        """
        prompt = (
            "I have sequencing data from a tumor and its matched normal sample. "
            "How do I identify somatic variants between them?"
        )

        response = await self._query_router(prompt)

        quality_score = await self._evaluate_response(
            response=response,
            rubric=(
                "Response should outline:\n"
                "1. Alignment (BWA-MEM, Bowtie2)\n"
                "2. Pre-processing (duplicate marking, base recalibration - GATK)\n"
                "3. Somatic variant calling (Mutect2, VarScan, Strelka)\n"
                "4. Filtering (remove germline variants, low-quality calls)\n"
                "5. Annotation (VEP, ANNOVAR for functional impact)\n"
                "6. Mention of tumor-normal paired analysis importance"
            ),
            min_score=0.7,
        )

        assert quality_score >= 0.7, f"Response quality too low: {quality_score}"

    @pytest.mark.asyncio
    async def test_general_onboarding(self):
        """7.7 'What should I do next?' general onboarding.

        Goal: Evaluate clarification, data-typing, and analytical guidance.
        """
        prompt = (
            "I just got my sequencing data back, but I'm not sure where to begin analyzing it. "
            "What should I do first?"
        )

        response = await self._query_router(prompt)

        quality_score = await self._evaluate_response(
            response=response,
            rubric=(
                "Response should:\n"
                "1. Ask clarifying questions (data type: RNA-seq, WGS, scRNA-seq, etc.)\n"
                "2. Suggest starting with QC (FastQC, MultiQC)\n"
                "3. Mention checking data format and quality\n"
                "4. Provide general overview of typical workflows based on data type\n"
                "5. Be helpful and not overwhelming\n"
                "6. Offer to provide more specific guidance once data type is known"
            ),
            min_score=0.7,
        )

        assert quality_score >= 0.7, f"Response quality too low: {quality_score}"

    @pytest.mark.asyncio
    async def test_coverage_anomalies(self):
        """7.8 Coverage anomalies & artifacts.

        Goal: Test recognition of common sequencing artifacts.
        """
        prompt = (
            "My coverage plot looks uneven across the genome. "
            "What could be causing this, and how can I investigate further?"
        )

        response = await self._query_router(prompt)

        quality_score = await self._evaluate_response(
            response=response,
            rubric=(
                "Response should mention possible causes:\n"
                "1. PCR duplicates (use Picard MarkDuplicates)\n"
                "2. GC bias (use tools like deepTools or Picard CollectGcBiasMetrics)\n"
                "3. Copy number variations (if cancer/tumor sample)\n"
                "4. Library preparation artifacts\n"
                "5. Alignment issues (mappability)\n"
                "6. Suggested diagnostic tools: IGV for visualization, deepTools for metrics\n"
                "7. Quality control metrics to check"
            ),
            min_score=0.7,
        )

        assert quality_score >= 0.7, f"Response quality too low: {quality_score}"

    # ── Helper methods ────────────────────────────────────────────────────────

    async def _query_router(self, prompt: str) -> str:
        """Send prompt to Router agent and return response content."""
        start_time = time.time()
        response = self._post(
            "/api/ai/agents/query", data={"query": prompt, "agent_type": "router"}, json=True
        )
        # Retry once on 500 — often caused by transient Anthropic API rate limits
        if response.status_code == 500:
            time.sleep(5)
            response = self._post(
                "/api/ai/agents/query", data={"query": prompt, "agent_type": "router"}, json=True
            )
        query_duration = time.time() - start_time

        self._assert_status_code_is(response, 200)
        result = response.json()

        self._test_metrics["query_duration_ms"] = int(query_duration * 1000)
        self._test_metrics["prompt"] = prompt
        self._test_metrics["agent_response"] = result["response"]["content"]
        self._test_metrics["agent_type"] = result["response"].get("agent_type", "router")

        # Capture orchestrator/router planning metadata if present
        agent_resp = result.get("response", {})
        if isinstance(agent_resp, dict):
            metadata = agent_resp.get("metadata", {})
            if metadata.get("agents_used"):
                self._test_metrics["orchestrator_agents_used"] = metadata["agents_used"]
                self._test_metrics["orchestrator_execution_type"] = metadata.get("execution_type", "unknown")
            if metadata.get("method"):
                self._test_metrics["routing_method"] = metadata["method"]
            handoff = metadata.get("handoff_info", {})
            if handoff:
                self._test_metrics["handoff_info"] = handoff

        if "usage" in result:
            self._test_metrics["agent_tokens_input"] = result["usage"].get("input_tokens", 0)
            self._test_metrics["agent_tokens_output"] = result["usage"].get("output_tokens", 0)

        return result["response"]["content"]

    async def _evaluate_response(self, response: str, rubric: str, min_score: float) -> float:
        """Evaluate response quality using LLM judge (Claude Opus 4.6).

        Returns a score between 0.0 and 1.0.
        Skips the test (instead of failing) on rate limits or timeouts.
        """
        judge_api_key = (
            getattr(self._app.config, "agent_eval_judge_api_key", None)
            or os.environ.get("ANTHROPIC_API_KEY")
            or getattr(self._app.config, "ai_api_key", None)
        )
        if not judge_api_key:
            pytest.skip(
                "No API key available for judge evaluation. Set agent_eval_judge_api_key "
                "in galaxy.yml or ANTHROPIC_API_KEY environment variable"
            )

        if not hasattr(self, "_judge_client") or self._judge_client is None:
            self._judge_client = Anthropic(api_key=judge_api_key)

        judge_model = getattr(self._app.config, "agent_eval_judge_model", None) or "claude-opus-4-6"

        judge_prompt = f"""You are an expert evaluator of AI agent responses for bioinformatics workflows.

Evaluate the following agent response against this rubric:

{rubric}

Agent Response:
{response}

Provide a score from 0.0 to 1.0, where:
- 1.0 = Excellent, comprehensive, accurate response covering all key points
- 0.7-0.9 = Good response covering most key points with minor gaps
- 0.5-0.7 = Adequate response but missing some important points
- < 0.5 = Poor response with major gaps or inaccuracies

Respond with ONLY a JSON object: {{"score": 0.X, "reasoning": "brief explanation"}}"""

        start_time = time.time()
        try:
            message = self._judge_client.messages.create(
                model=judge_model,
                max_tokens=500,
                messages=[{"role": "user", "content": judge_prompt}],
            )
        except RateLimitError as e:
            pytest.skip(f"Judge API rate limited — test inconclusive: {e}")
        except APITimeoutError as e:
            pytest.skip(f"Judge API timeout — test inconclusive: {e}")
        except APIError as e:
            pytest.fail(f"Judge API error: {e}")

        judge_duration = time.time() - start_time

        try:
            judge_result = json.loads(message.content[0].text)
            score = float(judge_result["score"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            pytest.fail(f"Judge returned invalid response: {e}\nRaw: {message.content[0].text}")

        self._test_metrics["judge_duration_ms"] = int(judge_duration * 1000)
        self._test_metrics["judge_model"] = judge_model
        self._test_metrics["quality_score"] = score
        self._test_metrics["judge_reasoning"] = judge_result.get("reasoning", "")
        self._test_metrics["rubric"] = rubric
        self._test_metrics["min_score"] = min_score

        if hasattr(message, "usage"):
            self._test_metrics["judge_tokens_input"] = message.usage.input_tokens
            self._test_metrics["judge_tokens_output"] = message.usage.output_tokens

        return score

    def tearDown(self):
        """Clean up judge client before base tearDown saves the report."""
        if hasattr(self, "_judge_client") and self._judge_client is not None:
            del self._judge_client
            self._judge_client = None
        super().tearDown()
