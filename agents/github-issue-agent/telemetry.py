import time
from langchain_core.callbacks import BaseCallbackHandler
from google.cloud import logging as gcp_logging

class MLOpsTelemetryHandler(BaseCallbackHandler):
    """
    Enterprise MLOps Telemetry: Intercepts Agent loops and streams 
    latency, token usage, and tool traces to Google Cloud Logging.
    """
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.tool_start_times = {}
        
        # Initialize GCP Logging Client (Falls back to standard print if not authenticated)
        try:
            client = gcp_logging.Client()
            self.logger = client.logger("ai-agent-telemetry")
            self.use_gcp = True
            print("🟢 GCP Cloud Logging connected.")
        except Exception:
            self.use_gcp = False
            print("🟡 GCP credentials not found. Defaulting to local console telemetry.")

    def log_event(self, event_name: str, payload: dict):
        """Formats and routes the telemetry payload."""
        payload["trace_id"] = self.trace_id
        
        if self.use_gcp:
            # Stream structured JSON directly to Google Cloud Logging
            self.logger.log_struct(payload, severity="INFO")
        else:
            # Local fallback for testing
            print(f"\n[TELEMETRY] {event_name.upper()} | {payload}")

    # --- LangChain Interceptors ---

    def on_llm_start(self, serialized: dict, prompts: list, **kwargs):
        self.log_event("llm_start", {"action": "Reasoning Loop Started", "model": serialized.get("name")})

    def on_llm_end(self, response, **kwargs):
        # Extract token usage from the LLM's response
        usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}
        if usage:
            self.log_event("token_metrics", {
                "action": "Token Consumption",
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            })

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
        tool_name = serialized.get("name", "unknown_tool")
        self.tool_start_times[tool_name] = time.time()
        self.log_event("tool_start", {"action": "Tool Executed", "tool_name": tool_name, "inputs": input_str})

    def on_tool_end(self, output: str, name: str, **kwargs):
        start_time = self.tool_start_times.get(name, time.time())
        latency = round(time.time() - start_time, 3)
        self.log_event("tool_end", {"action": "Tool Completed", "tool_name": name, "latency_seconds": latency})