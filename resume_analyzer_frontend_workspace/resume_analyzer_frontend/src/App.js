import React, { useState, useRef, useEffect } from "react";
import "./App.css";

/**
 * PUBLIC_INTERFACE
 * Resume Analyzer App - single-page UI for PDF upload, job description, and results.
 */
function App() {
  // Theme and colors
  const [theme, setTheme] = useState("dark");
  // Form state
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  // UI state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null); // analysis result from backend
  const [error, setError] = useState("");
  // Reference for file input to reset
  const fileInputRef = useRef();

  // Palette (dark, modern minimal, as per requirements)
  // See also theme CSS variables in App.css

  // Apply theme to <html> attribute
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  // PUBLIC_INTERFACE
  // Toggle between light/dark mode (default dark)
  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  /**
   * Handles PDF file selection and validates file type (.pdf) and size (≤2MB).
   */
  // PUBLIC_INTERFACE
  function handleFileChange(e) {
    setError("");
    setResult(null);
    const f = e.target.files && e.target.files[0];
    if (!f) {
      setFile(null);
      return;
    }
    // Type check
    if (
      !(
        f.type === "application/pdf" ||
        (f.name && f.name.toLowerCase().endsWith(".pdf"))
      )
    ) {
      setFile(null);
      setError("Only PDF files are accepted.");
      fileInputRef.current.value = ""; // Reset
      return;
    }
    // Size check (≤2MB)
    if (f.size > 2 * 1024 * 1024) {
      setFile(null);
      setError("PDF must be ≤ 2MB in size.");
      fileInputRef.current.value = "";
      return;
    }
    setFile(f);
  }

  // PUBLIC_INTERFACE
  // Handles form submission and upload via POST to backend.
  /**
   * Submission handler for resume and job description.
   * 
   * BACKEND ENDPOINT & CORS DEVELOPER TROUBLESHOOTING NOTES:
   * - The backend endpoint is set by REACT_APP_BACKEND_URL or defaults to http://localhost:3001/analyze-resume/.
   * - CORS/network errors (manifest as "Failed to fetch" or generic network errors) are commonly due to:
   *     - Backend not running (check backend logs/container status).
   *     - Backend running on a different port or address (adjust URL accordingly).
   *     - CORS: Browser blocked request because backend does not allow frontend's origin.
   *         - See FastAPI's CORSMiddleware (backend/src/api/main.py); adjust `allow_origins` if restricting origins.
   *         - If using reverse proxy or deployed URLs, set React .env or deployment environment variable appropriately.
   * - In the browser dev tools' console/network, look for:
   *     - CORS policy errors in Console tab
   *     - Network 0 status or no response in Network tab
   * - For local/dev, both ports 3000 (frontend) and 3001 (backend) must be accessible from browser.
   */
  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setResult(null);

    if (!file) {
      setError("Please choose a PDF resume (max 2MB).");
      return;
    }
    if (jobDescription.trim().length < 10) {
      setError("Job description must be at least 10 characters.");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file, file.name);
      formData.append("job_description", jobDescription);

      // Dynamically set backend URL based on environment for seamless container dev/deploy
      const BACKEND_URL =
        process.env.REACT_APP_BACKEND_URL ||
        "http://localhost:3001/analyze-resume/";

      let response;
      try {
        response = await fetch(
          BACKEND_URL,
          {
            method: "POST",
            body: formData,
          }
        );
      } catch (networkError) {
        setLoading(false);
        setResult(null);
        // Likely CORS, server-down, or URL problem
        setError(
          "Network error: Could not reach backend API. " +
          "This may be due to a CORS issue, server is down, or URL mismatch. " +
          "Console may have more details. If running locally, ensure both frontend (port 3000) and backend (port 3001) are running and accessible."
        );
        // For CORS troubleshooting, log detailed info
        // eslint-disable-next-line no-console
        console.error("Network or CORS error when trying to reach backend at:", BACKEND_URL, networkError);
        return;
      }

      if (!response.ok) {
        // Try to extract details from JSON, if possible
        let errDetail = "API request failed";
        try {
          const { detail } = await response.json();
          errDetail = detail || errDetail;
        } catch (err2) {
          // Response is probably not JSON (e.g. CORS preflight block returns empty)
          errDetail = "API request failed: Server returned " + response.status + " (" + response.statusText + ").";
        }
        setResult(null);
        setError(
          errDetail +
          (response.status === 0
            ? " [CORS or server issue suspected. Check browser network tab and backend status.]"
            : "")
        );
        // eslint-disable-next-line no-console
        console.error("Non-2xx response from backend:", response.status, response.statusText, errDetail);
        return;
      }

      try {
        const json = await response.json();
        setResult(json);
      } catch (parseError) {
        setResult(null);
        setError(
          "Received invalid JSON from backend. There may be a server issue."
        );
        // eslint-disable-next-line no-console
        console.error("Could not parse backend JSON:", parseError);
      }
    } catch (err) {
      setResult(null);
      setError(
        (err && err.message) ||
          "Failed to submit. Please check your connection and input."
      );
      // eslint-disable-next-line no-console
      console.error("Unexpected error in submission handler:", err);
    } finally {
      setLoading(false);
    }
  }

  // PUBLIC_INTERFACE
  // Reset the form completely
  function handleReset() {
    setFile(null);
    setJobDescription("");
    setResult(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  return (
    <div className="App">
      <header className="analyzer-header">
        <h1 className="analyzer-title">ResumeMatch AI</h1>
        <button
          type="button"
          className="theme-toggle"
          onClick={toggleTheme}
          tabIndex={0}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
        </button>
      </header>
      <main className="analyzer-main">
        <form className="analyzer-form" onSubmit={handleSubmit}>
          <label className="form-label" htmlFor="resume-file">
            PDF Resume <span>*</span>
            <input
              ref={fileInputRef}
              type="file"
              id="resume-file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              required
              className="form-input-file"
              aria-describedby="file-reqs"
            />
          </label>
          <div className="input-description" id="file-reqs">
            Only <strong>.pdf</strong>, max 2MB.
          </div>
          <label className="form-label" htmlFor="job-desc">
            Job Description <span>*</span>
            <textarea
              id="job-desc"
              className="form-input-textarea"
              rows={6}
              value={jobDescription}
              minLength={10}
              maxLength={3000}
              required
              placeholder="Paste the job description here (minimum 10 characters)"
              onChange={(e) => {
                setJobDescription(e.target.value);
                setError("");
                setResult(null);
              }}
            />
          </label>
          <div className="analyzer-actions">
            <button
              className="analyzer-btn"
              type="submit"
              disabled={loading}
              aria-busy={loading}
            >
              {loading ? (
                <span className="btn-spinner" title="Analyzing..."></span>
              ) : (
                "Analyze"
              )}
            </button>
            <button
              className="analyzer-btn analyzer-btn-secondary"
              type="button"
              onClick={handleReset}
              disabled={loading}
              style={{ marginLeft: 12 }}
            >
              Reset
            </button>
          </div>
          {error && (
            <div className="analyzer-msg analyzer-error" role="alert">
              {error}
            </div>
          )}
        </form>
        <section className="analyzer-result-section">
          {loading && (
            <div className="analyzer-loading">
              <span className="loading-spinner"></span>
              <span>Analyzing resume...</span>
            </div>
          )}
          {result && (
            <ResultPanel result={result} />
          )}
        </section>
      </main>
      <footer className="analyzer-footer">
        <span>
          &copy; {new Date().getFullYear()} ResumeMatch AI. Powered by SambaNova LLaMA-4 Maverick 17B<sup>&trade;</sup>
        </span>
      </footer>
    </div>
  );
}

/**
 * PUBLIC_INTERFACE
 * Displays the compatibility analysis result in a modern panel.
 */
function ResultPanel({ result }) {
  return (
    <div className="analyzer-result-card">
      <h2 className="result-title">Analysis Result</h2>
      <div className="result-score">
        <span className="score-label">Compatibility Score:</span>
        <span className="score-value">
          {typeof result.score === "number"
            ? (result.score * 100).toFixed(1)
            : "—"}
          %
        </span>
      </div>
      <div className="result-summary">
        <span className="summary-label">Summary:</span>
        <p>{result.summary || "No summary available."}</p>
      </div>
      {result.details && (
        <div className="result-details">
          <span className="details-label">Details:</span>
          <pre>{result.details}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
