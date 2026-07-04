from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from domain.entities.models import ResolutionReport
from domain.ports import RequestLogger
from infrastructure.config.settings import Settings


class FileRequestLogger(RequestLogger):
    """Write per-request decision logs to logs/{request_id}.json."""

    def __init__(self, settings: Settings) -> None:
        self._logs_path = Path(settings.logs_path)
        self._logs_path.mkdir(parents=True, exist_ok=True)
        self._buffers: dict[str, dict[str, object]] = {}

    def get_log_path(self, request_id: str) -> str:
        return str(self._logs_path / f"{request_id}.json")

    def start_request(self, request_id: str, input_data: dict[str, object]) -> None:
        self._buffers[request_id] = {
            "requestId": request_id,
            "startedAt": datetime.now(timezone.utc).isoformat(),
            "input": input_data,
            "decisions": [],
            "toolCalls": [],
        }

    def log_decision(
        self,
        request_id: str,
        node: str,
        input_summary: str,
        output_summary: str,
        duration_ms: int,
    ) -> None:
        buffer = self._buffers.setdefault(request_id, {"decisions": [], "toolCalls": []})
        decisions = buffer.setdefault("decisions", [])
        if isinstance(decisions, list):
            decisions.append(
                {
                    "node": node,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "inputSummary": input_summary,
                    "outputSummary": output_summary,
                    "durationMs": duration_ms,
                }
            )

    def log_tool_call(
        self,
        request_id: str,
        tool: str,
        parameters: dict[str, object],
        result: dict[str, object],
        success: bool,
    ) -> None:
        buffer = self._buffers.setdefault(request_id, {"decisions": [], "toolCalls": []})
        tool_calls = buffer.setdefault("toolCalls", [])
        if isinstance(tool_calls, list):
            tool_calls.append(
                {
                    "tool": tool,
                    "parameters": parameters,
                    "result": result,
                    "success": success,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    def complete_request(
        self,
        request_id: str,
        output: ResolutionReport,
        elapsed_ms: int,
    ) -> None:
        buffer = self._buffers.get(request_id, {})
        buffer["completedAt"] = datetime.now(timezone.utc).isoformat()
        buffer["elapsedMs"] = elapsed_ms
        buffer["output"] = output.model_dump(mode="json")
        log_path = Path(self.get_log_path(request_id))
        log_path.write_text(json.dumps(buffer, indent=2, default=str), encoding="utf-8")
