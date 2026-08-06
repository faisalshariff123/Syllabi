#Eval harness for extract_deadlines: checks date recall/precision against
#a hand-labeled fixture (eval_data.json). Titles are scored loosely (keyword
#match) since the LLM's exact phrasing isn't the thing we care about.

#Usage: python eval.py

import json
import os
import unicodedata

from extractor import extract_deadlines


def normalize(s: str) -> str:
    return unicodedata.normalize("NFKD", s)

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "eval_data.json")


def load_fixture():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


def score_case(pdf_path: str, expected: list[dict], term_start_date: str | None) -> dict:
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    actual = extract_deadlines(pdf_bytes, term_start_date=term_start_date)
    actual_by_date = {}
    for d in actual:
        actual_by_date.setdefault(d.date, []).append(normalize(d.title.lower()))

    matched, missed, wrong_title = [], [], []
    for exp in expected:
        titles = actual_by_date.get(exp["date"])
        if titles is None:
            missed.append(exp["date"])
            continue
        joined = " ".join(titles)
        if all(kw in joined for kw in exp["keywords"]):
            matched.append(exp["date"])
        else:
            wrong_title.append((exp["date"], titles, exp["keywords"]))

    expected_dates = {exp["date"] for exp in expected}
    extra = sorted(set(actual_by_date) - expected_dates)

    return {
        "total_expected": len(expected),
        "matched": len(matched),
        "missed_dates": missed,
        "wrong_title": wrong_title,
        "extra_dates": extra,
        "raw_count": len(actual),
    }


def main():
    fixture = load_fixture()
    all_results = []

    for case in fixture:
        pdf_path = os.path.join(os.path.dirname(__file__), case["pdf"])
        result = score_case(pdf_path, case["expected"], case.get("term_start_date"))
        all_results.append(result)

        print(f"\n{case['pdf']}")
        if result["total_expected"] == 0:
            if result["raw_count"] == 0:
                print("  PASS: no deadlines in source, none hallucinated")
            else:
                print(f"  FAIL: HALLUCINATED {result['raw_count']} deadline(s) out of nowhere: {result['extra_dates']}")
        else:
            recall = result["matched"] / result["total_expected"]
            print(f"  recall: {result['matched']}/{result['total_expected']} ({recall:.0%})")
            print(f"  extracted {result['raw_count']} deadlines total")
            if result["missed_dates"]:
                print(f"  MISSED dates: {result['missed_dates']}")
            if result["wrong_title"]:
                for date, titles, kws in result["wrong_title"]:
                    print(f"  WRONG TITLE @ {date}: got {titles}, wanted keywords {kws}")
            if result["extra_dates"]:
                print(f"  extra (unlabeled) dates: {result['extra_dates']}")

    scored = [r for r in all_results if r["total_expected"] > 0]
    total_matched = sum(r["matched"] for r in scored)
    total_expected = sum(r["total_expected"] for r in scored)
    hallucination_fails = sum(
        1 for r in all_results if r["total_expected"] == 0 and r["raw_count"] > 0
    )
    print(f"\n=== overall recall: {total_matched}/{total_expected} ({total_matched/total_expected:.0%}) ===")
    if hallucination_fails:
        print(f"=== {hallucination_fails} hallucination-on-empty-input failure(s) ===")


if __name__ == "__main__":
    main()
