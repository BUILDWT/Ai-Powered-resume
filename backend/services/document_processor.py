import logging
from typing import List, Dict, Any
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from backend.utils.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles processing of documents: text extraction, chunking, and embedding generation.
    """
    def __init__(self):
        try:
            # Initialize the sentence-transformer model for embeddings
            self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
            logger.info(f"Embedding model '{config.EMBEDDING_MODEL}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def process_pdf(self, file_stream) -> List[Dict[str, Any]]:
        """
        Processes a PDF file stream to extract text, chunk it, and generate embeddings.

        Args:
            file_stream: A file-like object representing the PDF.

        Returns:
            A list of dictionaries, where each dictionary represents a chunk
            with its text and vector embedding.
        """
        logger.info("Starting PDF processing.")
        try:
            text = self._extract_text_from_pdf(file_stream)
            chunks = self._chunk_text(text)
            
            if not chunks:
                logger.warning("No text chunks were generated from the PDF.")
                return []

            embeddings = self._generate_embeddings(chunks)
            
            processed_chunks = [
                {"text": chunk, "embedding": embedding.tolist()}
                for chunk, embedding in zip(chunks, embeddings)
            ]
            logger.info(f"Successfully processed PDF into {len(processed_chunks)} chunks.")
            return processed_chunks
        except Exception as e:
            logger.error(f"An error occurred during PDF processing: {e}")
            return []

    def _extract_text_from_pdf(self, file_stream) -> str:
        """Extracts text from a PDF file stream."""
        logger.info("Extracting text from PDF.")
        pdf_reader = PdfReader(file_stream)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        logger.info(f"Extracted {len(text)} characters from PDF.")
        return text

    def _chunk_text(self, text: str) -> List[str]:
        """Splits text into overlapping chunks."""
        logger.info(f"Chunking text with chunk_size={config.CHUNK_SIZE} and overlap={config.CHUNK_OVERLAP}.")
        chunks = []
        start = 0
        while start < len(text):
            end = start + config.CHUNK_SIZE
            chunks.append(text[start:end])
            start += config.CHUNK_SIZE - config.CHUNK_OVERLAP
        logger.info(f"Generated {len(chunks)} chunks.")
        return chunks

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates vector embeddings for a list of text chunks."""
        logger.info(f"Generating embeddings for {len(texts)} chunks.")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        logger.info("Embeddings generated successfully.")
        return embeddings

# Singleton instance
document_processor = DocumentProcessor()
