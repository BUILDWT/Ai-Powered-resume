import logging
import numpy as np
from typing import List, Dict, Any
from google.cloud import firestore
from backend.utils.config import config
from backend.services.document_processor import document_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    """
    Manages vector storage and retrieval using Google Firestore.
    """
    def __init__(self):
        try:
            # Initialize Firestore client
            self.db = firestore.Client(project=config.GCP_PROJECT_ID)
            self.collection = self.db.collection(config.FIRESTORE_COLLECTION)
            logger.info("Firestore client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise

    def add_documents(self, documents: List[Dict[str, Any]], document_id: str):
        """

        Adds document chunks and their embeddings to Firestore in a batch.

        Args:
            documents: A list of document chunks, each with 'text' and 'embedding'.
            document_id: The unique identifier for the source document.
        """
        logger.info(f"Adding {len(documents)} chunks for document '{document_id}' to Firestore.")
        batch = self.db.batch()
        for i, doc in enumerate(documents):
            doc_ref = self.collection.document(f"{document_id}_{i}")
            doc_data = {
                "document_id": document_id,
                "chunk_index": i,
                "text": doc["text"],
                "embedding": doc["embedding"]
            }
            batch.set(doc_ref, doc_data)
        
        try:
            batch.commit()
            logger.info("Successfully committed document chunks to Firestore.")
        except Exception as e:
            logger.error(f"Failed to commit batch to Firestore: {e}")
            raise

    def find_similar_chunks(self, query: str, top_k: int = 5) -> List[str]:
        """
        Finds the most similar document chunks to a given query.

        Args:
            query: The user's query string.
            top_k: The number of top similar chunks to return.

        Returns:
            A list of the most relevant text chunks.
        """
        logger.info(f"Finding {top_k} similar chunks for query: '{query}'")
        try:
            # Generate embedding for the user's query
            query_embedding = document_processor.embedding_model.encode([query])[0]
            query_vector = np.array(query_embedding)

            # Retrieve all document chunks from Firestore
            all_docs = self.collection.stream()

            similarities = []
            for doc in all_docs:
                doc_data = doc.to_dict()
                if "embedding" in doc_data and "text" in doc_data:
                    doc_vector = np.array(doc_data["embedding"])
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_vector, doc_vector)
                    similarities.append((similarity, doc_data["text"]))

            if not similarities:
                logger.warning("No documents found in the vector store.")
                return []

            # Sort by similarity score in descending order
            similarities.sort(key=lambda x: x[0], reverse=True)

            # Return the text of the top_k most similar chunks
            top_chunks = [text for _, text in similarities[:top_k]]
            logger.info(f"Found {len(top_chunks)} relevant chunks.")
            return top_chunks
        except Exception as e:
            logger.error(f"An error occurred during similarity search: {e}")
            return []

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculates cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
        return dot_product / (norm_vec1 * norm_vec2)

    def delete_document(self, document_id: str):
        """Deletes all chunks associated with a document_id."""
        logger.info(f"Deleting all chunks for document_id: {document_id}")
        docs = self.collection.where("document_id", "==", document_id).stream()
        batch = self.db.batch()
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
        
        if count > 0:
            batch.commit()
            logger.info(f"Deleted {count} chunks for document_id: {document_id}")
        else:
            logger.info(f"No chunks found for document_id: {document_id}")


# Singleton instance
vector_store = VectorStore()
