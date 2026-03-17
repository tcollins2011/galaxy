#!/usr/bin/env python3
"""Run agent evaluations against multiple models and generate a comparison dashboard.

Model list resolution order:
  1. GALAXY_TEST_AI_MODELS environment variable (comma-separated model names)
  2. agent_eval_models key in config/galaxy.yml or config/agent_eval.yml
  3. Single GALAXY_TEST_AI_MODEL / default (runs as a normal single-model eval)

galaxy.yml supports both string entries (uses global ai_api_key) and object entries
(per-model api_key for cross-provider comparisons):

  agent_eval_models:
    - "anthropic:claude-haiku-4-5"          # uses global ai_api_key
    - model: "openai:gpt-4o-mini"
      api_key: "sk-openai-..."              # per-model key
    - model: "google:gemini-2.0-flash"
      api_key: "AIza..."                    # per-model key

Examples:
  # Via galaxy.yml (supports per-model api_key)
  python scripts/run_multi_model_eval.py

  # Via env var (uses global ai_api_key for all)
  GALAXY_TEST_AI_MODELS="anthropic:claude-haiku-4-5,openai:gpt-4o-mini" python scripts/run_multi_model_eval.py

  # Pass pytest args through
  python scripts/run_multi_model_eval.py -k test_scrna
"""
import os
import subprocess
import sys
from pathlib import Path


def _load_local_models() -> list[dict]:
    """Read agent_eval_models from config/galaxy.yml or config/agent_eval.yml.

    Returns a list of dicts with 'model' and optional 'api_key' keys.
    """
    try:
        import yaml
    except ImportError:
        return []
    for path in [Path("config/galaxy.yml"), Path("config/agent_eval.yml")]:
        if path.exists():
            raw = yaml.safe_load(path.read_text()) or {}
            if "galaxy" in raw:
                raw = raw["galaxy"]
            models = raw.get("agent_eval_models")
            if models and isinstance(models, list):
                result = []
                for m in models:
                    if isinstance(m, str) and m:
                        result.append({"model": m})
                    elif isinstance(m, dict) and m.get("model"):
                        result.append({"model": m["model"], "api_key": m.get("api_key")})
                return result
    return []


def load_models() -> list[dict]:
    """Determine the list of models to evaluate.

    Returns a list of dicts with 'model' and optional 'api_key' keys.
    """
    if env_models := os.environ.get("GALAXY_TEST_AI_MODELS"):
        return [{"model": m.strip()} for m in env_models.split(",") if m.strip()]
    if local_models := _load_local_models():
        return local_models
    return [{"model": os.environ.get("GALAXY_TEST_AI_MODEL", "anthropic:claude-haiku-4-5")}]


def run_eval(entry: dict, extra_args: list[str]) -> int:
    """Run pytest for a single model entry. Returns the exit code."""
    model = entry["model"]
    env = {**os.environ, "GALAXY_TEST_AI_MODEL": model}
    if api_key := entry.get("api_key"):
        env["GALAXY_TEST_AI_API_KEY"] = api_key

    cmd = [
        sys.executable, "-m", "pytest",
        "test/integration/agent_evals/",
        "-m", "requires_llm",
        "-v",
        *extra_args,
    ]
    print(f"\n{'='*60}")
    print(f"  Model: {model}")
    if entry.get("api_key"):
        print(f"  API Key: (per-model key)")
    print(f"  Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    result = subprocess.run(cmd, env=env)
    return result.returncode


def main() -> None:
    # Anything after "--" is passed through to pytest
    extra_pytest_args = sys.argv[1:]

    models = load_models()
    print(f"Running agent evals for {len(models)} model(s):", flush=True)
    for entry in models:
        key_note = " (per-model key)" if entry.get("api_key") else ""
        print(f"  - {entry['model']}{key_note}", flush=True)

    exit_codes: dict[str, int] = {}
    for entry in models:
        exit_codes[entry["model"]] = run_eval(entry, extra_pytest_args)

    print(f"\n{'='*60}", flush=True)
    print("Results summary:", flush=True)
    any_failed = False
    for model, code in exit_codes.items():
        status = "PASSED" if code == 0 else "FAILED"
        if code != 0:
            any_failed = True
        print(f"  {status}  {model}", flush=True)
    print(f"{'='*60}\n", flush=True)

    print("Generating dashboards for all runs...", flush=True)
    subprocess.run([sys.executable, "scripts/agent_eval_dashboard.py", "--all-runs"])

    sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
