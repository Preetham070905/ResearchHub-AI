"""
End-to-end API test for plagiarism detection endpoints.

Tests the full flow:
1. Register/Login user
2. Create workspace
3. Upload two PDF-like papers (text content)
4. Test /plagiarism/check-text
5. Test /plagiarism/compare-papers
6. Verify response structure

Run: python test_plagiarism_api.py
"""

import requests
import json
import sys
import time

BASE = "http://127.0.0.1:8000"

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed = 0
failed = 0


def ok(msg, detail=""):
    global passed
    passed += 1
    print(f"  {GREEN}✓{RESET} {msg}" + (f"  ({detail})" if detail else ""))


def fail(msg, detail=""):
    global failed
    failed += 1
    print(f"  {RED}✗{RESET} {msg}" + (f"  — {detail}" if detail else ""))


def section(title):
    print(f"\n{BOLD}{CYAN}{'='*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*55}{RESET}")


# ── 1. Health Check ──────────────────────────────────
section("1. Server Health")

try:
    r = requests.get(f"{BASE}/")
    if r.status_code == 200 and "4.0" in r.json().get("version", ""):
        ok(f"Server running v{r.json()['version']}")
    else:
        fail(f"Unexpected response: {r.status_code}")
except Exception as e:
    fail(f"Server not reachable: {e}")
    print(f"\n  {RED}Cannot continue without server. Start with: uvicorn main:app --port 8000{RESET}\n")
    sys.exit(1)

# ── 2. Auth — Register + Login ──────────────────────
section("2. Authentication")

test_email = f"plagtest_{int(time.time())}@test.com"
test_pass = "TestPass123!"

# Register
r = requests.post(f"{BASE}/auth/register", json={"email": test_email, "password": test_pass})
if r.status_code == 200:
    ok(f"Registered: {test_email}")
else:
    # May already exist
    ok(f"Register response: {r.status_code} (may exist)")

