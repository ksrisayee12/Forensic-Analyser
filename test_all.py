"""
AIVENTRA — Master End-to-End Test Script
Run: python test_all.py [path/to/file.pdf]

Tests all endpoints in sequence:
  1. GET  /health
  2. POST /upload
  3. POST /ocr
  4. POST /analyze
  5. POST /extract
  6. POST /reason
  7. POST /rag/query
  8. GET  /case/{id}

Saves full output to test_results.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000"
RESULTS = {}

# ── Helpers ──────────────────────────────────────────────────────────────────

def ok(label: str, resp: requests.Response) -> dict:
    elapsed = getattr(resp, "_elapsed_ms", "?")
    if resp.status_code in (200, 201):
        print(f"  [PASS] {label} [{resp.status_code}] ({elapsed}ms)")
        data = resp.json()
        RESULTS[label] = data
        return data
    else:
        print(f"  [FAIL] {label} [{resp.status_code}]")
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        print(f"     Error: {json.dumps(err, indent=6)[:500]}")
        RESULTS[label] = {"error": err, "status_code": resp.status_code}
        return {}

def post(url, **kwargs) -> requests.Response:
    t0 = time.time()
    r = requests.post(f"{BASE_URL}{url}", **kwargs)
    r._elapsed_ms = int((time.time() - t0) * 1000)
    return r

def get(url, **kwargs) -> requests.Response:
    t0 = time.time()
    r = requests.get(f"{BASE_URL}{url}", **kwargs)
    r._elapsed_ms = int((time.time() - t0) * 1000)
    return r

def section(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Determine test file
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
    else:
        # Auto-pick most recent uploaded PDF
        uploads = sorted(Path("uploads").glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not uploads:
            print("❌ No test file. Usage: python test_all.py path/to/file.pdf")
            print("   Or upload a PDF first via POST /upload, then re-run.")
            sys.exit(1)
        test_file = uploads[0]

    print(f"\n*** AIVENTRA End-to-End Test ***")
    print(f"   Server : {BASE_URL}")
    print(f"   File   : {test_file}")
    print(f"   Size   : {test_file.stat().st_size / 1024:.1f} KB")

    case_id = None

    # ── 1. Health ────────────────────────────────────────────────────────────
    section("1. Health Check")
    r = get("/health")
    health = ok("health", r)
    if health:
        print(f"     Device       : {health.get('device', '?')}")
        print(f"     Ollama       : {health.get('ollama_available', '?')}")
        print(f"     Ollama models: {health.get('ollama_models', [])}")
        models = health.get("models_loaded", {})
        loaded = [k for k, v in models.items() if v]
        print(f"     Models loaded: {loaded}")

    # ── 2. Upload ─────────────────────────────────────────────────────────────
    section("2. Upload Document")
    with open(test_file, "rb") as f:
        r = post("/upload", files={"file": (test_file.name, f, "application/pdf")})
    upload = ok("upload", r)
    if upload:
        case_id = upload.get("case_id")
        print(f"     case_id : {case_id}")
        print(f"     status  : {upload.get('status')}")

    # ── 3. OCR ───────────────────────────────────────────────────────────────
    section("3. OCR")
    with open(test_file, "rb") as f:
        r = post("/ocr", files={"file": (test_file.name, f, "application/pdf")})
    ocr = ok("ocr", r)
    if ocr:
        text_preview = (ocr.get("text", "") or "")[:200].replace("\n", " ")
        print(f"     pages      : {ocr.get('page_count')}")
        print(f"     confidence : {ocr.get('confidence')}")
        print(f"     blocks     : {len(ocr.get('blocks', []))}")
        print(f"     text[:200] : {text_preview!r}")

    # ── 4. Analyze ────────────────────────────────────────────────────────────
    section("4. Full Pipeline Analysis")
    if not case_id:
        print("  ⚠️  Skipped — no case_id from upload step")
    else:
        r = post("/analyze", json={"case_id": case_id}, timeout=300)
        analyze = ok("analyze", r)
        if analyze:
            print(f"     status     : {analyze.get('status')}")
            print(f"     entities   : {len(analyze.get('entities', []))}")
            print(f"     injuries   : {len(analyze.get('injuries', []))}")
            print(f"     mechanism  : {analyze.get('spatial_analysis', {}).get('mechanism')}")
            print(f"     report_id  : {analyze.get('report_id')}")
            summary_prev = (analyze.get("summary") or "")[:200].replace("\n", " ")
            print(f"     summary[:200]: {summary_prev!r}")

    # ── 5. NLP Extract ───────────────────────────────────────────────────────
    section("5. NLP Entity Extraction")
    sample_text = (
        "The decedent sustained a single gunshot wound to the left anterior chest. "
        "Entrance wound measuring 0.8 cm. Bullet recovered from right thoracic cavity. "
        "Blood ethanol: 0.14 g/dL. Manner of death: Homicide."
    )
    r = post("/extract", json={"text": sample_text, "use_llm": False}, timeout=60)
    extract = ok("extract", r)
    if extract:
        print(f"     entity_count : {extract.get('entity_count')}")
        print(f"     sources_used : {extract.get('sources_used')}")
        for e in (extract.get("entities") or [])[:5]:
            print(f"       [{e.get('entity_type')}] {e.get('entity_value')} (conf={e.get('confidence'):.2f})")

    # ── 6. Reason ─────────────────────────────────────────────────────────────
    section("6. LLM Forensic Reasoning")
    if not case_id:
        print("  ⚠️  Skipped — no case_id from upload step")
    else:
        r = post("/reason", json={"case_id": case_id, "multi_model": False}, timeout=300)
        reason = ok("reason", r)
        if reason:
            print(f"     model      : {reason.get('model')}")
            print(f"     report_id  : {reason.get('report_id')}")
            summ = (reason.get("summary") or "")[:200].replace("\n", " ")
            print(f"     summary[:200]: {summ!r}")

    # ── 7. RAG Query ─────────────────────────────────────────────────────────
    section("7. RAG Query")
    if not case_id:
        print("  ⚠️  Skipped — no case_id from upload step")
    else:
        r = post(
            "/rag/query",
            json={
                "case_id": case_id,
                "query": "What is the mechanism and manner of death?",
                "top_k": 5,
            },
            timeout=120,
        )
        rag = ok("rag_query", r)
        if rag:
            print(f"     chunks     : {rag.get('chunk_count')}")
            print(f"     model      : {rag.get('model')}")
            ans = (rag.get("answer") or "")[:200].replace("\n", " ")
            print(f"     answer[:200]: {ans!r}")

    # ── 8. Case Detail ───────────────────────────────────────────────────────
    section("8. Case Record Retrieval")
    if not case_id:
        print("  ⚠️  Skipped — no case_id from upload step")
    else:
        r = get(f"/case/{case_id}", timeout=30)
        case_detail = ok("case_detail", r)
        if case_detail:
            print(f"     status          : {case_detail.get('status')}")
            print(f"     injuries        : {len(case_detail.get('injuries', []))}")
            print(f"     forensic_ents   : {len(case_detail.get('forensic_entities', []))}")
            print(f"     toxicology      : {len(case_detail.get('toxicology', []))}")
            print(f"     reports         : {len(case_detail.get('reports', []))}")

    # ── Summary ───────────────────────────────────────────────────────────────
    section("Test Summary")
    passed = sum(1 for v in RESULTS.values() if "error" not in v)
    total = len(RESULTS)
    print(f"  Passed: {passed}/{total}")
    for name, result in RESULTS.items():
        status = "✅" if "error" not in result else "❌"
        print(f"    {status} {name}")

    # ── Write results ─────────────────────────────────────────────────────────
    out_path = Path("test_results.json")
    out_path.write_text(json.dumps(RESULTS, indent=2, default=str), encoding="utf-8")
    print(f"\n  [INFO] Full results -> {out_path.resolve()}")
    print()

if __name__ == "__main__":
    main()
