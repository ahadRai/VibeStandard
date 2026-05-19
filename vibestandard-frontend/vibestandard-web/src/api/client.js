const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async post(path, body) {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: "Unknown error" }));
      throw new ApiError(error.error || "Request failed", response.status);
    }
    return response.json();
  }

  async get(path) {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: { "Accept": "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: "Unknown error" }));
      throw new ApiError(error.error || "Request failed", response.status);
    }
    return response.json();
  }
}

export class ApiError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
