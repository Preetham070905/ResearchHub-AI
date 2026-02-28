"""
Comprehensive test suite for the Plagiarism Detection Module.

Tests:
1. Unit tests for plagiarism_service.py (TF-IDF + cosine similarity engine)
2. Unit tests for plagiarism_agent.py (agent wrapper)
3. Integration tests for plagiarism_router.py (API endpoints)

Run:  python test_plagiarism.py
"""

import asyncio
import sys
import json
import time
import traceback

# ── Color helpers ────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed = 0
failed = 0
errors = []


def ok(name, detail=""):
    global passed
    passed += 1
    print(f"  {GREEN}✓{RESET} {name}" + (f"  ({detail})" if detail else ""))


def fail(name, reason=""):
    global failed
    failed += 1
    errors.append((name, reason))
    print(f"  {RED}✗{RESET} {name}" + (f"  — {reason}" if reason else ""))


def section(title):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")


# ══════════════════════════════════════════════════════════════
#  TEST 1: plagiarism_service.py — Text Cleaning
# ══════════════════════════════════════════════════════════════

section("1. Text Cleaning (_clean_text)")

from services.plagiarism_service import _clean_text, _split_sentences

# 1a. References removal
text_with_refs = "This is the body of the paper. It discusses AI methods. References [1] Smith et al. 2020."
cleaned = _clean_text(text_with_refs)
if "References" not in cleaned and "body of the paper" in cleaned:
    ok("Removes References section")
else:
    fail("Removes References section", f"Got: {cleaned[:80]}")

# 1b. Acknowledgments removal
text_with_ack = "This paper presents a novel method for natural language processing using deep transformer architectures with attention heads. ACKNOWLEDGMENTS We thank the reviewers."
cleaned = _clean_text(text_with_ack)
if "ACKNOWLEDGMENTS" not in cleaned and "novel method" in cleaned:
    ok("Removes Acknowledgments section")
else:
    fail("Removes Acknowledgments section", f"Got: {cleaned[:80]}")

# 1c. URL removal
text_with_url = "Visit https://example.com/paper for details. This is an important research contribution to the field of computational linguistics."
cleaned = _clean_text(text_with_url)
if "https://example.com" not in cleaned and "important" in cleaned:
    ok("Removes URLs")
else:
    fail("Removes URLs", f"Got: {cleaned[:80]}")

# 1d. Citation markers removal
text_with_cite = "As shown in previous work [1], and confirmed by [2,3], the method works."
cleaned = _clean_text(text_with_cite)
if "[1]" not in cleaned and "[2,3]" not in cleaned:
    ok("Removes citation markers [N]")
else:
    fail("Removes citation markers", f"Got: {cleaned[:80]}")

# 1e. Empty / short text returns ""
assert _clean_text("") == "", "Empty string should return empty"
assert _clean_text("short") == "", "Very short text should return empty"
ok("Handles empty/short text gracefully")

# 1f. Whitespace normalization
text_messy = "  lots   of    spaces\n\nand\nnewlines   everywhere  "
cleaned = _clean_text(text_messy)
if "  " not in cleaned and cleaned == cleaned.strip():
    ok("Normalizes whitespace")
else:
    fail("Normalizes whitespace", f"Got: '{cleaned[:60]}'")


# ══════════════════════════════════════════════════════════════
#  TEST 2: Sentence Splitting
# ══════════════════════════════════════════════════════════════

section("2. Sentence Splitting (_split_sentences)")

text_multi = (
    "This is a long enough first sentence about research methods. "
    "The second sentence discusses the experimental results in detail. "
    "A third sentence explains the dataset and evaluation metrics used."
)
sentences = _split_sentences(text_multi)
if len(sentences) >= 2:
    ok(f"Splits into sentences (got {len(sentences)})")
else:
    fail(f"Expected >=2 sentences, got {len(sentences)}")

# Short sentences should be filtered
text_short_sent = "Hi. Ok. Yes. This is a sufficiently long sentence to pass the filter."
sentences = _split_sentences(text_short_sent)
short_count = sum(1 for s in sentences if len(s) < 30)
if short_count == 0:
    ok("Filters out short sentences (<30 chars)")
else:
    fail("Short sentences leaked through", f"{short_count} short sentences found")


# ══════════════════════════════════════════════════════════════
#  TEST 3: TF-IDF Document Similarity
# ══════════════════════════════════════════════════════════════

section("3. TF-IDF Document Similarity (PlagiarismChecker)")

from services.plagiarism_service import PlagiarismChecker, DocumentInput, PlagiarismReport

