"""
Plagiarism Detection Service — TF-IDF + Cosine Similarity engine.

Inspired by https://github.com/lynxrose/research-paper-plagiarism-detector
which uses TF-IDF vectorization and ML classification for research papers.

This service adapts those techniques into a production-ready plagiarism checker:
1. Text preprocessing (cleaning acknowledgments, references, escape characters)
2. TF-IDF vectorization of document text
3. Cosine similarity matrix between all document pairs
4. Sentence-level matching to find specific plagiarized passages
5. Overall plagiarism score computation

Used by:
  - PlagiarismAgent (agents/plagiarism_agent.py) for LLM-enhanced analysis
  - /plagiarism/ router for direct API access
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


# ── Data Classes ──────────────────────────────────────────────

@dataclass
class DocumentInput:
    """A document to check for plagiarism."""
    id: str
    title: str
    text: str
    source: str = "unknown"  # "uploaded", "arxiv", "pubmed", "workspace"


@dataclass
class SentenceMatch:
    """A pair of similar sentences found between two documents."""
    source_sentence: str
    matched_sentence: str
    similarity: float
    source_doc_id: str
    matched_doc_id: str


@dataclass
class DocumentPairResult:
    """Plagiarism result between two documents."""
    doc_a_id: str
    doc_a_title: str
    doc_b_id: str
    doc_b_title: str
    overall_similarity: float
    sentence_matches: List[SentenceMatch] = field(default_factory=list)


@dataclass
class PlagiarismReport:
    """Complete plagiarism check report."""
    target_doc_id: str
    target_doc_title: str
    overall_plagiarism_score: float  # 0-100
    risk_level: str  # "low", "moderate", "high", "critical"
    pair_results: List[DocumentPairResult] = field(default_factory=list)
    top_matching_sentences: List[SentenceMatch] = field(default_factory=list)
    summary: str = ""
    stats: Dict[str, Any] = field(default_factory=dict)


# ── Text Preprocessing (adapted from lynxrose cleaning.py) ────

# Section headers that mark the end of the main body
ENDING_HEADERS = [
    "References", "REFERENCES", "Bibliography", "BIBLIOGRAPHY",
    "ACKNOWLEDGMENTS", "Acknowledgments", "Acknowledgements",
    "R EFERENCES", "r eferences", "R e f e r e n c e s",
    "Acknowledge me nts", "APPENDIX", "Appendix",
]


def _clean_text(text: str) -> str:
    """
    Clean research paper text for similarity analysis.
    Adapted from lynxrose/research-paper-plagiarism-detector/cleaning.py
    """
    if not text:
        return ""

    # 1. Remove content after References/Acknowledgments section
    for header in ENDING_HEADERS:
        parts = text.split(header)
        if len(parts) > 1:
            text = parts[0]
            break

    # 2. Remove common PDF extraction artifacts
    text = re.sub(r'\x0c', ' ', text)           # form feeds
    text = re.sub(r'\xa0', ' ', text)            # non-breaking spaces
    text = re.sub(r'[\x00-\x08\x0b\x0e-\x1f]', '', text)  # control chars

    # 3. Remove URLs and emails
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\S+@\S+\.\S+', '', text)

    # 4. Remove citation markers like [1], [2,3], (Author et al., 2020)
    text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)
    text = re.sub(r'\([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4}\)', '', text)

    # 5. Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # 6. Remove very short text (likely noise)
    if len(text) < 50:
        return ""

    return text


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences for fine-grained comparison."""
    # Simple sentence splitter — handles abbreviations reasonably well
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    # Filter out very short sentences (headers, noise)
    return [s.strip() for s in sentences if len(s.strip()) > 30]


# ── TF-IDF Similarity Engine ──────────────────────────────────

