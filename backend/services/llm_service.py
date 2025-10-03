import logging
from typing import List
import vertexai
from vertexai.generative_models import GenerativeModel
from backend.utils.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with the Large Language Model (LLM) on Vertex AI.
    """
    def __init__(self):
        try:
            # Initialize Vertex AI
            vertexai.init(project=config.GCP_PROJECT_ID, location=config.GCP_REGION)
            # Load the specified generative model
            self.model = GenerativeModel(config.VERTEX_AI_MODEL_NAME)
            logger.info("Vertex AI and GenerativeModel initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise

    def generate_response(self, query: str, context_chunks: List[str]) -> str:
        """
        Generates a response from the LLM based on a query and context.

        Args:
            query: The user's question.
            context_chunks: A list of relevant text chunks from documents.

        Returns:
            The generated answer as a string.
        """
        logger.info("Generating response from LLM.")
        
        # Prompt Engineering: Create a detailed prompt for the LLM
        context_str = "\n\n".join(context_chunks)
        prompt = f"""
        You are a professional and helpful AI assistant for a personal portfolio website.
        Your role is to answer questions about the portfolio owner based ONLY on the provided context.
        If the answer is not found in the context, you must state that you don't have enough information to answer.
        Do not make up information. Be concise, friendly, and professional.

        CONTEXT:
        ---
        {context_str}
        ---

        QUESTION: {query}

        ANSWER:
        """

        try:
            # Generate content using the model
            response = self.model.generate_content(prompt)
            answer = response.text
            logger.info("Successfully generated response from LLM.")
            return answer
        except Exception as e:
            logger.error(f"An error occurred during LLM response generation: {e}")
            return "I'm sorry, but I encountered an error while trying to generate a response. Please try again later."

# Singleton instance
llm_service = LLMService()