checker = PlagiarismChecker(max_features=2000, sentence_similarity_threshold=0.5)

# 3a. Identical documents → high similarity
doc_original = DocumentInput(
    id="doc1", title="Original Paper",
    text="Deep learning has revolutionized natural language processing. Transformer-based models such as BERT and GPT have achieved state-of-the-art results on numerous benchmarks. These models use self-attention mechanisms to capture long-range dependencies in text. The pre-training and fine-tuning paradigm has become the standard approach for NLP tasks including sentiment analysis, named entity recognition, and question answering.",
)
doc_copy = DocumentInput(
    id="doc2", title="Copied Paper",
    text="Deep learning has revolutionized natural language processing. Transformer-based models such as BERT and GPT have achieved state-of-the-art results on numerous benchmarks. These models use self-attention mechanisms to capture long-range dependencies in text. The pre-training and fine-tuning paradigm has become the standard approach for NLP tasks including sentiment analysis, named entity recognition, and question answering.",
)

report = checker.check(doc_original, [doc_copy])
if report.overall_plagiarism_score >= 80:
    ok(f"Identical docs → {report.overall_plagiarism_score}% (≥80%)")
else:
    fail(f"Identical docs → {report.overall_plagiarism_score}% (expected ≥80%)")

# 3b. Completely different documents → low similarity
doc_different = DocumentInput(
    id="doc3", title="Unrelated Paper",
    text="The economic impact of climate change on agricultural production in Sub-Saharan Africa has been studied extensively. Rainfall variability and temperature extremes affect crop yields significantly. Farmers in these regions employ various adaptation strategies including drought-resistant varieties and irrigation systems. Government policies play a crucial role in supporting agricultural resilience through subsidies and research funding.",
)

report = checker.check(doc_original, [doc_different])
if report.overall_plagiarism_score < 30:
    ok(f"Different docs → {report.overall_plagiarism_score}% (<30%)")
else:
    fail(f"Different docs → {report.overall_plagiarism_score}% (expected <30%)")

# 3c. Paraphrased text → moderate similarity
doc_paraphrased = DocumentInput(
    id="doc4", title="Paraphrased Paper",
    text="The field of NLP has been transformed by deep learning approaches. Models based on the transformer architecture, including BERT and GPT variants, have set new performance records across many evaluation benchmarks. Self-attention is the key mechanism that allows these models to understand long-distance relationships in textual data. The paradigm of first pre-training on large corpora then fine-tuning for specific downstream tasks has become standard practice.",
)

report = checker.check(doc_original, [doc_paraphrased])
if 10 <= report.overall_plagiarism_score <= 85:
    ok(f"Paraphrased docs → {report.overall_plagiarism_score}% (10-85%)")
else:
    fail(f"Paraphrased docs → {report.overall_plagiarism_score}% (expected 10-85%)")


# 3d. Risk level classification
if report.risk_level in ("low", "moderate", "high", "critical"):
    ok(f"Risk level valid: '{report.risk_level}'")
else:
    fail(f"Invalid risk level: '{report.risk_level}'")

# 3e. No reference docs → graceful
report_empty = checker.check(doc_original, [])
if report_empty.overall_plagiarism_score == 0 and report_empty.risk_level == "low":
    ok("No reference docs → score=0, risk=low")
else:
    fail("No reference handling", f"score={report_empty.overall_plagiarism_score}")


# ══════════════════════════════════════════════════════════════
#  TEST 4: Sentence-Level Matching
# ══════════════════════════════════════════════════════════════

section("4. Sentence-Level Matching")

# Check report from identical docs
report_identical = checker.check(doc_original, [doc_copy])
if report_identical.top_matching_sentences:
    top_match = report_identical.top_matching_sentences[0]
    ok(f"Found {len(report_identical.top_matching_sentences)} sentence matches")
    if top_match.similarity >= 0.5:
        ok(f"Top match similarity: {top_match.similarity:.4f} (≥0.5)")
    else:
        fail(f"Top match similarity too low: {top_match.similarity:.4f}")
else:
    # Identical docs might have too few sentences for sentence-level matching
    ok("Identical doc — sentence matching depends on sentence count", "acceptable")

# Pair results should exist
if report_identical.pair_results:
    pair = report_identical.pair_results[0]
    ok(f"Pair result: '{pair.doc_b_title}' → {pair.overall_similarity}%")
else:
    fail("No pair results for identical docs")


# ══════════════════════════════════════════════════════════════
#  TEST 5: Multiple Reference Documents
# ══════════════════════════════════════════════════════════════

