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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
    Placeholder for the AI-powered compatibility analysis.

    In production, this function would call the SambaNova LLaMA-4 Maverick 17B API
    with the resume and job description, and parse the API's response.

    For now, it returns a dummy score with mock summary/details.

    Returns (dict):
        - score (float)
        - summary (str)
        - details (str)
    """
    # TODO: Replace with actual API call to SambaNova when available.
    import random
    fake_score = round(random.uniform(0.35, 0.95), 2)
    fake_summary = (
        "This is a simulated compatibility result between the resume and the job description. "
        "The real implementation will use SambaNova LLaMA-4 Maverick 17B for deep analysis."
    )
    fake_details = (
        f"Score is {fake_score}. This is a demo. Key skills are matched heuristically. "
        "Integration point for real LLM model."
    )
    return {
        "score": fake_score,
        "summary": fake_summary,
        "details": fake_details
    }


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

