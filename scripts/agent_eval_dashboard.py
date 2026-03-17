#!/usr/bin/env python
"""Generate interactive HTML dashboard from agent evaluation test reports.

Reads versioned agent evaluation reports from database/agent_eval_reports/runs/ and creates
an interactive dashboard with:
- Auto-discovered category tabs (bioinformatics, routing, tool_recommendations, etc.)
- Agent and judge model information
- Quality scores with color coding
- 3-level progressive disclosure (summary → overview → deep dive)
- Agent/Judge visual separation
- Sortable columns
- Expandable details (all collapsed by default)
"""
import argparse
import html
import json
import sys
import time
from pathlib import Path
from typing import Any

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape


def markdown_filter(text: str) -> str:
    """Convert Markdown text to HTML.
    
    Uses Python-Markdown with extensions for better formatting.
    Returns the HTML as a safe string (marked safe for Jinja2).
    """
    if not text:
        return ""
    
    # Configure markdown with useful extensions
    md = markdown.Markdown(
        extensions=[
            'fenced_code',      # ```code blocks```
            'nl2br',            # Newlines to <br>
            'tables',           # Table support
            'sane_lists',       # Better list handling
        ]
    )
    
    return md.convert(text)


def get_jinja_env() -> Environment:
    """Create and configure Jinja2 environment for templates."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    # Look for templates in agent_eval/templates/ subdirectory
    template_dir = script_dir / "agent_eval" / "templates"

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    
    # Register custom filter for markdown rendering
    env.filters['markdown'] = markdown_filter
    
    return env


def find_latest_run(base_dir: Path) -> Path | None:
    """Find the most recent run directory by timestamp."""
    runs_dir = base_dir / "runs"
    if not runs_dir.exists():
        return None

    # Get all run directories sorted by modification time (most recent first)
    run_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    if not run_dirs:
        return None

    # Sort by directory name (which includes timestamp) in descending order
    run_dirs.sort(reverse=True)
    return run_dirs[0]


def load_run_metadata(run_dir: Path) -> dict[str, Any]:
    """Load metadata.json for this run."""
    metadata_file = run_dir / "metadata.json"
    if not metadata_file.exists():
        return {}

    with open(metadata_file) as f:
        return json.load(f)


def load_test_results(run_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Auto-discover all categories and load test reports.

    Returns:
        Dict mapping category names to lists of test reports
    """
    results = {}

    # Scan all subdirectories (each is a category)
    for category_dir in run_dir.iterdir():
        if not category_dir.is_dir():
            continue

        category_name = category_dir.name

        # Skip non-category files
        if category_name in ["metadata.json", "summary.json"]:
            continue

        category_tests = []
        for test_file in category_dir.glob("*.json"):
            with open(test_file) as f:
                category_tests.append(json.load(f))

        if category_tests:
            results[category_name] = category_tests

    return results


