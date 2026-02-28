"""
Paper Search Service — fetches papers from arXiv and PubMed.

WHY TWO SOURCES:
- arXiv: Strong for CS, ML, physics, math — has full abstracts immediately
- PubMed: Strong for biomedical, life sciences — broadens coverage

HOW IT WORKS:
1. arXiv: HTTP GET to their Atom XML API → parse XML → extract title/abstract/authors/url
2. PubMed: Two-step process:
   a. ESearch → get paper IDs matching query
   b. EFetch → get full details (title, abstract) for those IDs
3. Both run concurrently via asyncio.gather() for speed

Returns a list of PaperResult dataclass objects with a unified schema.
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from typing import List
import httpx
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class PaperResult:
    """Unified paper format from any source."""
    title: str
    abstract: str
    authors: List[str]
    url: str
    source: str  # "arxiv" or "pubmed"

    def to_dict(self):
        return asdict(self)


# ======================== arXiv ========================

async def _search_arxiv(query: str, max_results: int = None) -> List[PaperResult]:
    """
    Search arXiv via their Atom API.
    Docs: https://info.arxiv.org/help/api/basics.html
    """
    max_results = max_results or settings.ARXIV_MAX_RESULTS
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }

    papers = []
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

        # Parse Atom XML
        root = ET.fromstring(response.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            link = entry.find("atom:id", ns)

            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns)
                if name is not None and name.text:
                    authors.append(name.text.strip())

            papers.append(PaperResult(
                title=title.text.strip().replace("\n", " ") if title is not None and title.text else "Untitled",
                abstract=summary.text.strip().replace("\n", " ") if summary is not None and summary.text else "",
                authors=authors,
                url=link.text.strip() if link is not None and link.text else "",
                source="arxiv"
            ))

        logger.info(f"arXiv returned {len(papers)} papers for query: {query}")

    except Exception as e:
        logger.error(f"arXiv search failed: {e}")

    return papers


# ======================== PubMed ========================

async def _search_pubmed(query: str, max_results: int = None) -> List[PaperResult]:
    """
    Search PubMed via NCBI E-utilities (ESearch + EFetch).
    Two-step process because ESearch only returns IDs, not full records.
    """
    max_results = max_results or settings.PUBMED_MAX_RESULTS
    papers = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1: ESearch — get matching paper IDs
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance"
            }

            search_resp = await client.get(search_url, params=search_params)
            search_resp.raise_for_status()
            search_data = search_resp.json()

            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                logger.info(f"PubMed: No results for query: {query}")
                return papers

            # Step 2: EFetch — get full records for those IDs
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml"
            }

            fetch_resp = await client.get(fetch_url, params=fetch_params)
            fetch_resp.raise_for_status()

        # Parse PubMed XML
        root = ET.fromstring(fetch_resp.text)

        for article in root.findall(".//PubmedArticle"):
            # Title
            title_el = article.find(".//ArticleTitle")
            title = title_el.text.strip() if title_el is not None and title_el.text else "Untitled"

            # Abstract
            abstract_parts = []
            for abs_text in article.findall(".//AbstractText"):
                if abs_text.text:
                    abstract_parts.append(abs_text.text.strip())
            abstract = " ".join(abstract_parts)

            # Authors
            authors = []
            for author in article.findall(".//Author"):
                last = author.find("LastName")
                first = author.find("ForeName")
                if last is not None and last.text:
                    name = last.text
                    if first is not None and first.text:
                        name = f"{first.text} {last.text}"
                    authors.append(name)

            # PMID for URL
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None and pmid_el.text else ""
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

            papers.append(PaperResult(
                title=title,
                abstract=abstract,
                authors=authors,
                url=url,
                source="pubmed"
            ))

        logger.info(f"PubMed returned {len(papers)} papers for query: {query}")

    except Exception as e:
        logger.error(f"PubMed search failed: {e}")

    return papers


# ======================== Combined Search ========================

async def search_papers(query: str, max_results: int = 5) -> List[PaperResult]:
    """
    Search both arXiv and PubMed concurrently.
    Returns combined list of PaperResult objects.
    """
    arxiv_papers, pubmed_papers = await asyncio.gather(
        _search_arxiv(query, max_results=max_results),
        _search_pubmed(query, max_results=max_results),
        return_exceptions=True
    )

    # Handle cases where one source fails
    results = []
    if isinstance(arxiv_papers, list):
        results.extend(arxiv_papers)
    else:
        logger.error(f"arXiv search raised exception: {arxiv_papers}")

    if isinstance(pubmed_papers, list):
        results.extend(pubmed_papers)
    else:
        logger.error(f"PubMed search raised exception: {pubmed_papers}")

    logger.info(f"Total papers found: {len(results)} for query: {query}")
    return results
