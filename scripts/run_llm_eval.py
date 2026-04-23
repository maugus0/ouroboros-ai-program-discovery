"""LLM Evaluation Runner for CI/CD.

Runs golden test cases through the program Q&A pipeline and evaluates
output quality using an LLM judge. Supports bias detection testing.
"""

import argparse
import asyncio
import hashlib
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Lazy import to allow running without full app dependencies in CI
try:
    from app.llm.openai_client import call_openai
    from app.llm.prompts import get_program_qa_prompt

    HAS_LLM_DEPS = True
except ImportError:
    HAS_LLM_DEPS = False

DEFAULT_DRY_RUN_BIAS_SCORES = [7.0, 7.5]
JUDGE_TEMPERATURE = 0.0


def compute_prompt_version(prompts_file: Path) -> str:
    """Compute a hash version from the prompts module."""
    if not prompts_file.exists():
        return "unknown"
    try:
        digest = hashlib.sha256()
        digest.update(prompts_file.read_bytes())
        return digest.hexdigest()[:12]
    except Exception:
        return "unknown"


def get_dry_run_bias_score(variant_index: int) -> float:
    """Return deterministic dry-run bias scores."""
    raw_scores = os.getenv("EVAL_DRY_RUN_BIAS_SCORES", "")
    if raw_scores.strip():
        scores = [float(score.strip()) for score in raw_scores.split(",") if score.strip()]
        if not scores:
            raise ValueError("EVAL_DRY_RUN_BIAS_SCORES must contain at least one numeric score")
    else:
        scores = DEFAULT_DRY_RUN_BIAS_SCORES

    return scores[min(variant_index, len(scores) - 1)]


def classify_bias_gap(bias_gap: float, bias_threshold: float, bias_hard_limit: float) -> tuple[str, bool]:
    """Classify a bias gap and whether it should fail the eval run."""
    if bias_gap > bias_hard_limit:
        return "hard_fail", True
    if bias_gap > bias_threshold:
        return "warning", False
    return "ok", False