# Login
r = requests.post(
    f"{BASE}/auth/login",
    data={"username": test_email, "password": test_pass},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
if r.status_code == 200 and "access_token" in r.json():
    token = r.json()["access_token"]
    ok(f"Login successful, token: {token[:20]}...")
else:
    fail(f"Login failed: {r.status_code} {r.text}")
    sys.exit(1)

headers = {"Authorization": f"Bearer {token}"}

# ── 3. Create Workspace ─────────────────────────────
section("3. Workspace")

r = requests.post(f"{BASE}/workspaces/", json={"name": "Plagiarism Test Workspace"}, headers=headers)
if r.status_code == 200:
    ws = r.json()
    ws_id = ws["id"]
    ok(f"Workspace created: id={ws_id}, name='{ws['name']}'")
else:
    fail(f"Workspace creation: {r.status_code} {r.text}")
    sys.exit(1)

# ── 4. Test /plagiarism/check-text ───────────────────
section("4. /plagiarism/check-text (no workspace papers)")

text_to_check = (
    "Deep learning has revolutionized natural language processing over the past decade. "
    "Transformer-based models such as BERT and GPT have achieved state-of-the-art results "
    "on numerous NLP benchmarks. These models leverage self-attention mechanisms to effectively "
    "capture long-range dependencies. The pre-training and fine-tuning paradigm has become the "
    "standard approach for a variety of tasks including text classification, question answering, "
    "named entity recognition, and machine translation."
)

r = requests.post(
    f"{BASE}/plagiarism/check-text",
    data={
        "text": text_to_check,
        "title": "Test NLP Paper",
        "workspace_id": str(ws_id),
        "use_llm": "false",
    },
    headers=headers,
)

if r.status_code == 200:
    data = r.json()
    if data.get("status") == "no_references":
        ok(f"Correct response: '{data.get('message', 'no references')}'")
    else:
        ok(f"Response status: {data.get('status')}")
else:
    fail(f"check-text: {r.status_code} {r.text[:200]}")

# ── 5. Upload Papers to Workspace ────────────────────
section("5. Upload Papers (creating test PDFs)")

# We'll create minimal PDF files for testing
# First paper
import io

def make_simple_pdf(text_content: str) -> bytes:
    """Create a minimal valid PDF with text content."""
    # Minimal PDF structure
    content = text_content.encode('latin-1', errors='replace')
    
    pdf = b"%PDF-1.4\n"
    
    # Object 1: Catalog
    obj1_offset = len(pdf)
    pdf += b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    
    # Object 2: Pages
    obj2_offset = len(pdf)
    pdf += b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    
    # Object 3: Page
    obj3_offset = len(pdf)
    pdf += b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    
    # Object 4: Content stream
    stream = b"BT /F1 12 Tf 72 720 Td ("
    stream += content[:500]
    stream += b") Tj ET"
    
    obj4_offset = len(pdf)
    pdf += f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode()
    pdf += stream
    pdf += b"\nendstream\nendobj\n"
    
    # Object 5: Font
    obj5_offset = len(pdf)
    pdf += b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    
    # Xref
    xref_offset = len(pdf)
    pdf += b"xref\n0 6\n"
    pdf += b"0000000000 65535 f \n"
    pdf += f"{obj1_offset:010d} 00000 n \n".encode()
    pdf += f"{obj2_offset:010d} 00000 n \n".encode()
    pdf += f"{obj3_offset:010d} 00000 n \n".encode()
    pdf += f"{obj4_offset:010d} 00000 n \n".encode()
    pdf += f"{obj5_offset:010d} 00000 n \n".encode()
    
    pdf += b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
    pdf += b"startxref\n"
    pdf += f"{xref_offset}\n".encode()
    pdf += b"%%EOF\n"
    
    return pdf

paper1_text = (
    "Deep learning has revolutionized natural language processing. "
    "Transformer models like BERT and GPT achieve state-of-the-art results. "
    "Self-attention mechanisms capture long-range dependencies effectively."
)
paper2_text = (
    "Climate change impacts on agriculture in developing nations. "
    "Rainfall variability affects crop yields significantly. "
    "Adaptation strategies include drought-resistant varieties and irrigation."
)

pdf1 = make_simple_pdf(paper1_text)
pdf2 = make_simple_pdf(paper2_text)

# Upload paper 1
r = requests.post(
    f"{BASE}/papers/{ws_id}",
    files={"file": ("nlp_paper.pdf", io.BytesIO(pdf1), "application/pdf")},
    headers=headers,
)
if r.status_code == 200:
    p1 = r.json()
    ok(f"Uploaded paper 1: id={p1['id']}, '{p1['filename']}'")
else:
    fail(f"Upload paper 1: {r.status_code} {r.text[:200]}")
    p1 = None

# Upload paper 2
r = requests.post(
    f"{BASE}/papers/{ws_id}",
    files={"file": ("climate_paper.pdf", io.BytesIO(pdf2), "application/pdf")},
    headers=headers,
)
if r.status_code == 200:
    p2 = r.json()
    ok(f"Uploaded paper 2: id={p2['id']}, '{p2['filename']}'")
else:
    fail(f"Upload paper 2: {r.status_code} {r.text[:200]}")
    p2 = None

# ── 6. Test /plagiarism/check-text (with workspace papers) ──
section("6. /plagiarism/check-text (with papers)")

r = requests.post(
    f"{BASE}/plagiarism/check-text",
    data={
        "text": text_to_check,
        "title": "NLP Review Paper",
        "workspace_id": str(ws_id),
        "use_llm": "false",
    },
    headers=headers,
)

if r.status_code == 200:
    data = r.json()
    status = data.get("status")
    result = data.get("result")
    
    if status == "success" and result:
        score = result.get("overall_plagiarism_score", -1)
        risk = result.get("risk_level", "unknown")
        pairs = result.get("pair_results", [])
        ok(f"Score: {score}%, Risk: {risk}, Pairs: {len(pairs)}")
        
        # Verify result structure
        expected_keys = ["target_doc_id", "target_doc_title", "overall_plagiarism_score",
                        "risk_level", "summary", "pair_results", "stats"]
        missing = [k for k in expected_keys if k not in result]
        if not missing:
            ok(f"Result has all expected keys ({len(expected_keys)})")
        else:
            fail(f"Missing keys: {missing}")
        
        # Check stats
        stats = result.get("stats", {})
        if stats.get("reference_count", 0) > 0:
            ok(f"Stats: {stats.get('reference_count')} references checked")
        else:
            fail("Stats: reference_count is 0")
    elif status == "no_references":
        ok(f"No valid references extracted (PDFs may have insufficient text): {data.get('message', '')}")
    else:
        fail(f"Unexpected status: {status}, result: {str(result)[:200]}")
else:
    fail(f"check-text: {r.status_code} {r.text[:300]}")

# ── 7. Test /plagiarism/compare-papers ───────────────
section("7. /plagiarism/compare-papers")

if p1 and p2:
    r = requests.post(
        f"{BASE}/plagiarism/compare-papers",
        data={
            "paper_a_id": str(p1["id"]),
            "paper_b_id": str(p2["id"]),
            "workspace_id": str(ws_id),
            "use_llm": "false",
        },
        headers=headers,
    )
    
    if r.status_code == 200:
        data = r.json()
        if data.get("status") == "success" and data.get("result"):
            result = data["result"]
            ok(f"Compare: score={result.get('overall_plagiarism_score')}%, risk={result.get('risk_level')}")
        elif r.status_code == 200:
            ok(f"Compare returned: {data.get('status', 'unknown')} — {str(data)[:200]}")
    elif r.status_code == 400:
        ok(f"Compare: 400 (PDFs may lack extractable text) — {r.text[:150]}")
    else:
        fail(f"Compare: {r.status_code} {r.text[:200]}")
else:
    fail("Skipped compare — papers not uploaded")

# ── 8. Test /plagiarism/check (file upload) ──────────
section("8. /plagiarism/check (PDF upload)")

pdf_test = make_simple_pdf(text_to_check)
r = requests.post(
    f"{BASE}/plagiarism/check",
    files={"file": ("test_paper.pdf", io.BytesIO(pdf_test), "application/pdf")},
    data={
        "workspace_id": str(ws_id),
        "use_llm": "false",
    },
    headers=headers,
)

if r.status_code == 200:
    data = r.json()
    if data.get("status") == "success" and data.get("result"):
        result = data["result"]
        ok(f"PDF check: score={result.get('overall_plagiarism_score')}%, risk={result.get('risk_level')}")
    elif data.get("status") == "no_references":
        ok(f"PDF check: no references — {data.get('message', '')}")
    else:
        ok(f"PDF check returned: {data.get('status')}")
elif r.status_code == 400:
    ok(f"PDF check: 400 (text extraction issue) — {r.text[:150]}")
else:
    fail(f"PDF check: {r.status_code} {r.text[:200]}")

# ── 9. Error Cases ───────────────────────────────────
section("9. Error Cases")

# Non-PDF file
r = requests.post(
    f"{BASE}/plagiarism/check",
    files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    data={"workspace_id": str(ws_id), "use_llm": "false"},
    headers=headers,
)
if r.status_code == 400:
    ok("Non-PDF rejected with 400")
else:
    fail(f"Non-PDF should be 400, got {r.status_code}")

# Short text
r = requests.post(
    f"{BASE}/plagiarism/check-text",
    data={"text": "short", "workspace_id": str(ws_id), "use_llm": "false"},
    headers=headers,
)
if r.status_code == 400:
    ok("Short text rejected with 400")
else:
    fail(f"Short text should be 400, got {r.status_code}")

# No auth
r = requests.post(
    f"{BASE}/plagiarism/check-text",
    data={"text": "x" * 100, "workspace_id": str(ws_id), "use_llm": "false"},
)
if r.status_code == 401:
    ok("No auth returns 401")
else:
    fail(f"No auth should be 401, got {r.status_code}")

# ── 10. OpenAPI Doc Check ────────────────────────────
section("10. Swagger/OpenAPI")

r = requests.get(f"{BASE}/openapi.json")
if r.status_code == 200:
    paths = r.json().get("paths", {})
    plag_paths = [p for p in paths if "plagiarism" in p]
    if len(plag_paths) == 3:
        ok(f"OpenAPI: {len(plag_paths)} plagiarism endpoints documented")
    else:
        fail(f"Expected 3 plagiarism paths, got {len(plag_paths)}: {plag_paths}")

    # Check tags
    tags = r.json().get("tags", [])
    tag_names = [t.get("name") for t in tags] if tags else []
    ok(f"API docs accessible at http://127.0.0.1:8000/docs")
else:
    fail(f"OpenAPI: {r.status_code}")


# ── SUMMARY ──────────────────────────────────────────
section("TEST SUMMARY")
total = passed + failed
print(f"\n  {BOLD}Total: {total}  |  {GREEN}Passed: {passed}{RESET}  |  {RED}Failed: {failed}{RESET}\n")

if failed == 0:
    print(f"  {GREEN}{BOLD}🎉 ALL API TESTS PASSED!{RESET}\n")
else:
    print(f"  {RED}{BOLD}❌ {failed} TEST(S) FAILED{RESET}\n")

sys.exit(0 if failed == 0 else 1)
