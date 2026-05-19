import { apiClient } from "./client";

export async function submitScan(githubUrl) {
  // POST /api/scan
  // Returns { job_id, status, message, estimated_duration_seconds }
  return apiClient.post("/api/scan", { github_url: githubUrl });
}

export async function getScanStatus(jobId) {
  // GET /api/scan/{jobId}/status
  // Returns JobStatusResponse
  return apiClient.get(`/api/scan/${jobId}/status`);
}

export async function pollUntilComplete(jobId, onStatusUpdate, intervalMs = 2000) {
  // Poll getScanStatus every intervalMs until status is "complete" or "failed"
  // Call onStatusUpdate(statusResponse) on every poll
  // Return the final status response
  // Stop polling after 10 minutes (300 polls at 2s) — throw error if exceeded
  // Use a simple recursive setTimeout pattern — not setInterval
  return new Promise((resolve, reject) => {
    let polls = 0;
    const maxPolls = 300;

    const poll = async () => {
      try {
        const status = await getScanStatus(jobId);
        onStatusUpdate(status);
        polls++;

        if (status.status === "complete" || status.status === "failed") {
          resolve(status);
          return;
        }

        if (polls >= maxPolls) {
          reject(new Error("Scan timed out after 10 minutes"));
          return;
        }

        setTimeout(poll, intervalMs);
      } catch (error) {
        reject(error);
      }
    };

    setTimeout(poll, intervalMs);
  });
}
