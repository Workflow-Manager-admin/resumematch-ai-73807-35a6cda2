from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from typing import Optional
import fitz  # PyMuPDF for PDF text extraction
import io

# PUBLIC_INTERFACE
class AnalysisResult(BaseModel):
    score: float = Field(..., description="Compatibility score between 0 and 1")
    summary: str = Field(..., description="Natural language summary of compatibility")
    details: Optional[str] = Field(None, description="Detailed findings explanation")

# PUBLIC_INTERFACE
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Description of error")

# OpenAPI tag definitions
openapi_tags = [
    {
        "name": "Resume Analysis",
        "description": "Endpoints for analyzing resume PDF against a job description."
    }
]

app = FastAPI(
    title="Resume Analyzer API",
    description="Backend service for analyzing uploaded resumes against a job description using (placeholder) SambaNova LLaMA-4 Maverick 17B model.",
    version="1.0.0",
    openapi_tags=openapi_tags
)

# CORS setup for frontend integration:
# These origins should match deployed frontend(s)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000",
    "https://beta.kavia.ai",
    "https://vscode-internal-5713-beta.beta01.cloud.kavia.ai:3000",
    # Add any other deployed frontend URLs as needed
]
# If you deploy somewhere else, add the domain (or wildcard for dev) here.

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

MAX_PDF_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB


# PUBLIC_INTERFACE
@app.get("/", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.post(
    "/analyze-resume/",
    response_model=AnalysisResult,
    tags=["Resume Analysis"],
    summary="Analyze Resume for Job Compatibility",
    description="""
    Accepts a PDF resume and a job description, analyzes them for compatibility using an AI model,
    and returns a structured analysis result.
    """,
    responses={
        200: {"model": AnalysisResult, "description": "Analysis result returned successfully."},
        400: {"model": ErrorResponse, "description": "Invalid input."},
        500: {"model": ErrorResponse, "description": "Processing error."}
    },
)
async def analyze_resume(
    file: UploadFile = File(..., description="Resume PDF file to upload. Must be a .pdf, ≤ 2 MB.",
                            examples={"application/pdf": {"summary": "A PDF file"}}),
    job_description: str = Form(..., min_length=10, description="The job description text. Multiline supported.")
) -> AnalysisResult:
    """
    Upload a resume PDF and job description text, then receive a compatibility analysis result.

    **Parameters:**
    - **file**: PDF file (.pdf, max 2MB)
    - **job_description**: Multiline job description (text)

    **Returns:**
    - **score**: Compatibility score (0-1)
    - **summary**: Human-readable summary
    - **details**: Optional, detailed explanation

    ---

    **Note:** The compatibility analysis uses a placeholder for SambaNova LLaMA-4 Maverick 17B API integration.
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a PDF (.pdf extension)."
        )
    # Validate file size (stream from upload since UploadFile exposes .file)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    if file_size > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="PDF file size must be ≤ 2MB."
        )
    file.file.seek(0)
    pdf_bytes = await file.read()
    try:
        pdf_text = extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Failed to parse PDF: " + str(e)
        )

    if not pdf_text or len(pdf_text) < 30:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Could not extract sufficient text from the resume PDF."
        )

    # Placeholder: This is where the SambaNova API integration would go
    try:
        result = perform_compatibility_analysis(pdf_text, job_description)
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during compatibility analysis: " + str(e)
        )

    return AnalysisResult(**result)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF document using PyMuPDF.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        raise RuntimeError("PDF parsing failed: " + str(e))


# PUBLIC_INTERFACE
def perform_compatibility_analysis(resume_text: str, job_description: str) -> dict:
    """
    PUBLIC_INTERFACE
    Performs compatibility analysis by sending the resume and job description to SambaNova API.

    Calls the SambaNova API v1 endpoint using the preferred model and payload schema,
    handles errors, and parses the response into dict with the expected fields.

    Args:
        resume_text (str): Extracted text from the user's PDF resume.
        job_description (str): Job description string text.

    Returns (dict):
        - score (float): Compatibility score (0-1)
        - summary (str): Human-readable summary
        - details (str): More detailed information

    Raises:
        RuntimeError: If the API call fails or produces an invalid response.
    """
    import os
    import httpx

    # Securely load the SambaNova API Key from environment or .env (set up in deployment)
    sambanova_api_key = os.getenv("SAMBANOVA_API_KEY")
    if not sambanova_api_key:
        # Try .env (if python-dotenv is installed)
        try:
            from dotenv import load_dotenv
            load_dotenv()
            sambanova_api_key = os.getenv("SAMBANOVA_API_KEY")
        except Exception:
            sambanova_api_key = None
    if not sambanova_api_key:
        raise RuntimeError("SambaNova API key is not configured. Set SAMBANOVA_API_KEY in environment or .env.")

    endpoint = "https://api.sambanova.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {sambanova_api_key}",
        "Content-Type": "application/json"
    }
    # Build prompt/messages as expected by the API
    prompt_messages = [
        {
            "role": "system", 
            "content": (
                "You are a helpful assistant for resume-job matching. "
                "You will receive a resume and a job description; "
                "analyze their compatibility and reply with: "
                "a JSON object containing a compatibility score (float 0-1), "
                "a brief summary, and detailed findings. "
                "Only reply with the JSON object."
            )
        },
        {
            "role": "user",
            "content": (
                f"Resume:\n{resume_text}\n\nJob Description:\n{job_description}\n\n"
                "Reply strictly in JSON as: {\"score\": <0-1>, \"summary\": \"...\", \"details\": \"...\"}."
            )
        }
    ]
    payload = {
        "stream": False,
        "model": "Meta-Llama-3.3-70B-Instruct",
        "messages": prompt_messages,
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        # SambaNova returns a "choices" list similar to OpenAI; parse accordingly.
        data = resp.json()
        if not data or "choices" not in data or not data["choices"]:
            raise RuntimeError(f"Unexpected SambaNova API response: {data}")

        # The format is expected to be in data["choices"][0]["message"]["content"]
        message_content = data["choices"][0]["message"]["content"]
        # The actual model output should be a JSON string as prompted.
        import json as pyjson
        try:
            analysis_result = pyjson.loads(message_content)
        except Exception as json_error:
            # If response is not a valid JSON object, provide diagnostic details.
            raise RuntimeError(f"SambaNova model did not return valid JSON: {message_content}") from json_error

        # Validate required fields
        score = analysis_result.get("score")
        summary = analysis_result.get("summary")
        details = analysis_result.get("details")
        if not isinstance(score, (float, int)) or summary is None:
            raise RuntimeError("Missing or invalid fields in SambaNova result: " + str(analysis_result))

        # Score normalization (ensure 0..1)
        score = max(0.0, min(1.0, float(score)))
        return {
            "score": score,
            "summary": str(summary),
            "details": str(details) if details is not None else "",
        }
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"SambaNova API HTTP error: {str(e)} - {getattr(e.response, 'text', '')}")
    except Exception as e:
        raise RuntimeError(f"SambaNova API integration error: {str(e)}")


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    """
    Custom JSON error responses for HTTPExceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    """
    Catch-all for internal server errors.
    """
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. " + str(exc)}
    )

# OpenAPI WebSocket usage doc endpoint in case future real-time is needed
@app.get("/docs/websocket-usage", tags=["Resume Analysis"])
def websocket_usage_notes():
    """
    (Reserved for future use)
    If WebSocket-based notification or real-time connectivity is needed for AI analysis,
    document usage here and implement the FastAPI WebSocket route.
    """
    return {"detail": "No WebSocket API available yet. All analysis is synchronous via POST /analyze-resume/."}

