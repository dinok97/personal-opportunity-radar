from pathlib import Path
import json
import pandas as pd

# Folder structure:
# evaluation/
#   data/cv_related_QA.csv
#   results/
#   src/evaluate_cv_qa.py

EVALUATION_DIR = Path(__file__).resolve().parents[1]
INPUT_CSV = EVALUATION_DIR / "data" / "cv_related_QA.csv"
RESULTS_DIR = EVALUATION_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SCORING_CSV = RESULTS_DIR / "cv_qa_scoring.csv"
SUMMARY_CSV = RESULTS_DIR / "cv_qa_metrics_by_question.csv"
SUMMARY_JSON = RESULTS_DIR / "cv_qa_metrics_summary.json"


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Input CSV not found: {INPUT_CSV}\n"
            "Check that evaluation/data/cv_related_QA.csv exists."
        )

    df = pd.read_csv(INPUT_CSV)
    df.columns = df.columns.str.strip()

    required = {"ID", "Question", "Answers"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"CSV is missing columns: {sorted(missing)}. "
            f"Columns found: {df.columns.tolist()}"
        )

    # Create a scoring template only if one does not already exist,
    # so that previously entered scores are not overwritten.
    if SCORING_CSV.exists():
        scores = pd.read_csv(SCORING_CSV)
        scores.columns = scores.columns.str.strip()
        print(f"Using existing scoring file: {SCORING_CSV}")
    else:
        scores = df.copy()
        scores["Correctness_Score_0_2"] = ""
        scores["Supported_Claims"] = ""
        scores["Total_Factual_Claims"] = ""
        scores["Has_Unsupported_Claim"] = ""
        scores["Evaluator_Notes"] = ""
        scores.to_csv(SCORING_CSV, index=False, encoding="utf-8-sig")
        print(f"Created scoring template: {SCORING_CSV}")

    score_required = {
        "ID", "Correctness_Score_0_2",
        "Supported_Claims", "Total_Factual_Claims",
        "Has_Unsupported_Claim"
    }
    score_missing = score_required - set(scores.columns)
    if score_missing:
        raise ValueError(
            f"Scoring file is missing columns: {sorted(score_missing)}. "
            f"Open {SCORING_CSV} and check its headers."
        )

    # Convert manually entered scores to numeric values.
    for col in [
        "Correctness_Score_0_2",
        "Supported_Claims",
        "Total_Factual_Claims",
    ]:
        scores[col] = pd.to_numeric(scores[col], errors="coerce")

    scores["Faithfulness_Percent"] = (
        scores["Supported_Claims"] / scores["Total_Factual_Claims"] * 100
    ).where(scores["Total_Factual_Claims"] > 0).round(2)

    # Do not pretend metrics are final if required manual labels are blank.
    complete_correctness = scores["Correctness_Score_0_2"].notna().all()
    complete_claim_counts = (
        scores["Supported_Claims"].notna().all()
        and scores["Total_Factual_Claims"].notna().all()
    )
    complete_hallucination_labels = (
        scores["Has_Unsupported_Claim"].astype(str).str.strip().ne("").all()
    )

    scores.to_csv(SUMMARY_CSV, index=False, encoding="utf-8-sig")

    summary = {
        "number_of_questions": int(len(scores)),
        "input_csv": str(INPUT_CSV),
        "scoring_csv": str(SCORING_CSV),
        "correctness_metrics_status": "complete" if complete_correctness else "incomplete: enter a score for every question",
        "claim_metrics_status": "complete" if complete_claim_counts else "incomplete: enter supported and total factual claims for every question",
        "hallucination_metrics_status": "complete" if complete_hallucination_labels else "incomplete: enter Yes or No for every question",
    }

    if complete_correctness:
        mean_score = float(scores["Correctness_Score_0_2"].mean())
        summary["correctness_score_sum"] = float(scores["Correctness_Score_0_2"].sum())
        summary["average_correctness_out_of_2"] = round(mean_score, 3)
        summary["normalized_correctness_percent"] = round(mean_score / 2 * 100, 2)

    if complete_claim_counts:
        supported = int(scores["Supported_Claims"].sum())
        total = int(scores["Total_Factual_Claims"].sum())
        summary["supported_claims"] = supported
        summary["total_factual_claims"] = total
        summary["claim_level_faithfulness_percent"] = (
            round(supported / total * 100, 2) if total > 0 else None
        )

    if complete_hallucination_labels:
        yes_count = int(
            scores["Has_Unsupported_Claim"]
            .astype(str).str.strip().str.lower().eq("yes").sum()
        )
        summary["answers_with_unsupported_claims"] = yes_count
        summary["answer_level_hallucination_rate_percent"] = (
            round(yes_count / len(scores) * 100, 2) if len(scores) else None
        )

    summary["note"] = (
        "Metrics are calculated from manually entered evaluation labels. "
        "They are not final until the labels and claim counts have been verified against the CV."
    )

    SUMMARY_JSON.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\nLoaded {len(df)} questions from: {INPUT_CSV}")
    print(f"Scoring file: {SCORING_CSV}")
    print(f"Per-question output: {SUMMARY_CSV}")
    print(f"Summary JSON: {SUMMARY_JSON}")
    print("\nMetrics status:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
