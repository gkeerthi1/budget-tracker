// Single place to change the backend URL.
// Flask backend must run with CORS enabled and supports_credentials=True
// (see note at bottom of this handoff) since the session cookie has to
// travel cross-origin from localhost:4200 -> localhost:5000.
export const API_BASE = 'http://localhost:5000/api';
