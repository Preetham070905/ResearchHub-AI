import os
import logging
from typing import List
import fitz  # PyMuPDF
from services.paper_search import PaperResult

logger = logging.getLogger(__name__)

def extract_papers_from_workspace(workspace_id: int) -> List[PaperResult]:
    """
    Reads all uploaded PDFs from a workspace directory, extracts their text,
    and converts them into PaperResult objects that the agents can process.
    """
    upload_dir = f"uploads/workspace_{workspace_id}"
    papers = []
    
    if not os.path.exists(upload_dir):
        logger.warning(f"Workspace directory {upload_dir} not found.")
        return papers
        
    for filename in os.listdir(upload_dir):
        if not filename.lower().endswith(".pdf"):
            continue
            
        file_path = os.path.join(upload_dir, filename)
        logger.info(f"Extracting text from: {filename}")
        
        try:
            doc = fitz.open(file_path)
            
            # Extract first 3 pages as abstract/summary to avoid blowing up token limits
            text_chunks = []
            for i in range(min(3, len(doc))):
                page = doc.load_page(i)
                text_chunks.append(page.get_text())
                
            full_text = "\n".join(text_chunks).strip()
            
            # Create a PaperResult
            # We use the filename as the title, and the extracted text as the abstract
            # since the agents are prompted to read 'abstracts'.
            # We truncate to 3000 chars to be safe with LLM context windows if there are many papers.
            papers.append(PaperResult(
                title=filename.replace(".pdf", ""),
                abstract=full_text[:3000] + ("..." if len(full_text) > 3000 else ""),
                authors=["Uploaded Document"],
                url=f"local://workspace_{workspace_id}/{filename}",
                source="uploaded"
            ))
            
            doc.close()
        except Exception as e:
            logger.error(f"Failed to extract text from {filename}: {e}")
            
    return papers