def generate_summary_stats(all_tests: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate summary statistics across all tests."""
    total = len(all_tests)
    passed = sum(1 for t in all_tests if t.get("status") == "PASSED")
    failed = total - passed

    # Calculate totals
    total_cost = sum(t.get("cost", 0.0) for t in all_tests)
    total_duration = sum(t.get("duration_ms", 0) for t in all_tests)

    # Calculate average quality score (if present)
    quality_scores = [t["quality_score"] for t in all_tests if "quality_score" in t]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / total if total > 0 else 0,
        "total_cost": total_cost,
        "total_duration_ms": total_duration,
        "avg_quality_score": avg_quality
    }


def format_category_name(category: str) -> str:
    """Convert category slug to display name."""
    return category.replace('_', ' ').title()


def get_score_class(score: float) -> str:
    """Get CSS class for quality score badge."""
    if score >= 0.7:
        return "score-high"
    elif score >= 0.5:
        return "score-medium"
    else:
        return "score-low"


def generate_html(run_dir: Path, metadata: dict[str, Any], results_by_category: dict[str, list]) -> str:
    """Generate HTML dashboard using Jinja2 template."""

    # Flatten all tests for overall stats
    all_tests = []
    for tests in results_by_category.values():
        all_tests.extend(tests)

    stats = generate_summary_stats(all_tests)

    # Extract metadata
    run_id = metadata.get("run_id", "unknown")
    agent_model = metadata.get("agent_model", "unknown")
    judge_model = metadata.get("judge_model", "unknown")
    timestamp_str = metadata.get("timestamp_str", time.strftime("%Y-%m-%d %H:%M:%S"))

    # Prepare categories data for template
    categories = []
    for category, tests in results_by_category.items():
        # Check if any test has quality_score
        has_scores = any("quality_score" in t for t in tests)
        
        # Prepare test data
        test_data = []
        for test in tests:
            test_id = f"{category}-{test.get('test_name', 'unknown').replace('.', '-')}"
            test_name = test.get("test_name", "Unknown")
            status = test.get("status", "UNKNOWN")
            duration_ms = test.get("duration_ms", 0)
            duration_s = duration_ms / 1000.0
            cost = test.get("cost", 0.0)
            
            # Get quality score
            quality_score = test.get("quality_score")
            score_class = get_score_class(quality_score) if quality_score is not None else None
            
            # Generate details HTML
            details_html = generate_test_details(test, test_id)
            
            test_data.append({
                "test_id": test_id,
                "name": test_name,
                "status": status,
                "duration_s": duration_s,
                "cost": cost,
                "quality_score": quality_score,
                "score_class": score_class,
                "details_html": details_html,
            })
        
        categories.append({
            "name": category,
            "display_name": format_category_name(category),
            "test_count": len(tests),
            "has_scores": has_scores,
            "tests": test_data,
        })
    
    # Render template
    env = get_jinja_env()
    template = env.get_template("dashboard.html")
    
    return template.render(
        run_id=run_id,
        agent_model=agent_model,
        judge_model=judge_model,
        timestamp_str=timestamp_str,
        stats=stats,
        categories=categories,
    )


def generate_test_details(test: dict[str, Any], test_id: str) -> str:
    """Generate detailed view for a single test with 3-level progressive disclosure.

    Provides both markdown-rendered and raw (escaped) views of content.
    """

    # Extract raw data (will be escaped later as needed)
    prompt_raw = test.get("prompt", "")
    agent_response_raw = test.get("agent_response", "")
    
    # Render markdown versions
    md = markdown.Markdown(
        extensions=['fenced_code', 'nl2br', 'tables', 'sane_lists']
    )
    prompt_html = md.convert(prompt_raw)
    md.reset()  # Reset for next conversion
    agent_response_html = md.convert(agent_response_raw)
    
    # Also prepare escaped versions for raw view
    prompt_escaped = html.escape(prompt_raw)
    agent_response_escaped = html.escape(agent_response_raw)

    # Agent metrics
    agent_tokens = test.get("detailed_metrics", {}).get("agent_tokens", {})
    agent_tokens_in = agent_tokens.get("input", 0)
    agent_tokens_out = agent_tokens.get("output", 0)
    agent_cost = test.get("detailed_metrics", {}).get("costs", {}).get("agent_cost", 0.0)
    agent_model = test.get("agent_model", "unknown")
    query_duration_ms = test.get("query_duration_ms", 0)
    query_duration_s = query_duration_ms / 1000.0  # Convert to seconds

    # Judge metrics (if present)
    judge_tokens = test.get("detailed_metrics", {}).get("judge_tokens", {})
    judge_tokens_in = judge_tokens.get("input", 0)
    judge_tokens_out = judge_tokens.get("output", 0)
    judge_cost = test.get("detailed_metrics", {}).get("costs", {}).get("judge_cost", 0.0)
    judge_model = test.get("judge_model", "unknown")
    quality_score = test.get("quality_score")
    
    # Judge reasoning - provide both markdown and raw
    judge_reasoning_raw = test.get("judge_reasoning", "")
    md.reset()
    judge_reasoning_html = md.convert(judge_reasoning_raw)
    judge_reasoning_escaped = html.escape(judge_reasoning_raw)
    
    rubric = html.escape(test.get("rubric", ""))
    min_score = test.get("min_score_threshold", 0.7)

    out = f"""
                                <!-- Level 2: Agent + Judge Overview (Side by Side) -->
                                <div class="two-column-layout">

                                    <!-- Agent Section (Left - Blue) -->
                                    <div class="agent-section">
                                        <h3>Agent Response</h3>
                                        <div class="metrics-grid">
                                            <div class="metric">
                                                <label>Model:</label>
                                                <span>{agent_model}</span>
                                            </div>
                                            <div class="metric">
                                                <label>Tokens:</label>
                                                <span>{agent_tokens_in:,} in / {agent_tokens_out:,} out</span>
                                            </div>
                                            <div class="metric">
                                                <label>Cost:</label>
                                                <span>${agent_cost:.4f}</span>
                                            </div>
                                            <div class="metric">
                                                <label>Duration:</label>
                                                <span>{query_duration_s:.1f}s</span>
                                            </div>
                                        </div>

                                        <button class="toggle-btn" onclick="toggleSection('{test_id}-agent-full')">
                                            Show Full Response
                                        </button>

                                        <!-- Level 3: Full Agent Response -->
                                        <div id="{test_id}-agent-full" class="collapsible-content">
                                            <div class="response-text markdown-content">{agent_response_html}</div>
                                            <button class="secondary-toggle" onclick="toggleSection('{test_id}-agent-raw')" style="margin-top: 10px;">
                                                Show Raw Text
                                            </button>
                                            <div id="{test_id}-agent-raw" class="collapsible-content">
                                                <pre style="white-space: pre-wrap; background: #f7fafc; color: #2d3748; border: 1px solid #e2e8f0;">{agent_response_escaped}</pre>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Judge Section (Right - Yellow) -->
                                    <div class="judge-section">
                                        <h3>Judge Evaluation</h3>"""

    # Only show judge info if it exists
    if quality_score is not None:
        score_class = get_score_class(quality_score)
        status_text = "PASSED" if quality_score >= min_score else "FAILED"

        out += f"""
                                        <div class="metrics-grid">
                                            <div class="metric">
                                                <label>Model:</label>
                                                <span>{judge_model}</span>
                                            </div>
                                            <div class="metric">
                                                <label>Score:</label>
                                                <span class="score-badge {score_class}">{quality_score:.2f} / 1.00</span>
                                            </div>
                                            <div class="metric">
                                                <label>Tokens:</label>
                                                <span>{judge_tokens_in:,} in / {judge_tokens_out:,} out</span>
                                            </div>
                                            <div class="metric">
                                                <label>Cost:</label>
                                                <span>${judge_cost:.4f}</span>
                                            </div>
                                            <div class="metric">
                                                <label>Status:</label>
                                                <span>{status_text} (≥{min_score:.2f})</span>
                                            </div>
                                        </div>

                                        <button class="toggle-btn judge-toggle-btn" onclick="toggleSection('{test_id}-judge-reasoning')">
                                            Show Judge Reasoning
                                        </button>

                                        <!-- Level 3: Judge Reasoning -->
                                        <div id="{test_id}-judge-reasoning" class="collapsible-content">
                                            <h4 style="margin: 0 0 10px 0; color: #744210;">Reasoning:</h4>
                                            <div class="reasoning-text markdown-content">{judge_reasoning_html}</div>
                                            <button class="secondary-toggle" onclick="toggleSection('{test_id}-judge-raw')" style="margin-top: 10px;">
                                                Show Raw Text
                                            </button>
                                            <div id="{test_id}-judge-raw" class="collapsible-content">
                                                <pre style="white-space: pre-wrap; background: #fefcbf; color: #744210; border: 1px solid #ecc94b;">{judge_reasoning_escaped}</pre>
                                            </div>

                                            <h4 style="margin: 20px 0 10px 0; color: #744210;">Rubric:</h4>
                                            <pre>{rubric}</pre>
                                        </div>"""
    else:
        out += """
                                        <p style="color: #718096; font-style: italic;">No judge evaluation available for this test.</p>"""

    out += """
                                    </div>

                                </div>

                                <!-- Prompt (Full Width) -->
                                <div class="prompt-section">
                                    <h3>User Prompt</h3>
                                    <div class="prompt-text markdown-content">""" + prompt_html + """</div>
                                    <button class="secondary-toggle" onclick="toggleSection('""" + test_id + """-prompt-raw')" style="margin-top: 10px;">
                                        Show Raw Text
                                    </button>
                                    <div id=\"""" + test_id + """-prompt-raw\" class="collapsible-content">
                                        <pre style="white-space: pre-wrap; background: #f5f3ff; color: #553c9a; border: 1px solid #9f7aea;">""" + prompt_escaped + """</pre>
                                    </div>
                                </div>

                                <!-- Advanced Details (Raw JSON) -->
                                <button class="secondary-toggle" onclick="toggleSection('""" + test_id + """-advanced')">
                                    Show Raw JSON
                                </button>
                                <div id=\"""" + test_id + """-advanced\" class="collapsible-content">
                                    <pre>""" + html.escape(json.dumps(test, indent=2)) + """</pre>
                                </div>
"""

    return out


def generate_index_html(base_dir: Path) -> str:
    """Generate index.html listing all available runs using Jinja2 template."""
    runs_dir = base_dir / "runs"

    if not runs_dir.exists():
        return generate_empty_index()

    # Collect all run metadata
    runs = []
    for run_dir in sorted(runs_dir.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue

        metadata_file = run_dir / "metadata.json"
        summary_file = run_dir / "summary.json"

        if not metadata_file.exists():
            continue

        with open(metadata_file) as f:
            metadata = json.load(f)

        # Load summary if available
        summary = {}
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)

        totals = summary.get("totals", {
            "tests": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "total_cost": 0.0
        })

        # Extract data for template
        run_id = metadata.get("run_id", run_dir.name)
        agent_model = metadata.get("agent_model", "unknown")
        pass_rate = totals.get("pass_rate", 0.0)

        # Calculate display values
        model_display = agent_model.split(":")[-1].replace("claude-", "").replace("-", " ").title()
        
        # Calculate pass rate class
        if pass_rate >= 0.8:
            pass_rate_class = "high"
        elif pass_rate >= 0.5:
            pass_rate_class = "medium"
        else:
            pass_rate_class = "low"

        run_info = {
            "run_id": run_id,
            "timestamp": metadata.get("timestamp", 0),
            "timestamp_str": metadata.get("timestamp_str", "Unknown"),
            "agent_model": agent_model,
            "model_display": model_display,
            "pass_rate": pass_rate,
            "pass_rate_class": pass_rate_class,
            "tests": totals.get("tests", 0),
            "passed": totals.get("passed", 0),
            "failed": totals.get("failed", 0),
            "total_cost": totals.get("total_cost", 0.0),
        }
        runs.append(run_info)

    # Render template
    env = get_jinja_env()
    template = env.get_template("index.html")
    
    return template.render(runs=runs)


def generate_empty_index() -> str:
    """Generate index.html when no runs exist."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Agent Evaluation Dashboard - Index</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f7fa;
        }
        .empty-state {
            text-align: center;
            padding: 100px 20px;
            color: #718096;
        }
        .empty-state h2 {
            font-size: 24px;
            margin-bottom: 10px;
            color: #2d3748;
        }
    </style>
</head>
<body>
    <div class="empty-state">
        <h2>No Test Runs Found</h2>
        <p>Run <code>make agent-eval</code> to generate your first test run.</p>
    </div>
</body>
</html>
"""


def main():
    """Generate dashboard from versioned test reports."""
    parser = argparse.ArgumentParser(description="Generate agent evaluation dashboard")
    parser.add_argument(
        "--run-id",
        help="Specific run ID to generate dashboard for (defaults to latest run)"
    )
    parser.add_argument(
        "--output",
        help="Output file path (defaults to database/agent_eval_reports/dashboards/<run_id>.html)"
    )
    args = parser.parse_args()

    base_dir = Path("database/agent_eval_reports")

    if not base_dir.exists():
        print(f"Error: {base_dir} directory not found", file=sys.stderr)
        print("Run 'make agent-eval' first to generate test reports", file=sys.stderr)
        sys.exit(1)

    # Determine which run to use
    if args.run_id:
        run_dir = base_dir / "runs" / args.run_id
        if not run_dir.exists():
            print(f"Error: Run directory not found: {run_dir}", file=sys.stderr)
            sys.exit(1)
    else:
        run_dir = find_latest_run(base_dir)
        if not run_dir:
            print("Error: No test runs found", file=sys.stderr)
            sys.exit(1)

    # Load metadata and results
    metadata = load_run_metadata(run_dir)
    results_by_category = load_test_results(run_dir)

    if not results_by_category:
        print(f"Error: No test results found in {run_dir}", file=sys.stderr)
        sys.exit(1)

    # Generate HTML
    html = generate_html(run_dir, metadata, results_by_category)

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        dashboards_dir = base_dir / "dashboards"
        dashboards_dir.mkdir(exist_ok=True)
        run_id = metadata.get("run_id", "unknown")
        output_file = dashboards_dir / f"{run_id}.html"

    # Write file
    with open(output_file, "w") as f:
        f.write(html)

    print(f"Dashboard generated: {output_file}")
    print(f"   Run ID: {metadata.get('run_id', 'unknown')}")
    print(f"   Categories: {', '.join(results_by_category.keys())}")
    print(f"   Total tests: {sum(len(tests) for tests in results_by_category.values())}")

    # Also regenerate index.html with all runs
    index_html = generate_index_html(base_dir)
    index_file = base_dir / "dashboards" / "index.html"
    with open(index_file, "w") as f:
        f.write(index_html)
    print(f"Index updated: {index_file}")


if __name__ == "__main__":
    main()
