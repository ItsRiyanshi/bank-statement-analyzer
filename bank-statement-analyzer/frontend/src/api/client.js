import axios from "axios";

// Resolve API base URL:
// 1. In production, use VITE_API_BASE provided at build time (e.g. Render backend URL).
//    If omitted in production, fallback to relative origin ("") to prevent hardcoding localhost.
// 2. In local development (Vite dev server), fall back to http://localhost:8000.
const resolveApiBase = () => {
  const envUrl = import.meta.env.VITE_API_BASE;
  if (envUrl && typeof envUrl === "string" && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, "");
  }
  if (import.meta.env.DEV) {
    return "http://localhost:8000";
  }
  return "";
};

export const API_BASE = resolveApiBase();

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000, // 60s timeout accommodates Render free-tier cold starts
});

export const getSummary = () => api.get("/api/analytics/summary").then((r) => r.data);
export const getHealthScore = () => api.get("/api/analytics/health-score").then((r) => r.data);
export const getRecurring = () => api.get("/api/analytics/recurring").then((r) => r.data);
export const getAnomalies = () => api.get("/api/analytics/anomalies").then((r) => r.data);
export const getSummaryText = () => api.get("/api/analytics/summary-text").then((r) => r.data);
export const getTransactions = (params) => api.get("/api/transactions", { params }).then((r) => r.data);

export const uploadPdf = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/api/upload/pdf", form, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
};

// smsTexts: array of strings, one per SMS message. The backend expects
// repeated `sms_texts` form fields (List[str] = Form(...)), so each
// message is appended under the same key.
export const uploadSms = (smsTexts) => {
  const form = new FormData();
  smsTexts.forEach((text) => form.append("sms_texts", text));
  return api.post("/api/upload/sms", form, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
};

export const getSafeToSpend = () => api.get("/api/calendar/safe-to-spend").then((r) => r.data);
export const getEvents = () => api.get("/api/calendar/events").then((r) => r.data);
export const addEvent = (payload) => api.post("/api/calendar/events", payload).then((r) => r.data);
export const deleteEvent = (id) => api.delete(`/api/calendar/events/${id}`).then((r) => r.data);
export const syncGoogleCalendar = () => api.post("/api/calendar/sync-google").then((r) => r.data);

export const getBudgetPlan = () => api.get("/api/budget/plan").then((r) => r.data);