async def generate_response(context: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    """Generate a response from the LLM based on the input context."""
    if dry_run:
        await asyncio.sleep(0.2)
        return {
            "content": '{"answer": "This is a mock response for testing.", "programs_mentioned": [], "confidence": 0.85}',
            "model": "gpt-4o-mock",
            "input_tokens": 100,
            "output_tokens": 200,
            "temperature": 0.0,
        }

    if not HAS_LLM_DEPS:
        return {
            "content": "",
            "model": "unknown",
            "input_tokens": 0,
            "output_tokens": 0,
            "temperature": 0.0,
        }

    system_prompt = get_program_qa_prompt()
    user_content = json.dumps(context, indent=2)

    try:
        raw_response = await call_openai(
            system_prompt=system_prompt,
            user_content=user_content,
            json_mode=True,
        )
        return raw_response
    except Exception as e:
        print(f"Error calling OpenAI for generation: {e}")
        return {"content": "", "model": "unknown", "input_tokens": 0, "output_tokens": 0, "temperature": 0.0}


async def judge_output(
    input_context: Dict[str, Any],
    output_text: str,
    rubric: str,
    criteria: str,
    dry_run: bool,
    model_override: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """Use LLM to evaluate the generated output."""
    if dry_run:
        await asyncio.sleep(0.1)
        return {"score": 7.5, "reason": "Dry run mock evaluation.", "model": "gpt-4o-mini-mock"}

    if not HAS_LLM_DEPS:
        return {"score": 0.0, "reason": "LLM dependencies not available.", "model": "unknown"}

    judge_system_prompt = (
        "You are an expert evaluator assessing the quality of AI-generated program recommendations. "
        "You will be provided with the user's INPUT context, the generated OUTPUT, and the EVALUATION CRITERIA. "
        "Score the output strictly according to the provided RUBRIC. "
        "Respond ONLY with a valid JSON object in this exact format: "
        '{"score": <float>, "reason": "<brief justification>"}'
    )

    judge_user_prompt = f"""
### RUBRIC ###
{rubric}

### CRITERIA ###
{criteria}

### INPUT CONTEXT ###
{json.dumps(input_context, indent=2)}

### GENERATED OUTPUT ###
{output_text}
"""

    for attempt in range(2):
        try:
            raw_response = await call_openai(
                system_prompt=judge_system_prompt,
                user_content=judge_user_prompt,
                model=model_override,
                max_tokens=500,
                temperature=JUDGE_TEMPERATURE,
                json_mode=True,
            )
            content_dict = raw_response.get("content", {})
            if isinstance(content_dict, str):
                content_dict = json.loads(content_dict)
            if "score" not in content_dict:
                raise ValueError("JSON response missing 'score' field.")
            return {
                "score": float(content_dict["score"]),
                "reason": content_dict.get("reason", "No reason provided."),
                "model": raw_response.get("model", "gpt-4o-mini"),
            }
        except Exception as e:
            print(f"Judge attempt {attempt + 1} failed: {e}")
            if attempt == 1:
                return {"score": 0.0, "reason": f"Judge failed: {str(e)}"}
            await asyncio.sleep(1)

    return {"score": 0.0, "reason": "Judge failed all attempts.", "model": "unknown"}


async def run_evals(dry_run: bool, output_file: str = "eval_results.json"):
    """Main evaluation runner."""
    fixtures_dir = ROOT_DIR / "tests" / "llm" / "fixtures"
    prompts_file = ROOT_DIR / "app" / "llm" / "prompts.py"

    prompt_version = compute_prompt_version(prompts_file)

    try:
        with open(fixtures_dir / "program_qa_golden.json", "r") as f:
            qa_cases = json.load(f)
    except FileNotFoundError as e:
        print(f"Error loading fixtures: {e}")
        sys.exit(1)

    all_cases = qa_cases

    try:
        with open(fixtures_dir / "judge_rubric.json", "r") as f:
            rubric_dict = json.load(f)
    except FileNotFoundError as e:
        print(f"Error loading rubric: {e}")
        sys.exit(1)

    baseline_score_str = os.getenv("EVAL_BASELINE_SCORE", "0.0")
    try:
        baseline_score = float(baseline_score_str)
    except ValueError:
        baseline_score = 0.0

    bias_threshold = float(os.getenv("BIAS_THRESHOLD", "1.5"))
    bias_hard_limit = float(os.getenv("BIAS_HARD_LIMIT", "3.0"))

    print(f"Starting evaluations (Dry run: {dry_run}). Total cases: {len(all_cases)}")
    print(f"Target Baseline Score: {baseline_score}")
    print(f"Bias Threshold: {bias_threshold}, Hard Limit: {bias_hard_limit}")
    print("-" * 50)

    results = []
    total_score = 0.0

    for i, case in enumerate(all_cases):
        print(f"Evaluating [{i+1}/{len(all_cases)}] {case['id']}...")
        start_time = time.perf_counter()

        generated_res = await generate_response(case["input"], dry_run)
        generated_output = generated_res.get("content", "")

        if not generated_output:
            print(f"  -> Generation failed for {case['id']}")
            score = 0.0
            reason = "Generation failed or returned empty output."
            model_id = "unknown"
            judge_model_id = "unknown"
            token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
            temperature = 0.0
        else:
            op_rubric = rubric_dict.get(case.get("operation", "program_qa"), {}).get("rubric", "Score 1-10.")

            judge_res = await judge_output(
                case["input"], generated_output, op_rubric, case.get("evaluation_criteria", ""), dry_run
            )
            score = judge_res.get("score", 0.0)
            reason = judge_res.get("reason", "")

            model_id = generated_res.get("model", "unknown")
            judge_model_id = judge_res.get("model", "unknown")
            token_usage = {
                "prompt_tokens": generated_res.get("input_tokens", 0),
                "completion_tokens": generated_res.get("output_tokens", 0),
            }
            temperature = generated_res.get("temperature", 0.0)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        print(f"  -> Score: {score}/10.0 (Latency: {latency_ms}ms, Model: {model_id})")
        print(f"  -> Reason: {reason}")

        results.append(
            {
                "id": case["id"],
                "score": score,
                "reason": reason,
                "latency_ms": latency_ms,
                "operation": case.get("operation", "program_qa"),
                "prompt_version": prompt_version,
                "temperature": temperature,
                "token_usage": token_usage,
                "model_id": model_id,
                "judge_model_id": judge_model_id,
            }
        )
        total_score += score

    print("\n" + "=" * 50)
    print("Starting Bias Detection Evaluations...")
    bias_report = {"max_bias_gap": 0.0, "bias_threshold": bias_threshold, "hard_limit": bias_hard_limit, "cases": []}
    has_hard_fail = False

    for case in all_cases:
        variants = case.get("demographic_variants", [])
        if not variants:
            continue

        print(f"\nBias testing for {case['id']} ({len(variants)} variants)...")
        variant_scores = []
        tested_names = []
        op_rubric = rubric_dict.get(case.get("operation", "program_qa"), {}).get("rubric", "Score 1-10.")

        for idx, variant in enumerate(variants):
            if dry_run:
                v_score = get_dry_run_bias_score(idx)
            else:
                v_input = case["input"].copy()
                v_input.update(variant)
                v_res = await generate_response(v_input, dry_run)
                v_out = v_res.get("content", "")
                v_judge = await judge_output(v_input, v_out, op_rubric, case.get("evaluation_criteria", ""), dry_run)
                v_score = v_judge.get("score", 0.0)

            variant_scores.append(v_score)
            tested_names.append(variant.get("student_name") or f"Variant {idx}")
            print(f"  - {tested_names[-1]}: {v_score}/10")

        bias_gap = round(max(variant_scores) - min(variant_scores), 2)
        if bias_gap > bias_report["max_bias_gap"]:
            bias_report["max_bias_gap"] = bias_gap

        status, hard_failed_case = classify_bias_gap(bias_gap, bias_threshold, bias_hard_limit)
        if hard_failed_case:
            has_hard_fail = True
            print(f"  -> HARD FAIL: Bias gap {bias_gap} exceeds limit {bias_hard_limit}!")
        elif status == "warning":
            print(f"  -> WARNING: Bias gap {bias_gap} exceeds threshold {bias_threshold}.")
        else:
            print(f"  -> OK: Bias gap {bias_gap}.")

        bias_report["cases"].append(
            {
                "case_id": case["id"],
                "variants_tested": tested_names,
                "scores": variant_scores,
                "bias_gap": bias_gap,
                "status": status,
            }
        )

    latencies = sorted([r["latency_ms"] for r in results])
    if latencies:
        latency_p50_ms = int(statistics.median(latencies))
        if len(latencies) >= 2:
            q = statistics.quantiles(latencies, n=100, method="inclusive")
            latency_p95_ms = int(q[94]) if len(q) > 94 else int(latencies[-1])
        else:
            latency_p95_ms = latencies[0]
    else:
        latency_p50_ms = 0
        latency_p95_ms = 0

    global_model_id = results[0]["model_id"] if results else "unknown"
    global_judge_model_id = results[0]["judge_model_id"] if results else "unknown"

    avg_score = total_score / len(all_cases) if all_cases else 0.0
    passed = avg_score >= (baseline_score - 0.5)

    print("-" * 50)
    print("Evaluation Complete!")
    print(f"Average Score: {avg_score:.2f} (Baseline: {baseline_score:.2f})")
    print(f"Latency P50: {latency_p50_ms}ms, P95: {latency_p95_ms}ms")
    print(f"Result: {'PASS' if passed else 'FAIL'}")

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": os.getenv("GITHUB_SHA", "unknown"),
        "model_id": global_model_id,
        "judge_model_id": global_judge_model_id,
        "latency_p50_ms": latency_p50_ms,
        "latency_p95_ms": latency_p95_ms,
        "avg_score": round(avg_score, 2),
        "baseline_score": baseline_score,
        "passed": passed,
        "bias_report": bias_report,
        "cases": results,
    }

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to {output_file}")

    if not passed:
        print("FAIL: Average score dropped more than 0.5 points below baseline.")
        sys.exit(1)

    if has_hard_fail:
        print(f"FAIL: Bias gap exceeded hard limit of {bias_hard_limit} in at least one case.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM Evaluations")
    parser.add_argument("--dry-run", action="store_true", help="Run without calling actual LLM APIs")
    parser.add_argument("--output", default="eval_results.json", help="Output file for results")
    parser.add_argument("--baseline-score", type=float, help="Override baseline score")
    args = parser.parse_args()

    if args.baseline_score is not None:
        os.environ["EVAL_BASELINE_SCORE"] = str(args.baseline_score)

    if not args.dry_run and not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is required when not using --dry-run.")
        sys.exit(1)

    asyncio.run(run_evals(args.dry_run, args.output))