class PlagiarismChecker:
    """
    TF-IDF + Cosine Similarity plagiarism detection engine.

    Adapted from lynxrose's approach:
    - TfidfVectorizer with configurable max_features (default: 5000)
    - Cosine similarity for document-level comparison
    - Sentence-level matching for detailed passage detection
    """

    def __init__(
        self,
        max_features: int = 5000,
        sentence_similarity_threshold: float = 0.6,
        ngram_range: Tuple[int, int] = (1, 2),
    ):
        self.max_features = max_features
        self.sentence_threshold = sentence_similarity_threshold
        self.ngram_range = ngram_range

    def check(
        self,
        target: DocumentInput,
        reference_docs: List[DocumentInput],
    ) -> PlagiarismReport:
        """
        Check a target document against a list of reference documents.

        Args:
            target: The document being checked for plagiarism
            reference_docs: Documents to compare against

        Returns:
            PlagiarismReport with similarity scores and matching passages
        """
        if not reference_docs:
            return PlagiarismReport(
                target_doc_id=target.id,
                target_doc_title=target.title,
                overall_plagiarism_score=0.0,
                risk_level="low",
                summary="No reference documents provided for comparison.",
                stats={"reference_count": 0},
            )

        # 1. Clean all documents
        target_clean = _clean_text(target.text)
        ref_clean = [(doc, _clean_text(doc.text)) for doc in reference_docs]
        ref_clean = [(doc, text) for doc, text in ref_clean if text]

        if not target_clean:
            return PlagiarismReport(
                target_doc_id=target.id,
                target_doc_title=target.title,
                overall_plagiarism_score=0.0,
                risk_level="low",
                summary="Target document has insufficient text for analysis.",
                stats={"reference_count": len(reference_docs)},
            )

        if not ref_clean:
            return PlagiarismReport(
                target_doc_id=target.id,
                target_doc_title=target.title,
                overall_plagiarism_score=0.0,
                risk_level="low",
                summary="No reference documents had sufficient text for comparison.",
                stats={"reference_count": len(reference_docs)},
            )

        # 2. Document-level TF-IDF similarity
        all_texts = [target_clean] + [text for _, text in ref_clean]
        doc_similarities = self._compute_document_similarity(all_texts)

        # 3. Sentence-level matching for each reference doc
        pair_results: List[DocumentPairResult] = []
        all_sentence_matches: List[SentenceMatch] = []

        target_sentences = _split_sentences(target_clean)

        for i, (ref_doc, ref_text) in enumerate(ref_clean):
            sim_score = float(doc_similarities[0, i + 1])  # target is index 0

            ref_sentences = _split_sentences(ref_text)
            sentence_matches = self._find_sentence_matches(
                target_sentences, ref_sentences, target.id, ref_doc.id
            )

            pair_result = DocumentPairResult(
                doc_a_id=target.id,
                doc_a_title=target.title,
                doc_b_id=ref_doc.id,
                doc_b_title=ref_doc.title,
                overall_similarity=round(sim_score * 100, 2),
                sentence_matches=sentence_matches[:10],  # Top 10 per pair
            )
            pair_results.append(pair_result)
            all_sentence_matches.extend(sentence_matches)

        # 4. Compute overall plagiarism score
        max_similarity = max(pr.overall_similarity for pr in pair_results)
        avg_similarity = sum(pr.overall_similarity for pr in pair_results) / len(pair_results)

        # Weighted: 60% max similarity, 40% average (max catches worst case)
        plagiarism_score = round(0.6 * max_similarity + 0.4 * avg_similarity, 2)

        # 5. Determine risk level
        risk_level = self._get_risk_level(plagiarism_score)

        # 6. Sort sentence matches by similarity (descending)
        all_sentence_matches.sort(key=lambda m: m.similarity, reverse=True)

        # 7. Build summary
        summary = self._build_summary(
            plagiarism_score, risk_level, pair_results, len(all_sentence_matches)
        )

        return PlagiarismReport(
            target_doc_id=target.id,
            target_doc_title=target.title,
            overall_plagiarism_score=plagiarism_score,
            risk_level=risk_level,
            pair_results=sorted(pair_results, key=lambda p: p.overall_similarity, reverse=True),
            top_matching_sentences=all_sentence_matches[:20],  # Top 20 overall
            summary=summary,
            stats={
                "reference_count": len(ref_clean),
                "target_sentences": len(target_sentences),
                "total_sentence_matches": len(all_sentence_matches),
                "max_document_similarity": round(max_similarity, 2),
                "avg_document_similarity": round(avg_similarity, 2),
                "tfidf_features": self.max_features,
                "ngram_range": list(self.ngram_range),
                "sentence_threshold": self.sentence_threshold,
            },
        )

    def _compute_document_similarity(self, texts: List[str]) -> np.ndarray:
        """
        Compute pairwise TF-IDF cosine similarity matrix.
        Adapted from lynxrose modeling.py's TfidfVectorizer approach.
        """
        vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            stop_words="english",
            sublinear_tf=True,          # Apply log normalization
            strip_accents="unicode",
        )
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
            return cosine_similarity(tfidf_matrix)
        except ValueError as e:
            logger.warning(f"TF-IDF vectorization failed: {e}")
            return np.zeros((len(texts), len(texts)))

    def _find_sentence_matches(
        self,
        target_sentences: List[str],
        ref_sentences: List[str],
        target_id: str,
        ref_id: str,
    ) -> List[SentenceMatch]:
        """
        Find sentence-level similarities above threshold.
        Uses TF-IDF on sentences for fine-grained matching.
        """
        if not target_sentences or not ref_sentences:
            return []

        all_sentences = target_sentences + ref_sentences
        try:
            vectorizer = TfidfVectorizer(
                max_features=2000,
                ngram_range=(1, 3),
                stop_words="english",
            )
            tfidf_matrix = vectorizer.fit_transform(all_sentences)

            # Compare target sentences (first N) against reference sentences (rest)
            n_target = len(target_sentences)
            target_vectors = tfidf_matrix[:n_target]
            ref_vectors = tfidf_matrix[n_target:]

            similarities = cosine_similarity(target_vectors, ref_vectors)
        except ValueError:
            return []

        matches = []
        for i in range(len(target_sentences)):
            for j in range(len(ref_sentences)):
                sim = float(similarities[i, j])
                if sim >= self.sentence_threshold:
                    matches.append(SentenceMatch(
                        source_sentence=target_sentences[i][:300],
                        matched_sentence=ref_sentences[j][:300],
                        similarity=round(sim, 4),
                        source_doc_id=target_id,
                        matched_doc_id=ref_id,
                    ))

        matches.sort(key=lambda m: m.similarity, reverse=True)
        return matches

    @staticmethod
    def _get_risk_level(score: float) -> str:
        """Map plagiarism score to risk category."""
        if score >= 70:
            return "critical"
        elif score >= 45:
            return "high"
        elif score >= 25:
            return "moderate"
        return "low"

    @staticmethod
    def _build_summary(
        score: float,
        risk: str,
        pairs: List[DocumentPairResult],
        total_matches: int,
    ) -> str:
        """Generate human-readable summary."""
        top_pair = max(pairs, key=lambda p: p.overall_similarity) if pairs else None
        summary = f"Plagiarism Score: {score}% ({risk.upper()} risk). "
        summary += f"Checked against {len(pairs)} reference document(s). "
        summary += f"Found {total_matches} sentence-level similarities above threshold. "
        if top_pair:
            summary += (
                f"Most similar document: '{top_pair.doc_b_title}' "
                f"({top_pair.overall_similarity}% similarity)."
            )
        return summary


# ── Module-level instance for easy import ─────────────────────

plagiarism_checker = PlagiarismChecker()
