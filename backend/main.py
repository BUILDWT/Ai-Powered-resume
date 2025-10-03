import os
import boto3
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import uuid

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")
API_KEY = os.getenv("API_KEY")

s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/health")
def health():
    return {"status": "ok"}

# Chat endpoint (mock for now)
@app.post("/chat")
async def chat(query: dict):
    return {"answer": f"Received your query: {query.get('query')}", "source_chunks": []}

# Upload document
@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...), x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    file_id = str(uuid.uuid4())
    s3_client.upload_fileobj(file.file, S3_BUCKET_NAME, f"{file_id}.pdf")

    # Store metadata in DynamoDB
    table.put_item(Item={"id": file_id, "filename": file.filename})
    return {"message": f"Document '{file.filename}' uploaded successfully."}