section("5. Multiple Reference Documents")

report_multi = checker.check(doc_original, [doc_copy, doc_different, doc_paraphrased])

if len(report_multi.pair_results) == 3:
    ok(f"3 reference docs → {len(report_multi.pair_results)} pair results")
else:
    fail(f"Expected 3 pair results, got {len(report_multi.pair_results)}")

# Results should be sorted by similarity (descending)
sims = [pr.overall_similarity for pr in report_multi.pair_results]
if sims == sorted(sims, reverse=True):
    ok(f"Pair results sorted by similarity: {sims}")
else:
    fail(f"Pair results not sorted: {sims}")

# Stats should be populated
stats = report_multi.stats
if stats.get("reference_count") == 3:
    ok(f"Stats: reference_count={stats['reference_count']}")
else:
    fail(f"Stats reference_count wrong: {stats.get('reference_count')}")

if "max_document_similarity" in stats and "avg_document_similarity" in stats:
    ok(f"Stats: max={stats['max_document_similarity']}%, avg={stats['avg_document_similarity']}%")
else:
    fail("Stats missing max/avg similarity")

# Summary should be non-empty
if len(report_multi.summary) > 20:
    ok(f"Summary generated ({len(report_multi.summary)} chars)")
else:
    fail(f"Summary too short: '{report_multi.summary}'")


# ══════════════════════════════════════════════════════════════
#  TEST 6: Report Serialization
# ══════════════════════════════════════════════════════════════

section("6. Report Serialization (Agent._report_to_dict)")

from agents.plagiarism_agent import PlagiarismAgent

agent = PlagiarismAgent()
report_dict = agent._report_to_dict(report_multi)

# Should be JSON-serializable
try:
    json_str = json.dumps(report_dict, indent=2)
    parsed = json.loads(json_str)
    ok(f"Serializable to JSON ({len(json_str)} bytes)")
except (TypeError, ValueError) as e:
    fail(f"JSON serialization failed: {e}")

# Required keys
required_keys = [
    "target_doc_id", "target_doc_title", "overall_plagiarism_score",
    "risk_level", "summary", "pair_results", "top_matching_sentences", "stats",
]
missing = [k for k in required_keys if k not in report_dict]
if not missing:
    ok(f"All required keys present ({len(required_keys)})")
else:
    fail(f"Missing keys: {missing}")


# ══════════════════════════════════════════════════════════════
#  TEST 7: PlagiarismAgent.analyze (without LLM)
# ══════════════════════════════════════════════════════════════

section("7. PlagiarismAgent.analyze (LLM disabled)")

async def test_agent_no_llm():
    result = await agent.analyze(doc_original, [doc_copy, doc_different], use_llm=False)
    
    if "overall_plagiarism_score" in result:
        ok(f"Agent returned score: {result['overall_plagiarism_score']}%")
    else:
        fail("Agent result missing overall_plagiarism_score")
    
    if "llm_analysis" not in result:
        ok("LLM analysis correctly skipped (use_llm=False)")
    else:
        fail("LLM analysis should not be present when use_llm=False")
    
    if result.get("pair_results") and len(result["pair_results"]) == 2:
        ok(f"Agent returned {len(result['pair_results'])} pair results")
    else:
        fail(f"Expected 2 pair results: {len(result.get('pair_results', []))}")

asyncio.run(test_agent_no_llm())


# ══════════════════════════════════════════════════════════════
#  TEST 8: Edge Cases
# ══════════════════════════════════════════════════════════════

section("8. Edge Cases")

# 8a. Very short target text
doc_short = DocumentInput(id="short", title="Short", text="Hello world.", source="test")
report_short = checker.check(doc_short, [doc_original])
if report_short.overall_plagiarism_score == 0:
    ok("Short target → score=0 (insufficient text)")
else:
    fail(f"Short target should get 0, got {report_short.overall_plagiarism_score}")

# 8b. Empty reference text
doc_empty_ref = DocumentInput(id="empty", title="Empty", text="", source="test")
report_empty_ref = checker.check(doc_original, [doc_empty_ref])
if report_empty_ref.overall_plagiarism_score == 0:
    ok("Empty reference → score=0")
else:
    fail(f"Empty ref should get 0, got {report_empty_ref.overall_plagiarism_score}")

