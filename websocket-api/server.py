import os
import base64
import boto3
import logging
import uvicorn
from fastapi import FastAPI, WebSocket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configurations
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_BUCKET_NAME = "pooja-websocket-files"  # Explicit bucket name
UPLOAD_FOLDER = "uploads"
FILE_NAME = "parrot_sound.wav"  # Explicit file name

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# FastAPI app
app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket connection established.")

    try:
        while True:
            data = await websocket.receive_json()
            file_data = base64.b64decode(data.get("data", ""))  # Decode base64 data

            file_path = os.path.join(UPLOAD_FOLDER, FILE_NAME)
            with open(file_path, "wb") as f:
                f.write(file_data)
            logging.info(f"File saved locally: {file_path}")

            # Upload to S3
            try:
                s3_client.upload_file(file_path, S3_BUCKET_NAME, FILE_NAME)
                logging.info(f"File uploaded to S3: s3://{S3_BUCKET_NAME}/{FILE_NAME}")
                await websocket.send_text(f"File {FILE_NAME} uploaded successfully to {S3_BUCKET_NAME}!")
            except Exception as s3_error:
                logging.error(f"S3 Upload Error: {s3_error}")
                await websocket.send_text(f"S3 Upload Error: {str(s3_error)}")

            # Cleanup local file
            os.remove(file_path)

    except Exception as e:
        logging.error(f"WebSocket Error: {e}")
        await websocket.send_text(f"Error: {str(e)}")

