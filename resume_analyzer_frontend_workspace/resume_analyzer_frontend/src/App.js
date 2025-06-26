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
  // Handles form submission and upload via POST to backend
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

      // The backend is expected at /analyze-resume/; adjust this if deployed behind a proxy.
      const response = await fetch(
        "http://localhost:3001/analyze-resume/",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        // Try to extract details from JSON
        let errDetail = "API request failed";
        try {
          const { detail } = await response.json();
          errDetail = detail || errDetail;
        } catch {
          // Ignore, use generic
        }
        throw new Error(errDetail);
      }

      const json = await response.json();
      setResult(json);
    } catch (err) {
      setResult(null);
      setError(
        err?.message ||
          "Failed to submit. Please check your connection and input."
      );
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