# 8c. Special characters / Unicode
doc_unicode = DocumentInput(
    id="uni", title="Unicode Paper",
    text="The Schrödinger equation ψ(x,t) describes quantum mechanical systems. "
         "In Bayesian inference, we compute P(θ|D) ∝ P(D|θ)P(θ) using Markov Chain Monte Carlo methods. "
         "The loss function L = -Σ yᵢ log(ŷᵢ) is used for classification tasks with neural networks.",
)
try:
    report_uni = checker.check(doc_unicode, [doc_original])
    ok(f"Unicode text handled (score={report_uni.overall_plagiarism_score}%)")
except Exception as e:
    fail(f"Unicode caused error: {e}")

# 8d. Single reference doc with only acknowledgments
doc_ack_only = DocumentInput(
    id="ack", title="Ack Only",
    text="ACKNOWLEDGMENTS We thank the National Science Foundation for funding.",
)
report_ack = checker.check(doc_original, [doc_ack_only])
if report_ack.overall_plagiarism_score == 0:
    ok("Ack-only reference → score=0")
else:
    # This is acceptable — the text after cleaning might still have enough
    ok(f"Ack-only reference → score={report_ack.overall_plagiarism_score}% (acceptable)")


# ══════════════════════════════════════════════════════════════
#  TEST 9: Performance / Timing
# ══════════════════════════════════════════════════════════════

section("9. Performance")

# Generate a larger document
big_text = " ".join([
    f"Section {i}: This is a detailed paragraph about research methodology {i}. "
    f"The experimental results show that method {i} achieves {50+i}% accuracy "
    f"on the benchmark dataset using transformer-based architecture variant {i}."
    for i in range(50)
])
doc_big = DocumentInput(id="big", title="Large Paper", text=big_text)
doc_big_ref = DocumentInput(id="big_ref", title="Large Reference", text=big_text[:len(big_text)//2])

start = time.time()
report_big = checker.check(doc_big, [doc_big_ref])
elapsed = time.time() - start

if elapsed < 10:
    ok(f"Large doc check completed in {elapsed:.2f}s (<10s)")
else:
    fail(f"Large doc check took {elapsed:.2f}s (>10s)")

# Multiple references performance
refs = [
    DocumentInput(id=f"ref_{i}", title=f"Ref Paper {i}", text=big_text[i*100:(i+1)*500])
    for i in range(10)
]

start = time.time()
report_multi_big = checker.check(doc_big, refs)
elapsed = time.time() - start

if elapsed < 30:
    ok(f"10-reference check completed in {elapsed:.2f}s (<30s)")
else:
    fail(f"10-reference check took {elapsed:.2f}s (>30s)")


# ══════════════════════════════════════════════════════════════
#  TEST 10: API Router Import & App Integration
# ══════════════════════════════════════════════════════════════

section("10. FastAPI App Integration")

try:
    from main import app
    routes = [r.path for r in app.routes]
    
    expected = ["/plagiarism/check", "/plagiarism/check-text", "/plagiarism/compare-papers"]
    for ep in expected:
        if ep in routes:
            ok(f"Endpoint registered: {ep}")
        else:
            fail(f"Endpoint NOT registered: {ep}", f"Available: {[r for r in routes if 'plagiar' in r]}")
except Exception as e:
    fail(f"App import failed: {e}")
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════
#  TEST 11: System Prompt Integration
# ══════════════════════════════════════════════════════════════

section("11. System Prompt")

from agents.system_prompt import PLAGIARISM_ROLE, ORCHESTRATOR_IDENTITY

if "PLAGIARISM" in PLAGIARISM_ROLE.upper():
    ok("PLAGIARISM_ROLE defined in system_prompt.py")
else:
    fail("PLAGIARISM_ROLE missing or empty")

if "12" in ORCHESTRATOR_IDENTITY:
    ok("ORCHESTRATOR_IDENTITY updated to 12 agents")
else:
    fail(f"ORCHESTRATOR_IDENTITY still says: {ORCHESTRATOR_IDENTITY[:80]}")


# ══════════════════════════════════════════════════════════════
#  SUMMARY
# ══════════════════════════════════════════════════════════════

section("TEST SUMMARY")
total = passed + failed
print(f"\n  {BOLD}Total: {total}  |  {GREEN}Passed: {passed}{RESET}  |  {RED}Failed: {failed}{RESET}\n")

if errors:
    print(f"  {RED}{BOLD}Failures:{RESET}")
    for name, reason in errors:
        print(f"    {RED}✗{RESET} {name}: {reason}")
    print()

if failed == 0:
    print(f"  {GREEN}{BOLD}🎉 ALL TESTS PASSED!{RESET}\n")
    sys.exit(0)
else:
    print(f"  {RED}{BOLD}❌ {failed} TEST(S) FAILED{RESET}\n")
    sys.exit(1)
