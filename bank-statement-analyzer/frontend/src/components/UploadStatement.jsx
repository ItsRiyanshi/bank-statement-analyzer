import { useRef, useState } from "react";
import { uploadPdf, uploadSms } from "../api/client.js";

export default function UploadStatement({ onUploaded }) {
  const [mode, setMode] = useState("pdf"); // "pdf" | "sms"
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [smsText, setSmsText] = useState("");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  const acceptFile = (selectedFile) => {
    if (!selectedFile) return;
    if (selectedFile.type !== "application/pdf" && !selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setStatus({ ok: false, message: "Choose a PDF bank statement to continue." });
      return;
    }
    setFile(selectedFile);
    setStatus(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    try {
      let res;
      if (mode === "pdf") {
        if (!file) {
          setLoading(false);
          return;
        }
        res = await uploadPdf(file);
      } else {
        const lines = smsText
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean);
        if (lines.length === 0) {
          setLoading(false);
          return;
        }
        res = await uploadSms(lines);
      }
      setStatus({ ok: true, message: `Imported ${res.transactions_added} transactions.` });
      onUploaded?.();
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || "Upload failed. If the backend is starting up, please try again in a few seconds.";
      setStatus({ ok: false, message: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="upload-card bg-white rounded-2xl shadow-sm border border-neutral-200 p-6">
      <div className="upload-card-heading"><div><p className="section-kicker">SECURE IMPORT</p><h3>Import transactions</h3></div><span className="secure-label"><span /> Encrypted in transit</span></div>

      <div className="mode-switch" role="tablist" aria-label="Import method">
        <button
          type="button"
          onClick={() => setMode("pdf")}
          role="tab" aria-selected={mode === "pdf"}
          className={`mode-option${mode === "pdf" ? " selected" : ""}`}
        >
          <span className="mode-option-icon">PDF</span> Bank statement
        </button>
        <button
          type="button"
          onClick={() => setMode("sms")}
          role="tab" aria-selected={mode === "sms"}
          className={`mode-option${mode === "sms" ? " selected" : ""}`}
        >
          <span className="mode-option-icon">SMS</span> Transaction alerts
        </button>
      </div>

      {mode === "pdf" ? (
        <>
          <div className={`drop-zone${dragging ? " dragging" : ""}${file ? " has-file" : ""}`}
            onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
            onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false); }}
            onDrop={(event) => { event.preventDefault(); setDragging(false); acceptFile(event.dataTransfer.files[0]); }}>
            <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            onChange={(event) => acceptFile(event.target.files[0])}
            className="visually-hidden-file"
            />
            <span className="drop-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6M12 18v-6m-3 3 3-3 3 3" /></svg></span>
            {file ? <><strong>{file.name}</strong><span>{(file.size / (1024 * 1024)).toFixed(2)} MB · Ready to analyze</span></> : <><strong>Drop your PDF statement here</strong><span>or <button type="button" className="browse-button" onClick={() => fileInputRef.current?.click()}>browse files</button></span><small>PDF format · Processed privately on your server</small></>}
          </div>
          <p className="privacy-copy"><span>◈</span> Runs locally via PyMuPDF + Tesseract OCR. No data leaves your server.</p>
        </>
      ) : (
        <>
          <label className="field-label" htmlFor="sms-alerts">Paste transaction messages</label>
          <textarea
            id="sms-alerts"
            value={smsText}
            onChange={(e) => setSmsText(e.target.value)}
            placeholder={"Paste bank SMS alerts, one per line, e.g.\nRs.500 debited from A/c XX1234 on 05-Sep-2026 for GROCERY. Avl Bal Rs.10000 -Bank"}
            rows={8}
            className="sms-textarea"
          />
          <p className="sms-help">
            Each line is parsed as one SMS message (date, amount, and credit/debit direction are detected automatically).
          </p>
        </>
      )}

      <button
        type="submit"
        disabled={loading || (mode === "pdf" ? !file : !smsText.trim())}
        className="upload-submit"
      >
        {loading ? <><span className="button-spinner" /> Processing statement...</> : <>Upload &amp; analyze <span aria-hidden="true">↗</span></>}
      </button>
      {status && (
        <div className={`upload-status ${status.ok ? "success" : "failure"}`} role="status"><span>{status.ok ? "✓" : "!"}</span>{status.message}</div>
      )}
    </form>
  );
}
