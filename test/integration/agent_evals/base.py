"""Shared base class for all agent evaluation tests."""
import json
import os
import time
from pathlib import Path

import yaml
from galaxy_test.driver.integration_util import IntegrationTestCase

from .eval_utils import calculate_model_cost

_EVAL_CONFIG_KEYS = frozenset({
    "ai_model", "ai_api_key", "ai_api_base_url",
    "agent_eval_judge_model", "agent_eval_judge_api_key",
    "agent_eval_tool_source_url",
    "inference_services",
})


class AgentEvalTestCase(IntegrationTestCase):
    """Base class for Galaxy agent evaluation tests.

    Provides shared setUp/tearDown, Galaxy config, and report saving so that
    individual test files only need to define test methods.
    """

    def setUp(self):
        super().setUp()
        self._test_start_time = time.time()
        self._test_metrics = {}
        self._test_category = self.__class__.__module__.split(".")[-1].replace("test_", "")
        self._test_class = self.__class__.__name__

    @classmethod
    def _load_local_eval_config(cls) -> dict:
        """Load eval settings from local config/galaxy.yml or config/agent_eval.yml.

        Returns only the keys relevant to agent evaluation, ignoring everything else.
        Returns an empty dict if no config file is found.
        """
        for path in [Path("config/galaxy.yml"), Path("config/agent_eval.yml")]:
            if path.exists():
                raw = yaml.safe_load(path.read_text()) or {}
                # Galaxy config files wrap all settings under a top-level "galaxy:" key
                if "galaxy" in raw:
                    raw = raw["galaxy"]
                return {k: v for k, v in raw.items() if k in _EVAL_CONFIG_KEYS and v}
        return {}

    @classmethod
    def handle_galaxy_config_kwds(cls, config):
        """Configure Galaxy with AI agent settings for evaluation.

        Resolution order: environment variable → config/galaxy.yml → built-in default.
        Env vars always win so CI overrides work correctly.
        """
        local = cls._load_local_eval_config()

        config["ai_model"] = (
            os.environ.get("GALAXY_TEST_AI_MODEL")
            or local.get("ai_model")
            or "anthropic:claude-haiku-4-5"
        )
        config["agent_eval_tool_source_url"] = (
            os.environ.get("AGENT_EVAL_TOOL_SOURCE_URL")
            or local.get("agent_eval_tool_source_url")
            or "https://usegalaxy.org"
        )

        if api_key := os.environ.get("GALAXY_TEST_AI_API_KEY") or local.get("ai_api_key"):
            config["ai_api_key"] = api_key
        if base_url := os.environ.get("GALAXY_TEST_AI_API_BASE_URL") or local.get("ai_api_base_url"):
            config["ai_api_base_url"] = base_url
        if judge_model := local.get("agent_eval_judge_model"):
            config["agent_eval_judge_model"] = judge_model
        if judge_key := local.get("agent_eval_judge_api_key"):
            config["agent_eval_judge_api_key"] = judge_key
        if inference_services := local.get("inference_services"):
            # Drop entries whose model uses a different provider than ai_model.
            # Galaxy has one ai_api_key shared across all agents; mixing providers
            # (e.g. anthropic: override when ai_model is openai:) silently breaks auth.
            primary_model = config.get("ai_model", "")
            primary_provider = primary_model.split(":")[0] if ":" in primary_model else None
            if primary_provider:
                compatible = {
                    name: svc_cfg
                    for name, svc_cfg in inference_services.items()
                    if not (isinstance(svc_cfg, dict) and ":" in svc_cfg.get("model", ""))
                    or svc_cfg.get("model", "").split(":")[0] == primary_provider
                }
            else:
                compatible = inference_services
            if compatible:
                config["inference_services"] = compatible

    def _save_test_report(self, test_name: str, status: str, error_message: str = None) -> None:
        """Save test results as JSON report for the dashboard."""
        reports_dir = Path("test-reports")
        reports_dir.mkdir(exist_ok=True)

        duration_ms = int((time.time() - self._test_start_time) * 1000)

        agent_tokens_in = self._test_metrics.get("agent_tokens_input", 0)
        agent_tokens_out = self._test_metrics.get("agent_tokens_output", 0)
        judge_tokens_in = self._test_metrics.get("judge_tokens_input", 0)
        judge_tokens_out = self._test_metrics.get("judge_tokens_output", 0)

        agent_model = getattr(self._app.config, "ai_model", "claude-sonnet-4-5")
        judge_model = self._test_metrics.get("judge_model", "claude-opus-4-6")

        agent_cost = calculate_model_cost(agent_model, agent_tokens_in, agent_tokens_out)
        judge_cost = calculate_model_cost(judge_model, judge_tokens_in, judge_tokens_out)
        total_cost = agent_cost + judge_cost

        # Derive test_file from the subclass module name so each report
        # correctly identifies which file it came from.
        test_file = self.__class__.__module__.split(".")[-1] + ".py"

        report = {
            "test_name": test_name,
            "test_class": getattr(self, "_test_class", "Unknown"),
            "test_category": getattr(self, "_test_category", "unknown"),
            "test_file": test_file,
            "run_id": getattr(self, "_agent_eval_run_id", "unknown"),
            "agent_model": agent_model,
            "judge_model": judge_model,
            "tool_source_url": getattr(self._app.config, "agent_eval_tool_source_url", None),
            "status": status,
            "duration_ms": duration_ms,
            "timestamp": time.time(),
            "tokens_input": agent_tokens_in + judge_tokens_in,
            "tokens_output": agent_tokens_out + judge_tokens_out,
            "cost": total_cost,
            **self._test_metrics,
        }

        if error_message:
            report["error"] = error_message

        report["detailed_metrics"] = {
            "agent_tokens": {"input": agent_tokens_in, "output": agent_tokens_out},
            "judge_tokens": {"input": judge_tokens_in, "output": judge_tokens_out},
            "costs": {
                "agent_cost": agent_cost,
                "judge_cost": judge_cost,
                "total_cost": total_cost,
            },
        }

        report_file = reports_dir / f"{test_name}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        if hasattr(self, "_report_manager"):
            category = report.get("test_category", "unknown")
            self._report_manager.save_report(category, test_name, report)

    def tearDown(self):
        """Save test report after each test."""
        test_name = getattr(self, "_current_test_name", "unknown_test")

        status = "PASSED"
        error_msg = None

        if hasattr(self, "_outcome"):
            result = self._outcome.result
            if result.failures or result.errors:
                status = "FAILED"
                if result.failures:
                    error_msg = str(result.failures[-1][1])
                elif result.errors:
                    error_msg = str(result.errors[-1][1])

        if status == "PASSED" and "quality_score" in self._test_metrics and "min_score" in self._test_metrics:
            quality_score = self._test_metrics["quality_score"]
            min_score = self._test_metrics["min_score"]
            if quality_score < min_score:
                status = "FAILED"
                error_msg = f"Quality score {quality_score} below threshold {min_score}"

        self._save_test_report(test_name, status, error_msg)
        super().tearDown()
