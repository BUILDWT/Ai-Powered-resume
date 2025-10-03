import logging
from fastapi import FastAPI, HTTPException, Depends, Security, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader

from backend.models.schemas import ChatRequest, ChatResponse, HealthCheckResponse, ErrorResponse
from backend.services.vector_store import vector_store
from backend.services.llm_service import llm_service
from backend.services.document_processor import document_processor
from backend.utils.config import config
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Portfolio Assistant API",
    description="API for a RAG-based AI agent to chat about portfolio documents.",
    version="1.0.0"
)

# --- CORS Middleware ---
# Allows the frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Key Security ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    """Dependency to validate the API key."""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key

# --- API Endpoints ---

@app.get("/", include_in_schema=False)
def root():
    return {"message": "Welcome to the AI Portfolio Assistant API!"}

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Monitoring"],
    summary="Perform a Health Check",
    description="Returns a status of 'ok' if the API is running."
)
def health_check():
    """Health check endpoint to verify API is live."""
    return HealthCheckResponse(status="ok")

@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["AI Chat"],
    summary="Chat with the AI Assistant",
    dependencies=[Depends(get_api_key)],
    responses={404: {"model": ErrorResponse, "description": "No relevant information found."}}
)
def chat_with_agent(request: ChatRequest):
    """
    Receives a user query, finds relevant document chunks, and generates a response.
    """
    logger.info(f"Received chat request with query: '{request.query}'")
    
    # 1. Find relevant document chunks from the vector store
    relevant_chunks = vector_store.find_similar_chunks(request.query, top_k=3)
    
    if not relevant_chunks:
        logger.warning("No relevant chunks found for the query.")
        raise HTTPException(status_code=404, detail="I don't have enough information to answer that question.")
        
    # 2. Generate a response using the LLM
    answer = llm_service.generate_response(request.query, relevant_chunks)
    
    return ChatResponse(answer=answer, source_chunks=relevant_chunks)

@app.post(
    "/upload-document",
    tags=["Document Management"],
    summary="Upload a PDF document for processing",
    dependencies=[Depends(get_api_key)],
    status_code=201
)
async def upload_document(file: UploadFile = File(..., description="The PDF file to be processed.")):
    """
    Uploads a PDF, processes it, and stores it for the RAG system.
    This endpoint will replace any existing document with the same name.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is supported.")

    document_id = file.filename
    logger.info(f"Received document for upload: {document_id}")

    try:
        # --- Store original file in Google Cloud Storage (optional but good practice) ---
        storage_client = storage.Client(project=config.GCP_PROJECT_ID)
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        blob = bucket.blob(document_id)
        
        contents = await file.read()
        blob.upload_from_string(contents, content_type=file.content_type)
        logger.info(f"Uploaded original file to GCS: gs://{config.GCS_BUCKET_NAME}/{document_id}")
        
        # Reset stream position to the beginning for processing
        await file.seek(0)

        # --- Process and store in vector store ---
        # 1. Process the PDF to get text chunks and embeddings
        processed_chunks = document_processor.process_pdf(file.file)

        if not processed_chunks:
            raise HTTPException(status_code=400, detail="Could not extract any content from the PDF.")

        # 2. Delete old chunks if they exist
        vector_store.delete_document(document_id)

        # 3. Add new chunks to the vector store
        vector_store.add_documents(processed_chunks, document_id)

        return {"message": f"Document '{document_id}' processed and stored successfully."}

    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
