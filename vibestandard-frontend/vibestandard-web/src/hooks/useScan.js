import { useState, useCallback } from "react";
import { submitScan, pollUntilComplete } from "../api/scan";
import { ApiError } from "../api/client";

export function useScan() {
  const [scanState, setScanState] = useState({
    status: "idle",        // "idle" | "submitting" | "cloning" | "scanning" | "complete" | "failed"
    jobId: null,
    progressMessage: "",
    result: null,
    error: null,
  });

  const startScan = useCallback(async (githubUrl) => {
    setScanState({ status: "submitting", jobId: null, progressMessage: "Submitting scan...", result: null, error: null });

    try {
      const { job_id } = await submitScan(githubUrl);
      setScanState(prev => ({ ...prev, status: "cloning", jobId: job_id, progressMessage: "Cloning repository..." }));

      const finalStatus = await pollUntilComplete(
        job_id,
        (statusUpdate) => {
          setScanState(prev => ({
            ...prev,
            status: statusUpdate.status,
            progressMessage: statusUpdate.progress_message,
          }));
        }
      );

      if (finalStatus.status === "complete") {
        setScanState(prev => ({ ...prev, status: "complete", result: finalStatus.result, progressMessage: "Scan complete" }));
      } else {
        setScanState(prev => ({ ...prev, status: "failed", error: finalStatus.error || "Scan failed" }));
      }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unexpected error. Please try again.";
      setScanState(prev => ({ ...prev, status: "failed", error: message }));
    }
  }, []);

  const reset = useCallback(() => {
    setScanState({ status: "idle", jobId: null, progressMessage: "", result: null, error: null });
  }, []);

  return { scanState, startScan, reset };
}
