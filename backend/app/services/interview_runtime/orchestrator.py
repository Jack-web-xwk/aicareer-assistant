from enum import Enum
from typing import Any, Dict, List, Optional


class RoundPhase(str, Enum):
    INTRO = "intro"
    TECHNICAL_CORE = "technical_core"
    DEEP_DIVE = "deep_dive"
    WRAP_UP = "wrap_up"


class InterviewRuntimeV2:
    """Runtime controller for interview turn lifecycle and event shaping."""

    def __init__(self, min_rounds: int, max_rounds: int):
        self.min_rounds = max(1, min_rounds)
        self.max_rounds = max(self.min_rounds, max_rounds)

    def _phase_of_round(self, current_round: int) -> RoundPhase:
        if current_round <= 1:
            return RoundPhase.INTRO
        if current_round < self.min_rounds:
            return RoundPhase.TECHNICAL_CORE
        if current_round < self.max_rounds:
            return RoundPhase.DEEP_DIVE
        return RoundPhase.WRAP_UP

    def build_round_progress(self, state: Dict[str, Any]) -> Dict[str, Any]:
        round_no = int(state.get("question_count", 1) or 1)
        phase = self._phase_of_round(round_no)
        return {
            "round": round_no,
            "min_rounds": self.min_rounds,
            "max_rounds": self.max_rounds,
            "phase": phase.value,
            "can_finish": round_no >= self.min_rounds,
        }

    def enforce_finish_guardrails(
        self,
        prev_state: Dict[str, Any],
        next_state: Dict[str, Any],
        force_end: bool = False,
    ) -> Dict[str, Any]:
        """Prevent early auto-finish before min_rounds unless explicit end."""
        merged = dict(next_state)
        round_no = int(merged.get("question_count", 1) or 1)
        is_finished = bool(merged.get("is_finished", False))
        if is_finished and round_no < self.min_rounds and not force_end:
            merged["is_finished"] = False
            merged["current_question"] = "我们继续下一轮。请结合一个真实项目，详细说明你如何定位并解决一次线上性能问题。"
        return merged

    def build_events(
        self,
        prev_state: Dict[str, Any],
        new_state: Dict[str, Any],
        transcript_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        events.append(
            {
                "type": "round_progress",
                "data": self.build_round_progress(new_state),
            }
        )
        if transcript_text:
            events.append(
                {
                    "type": "transcript_final",
                    "data": {"text": transcript_text},
                }
            )
        assistant_text = new_state.get("current_question")
        if assistant_text:
            events.append(
                {
                    "type": "interviewer_reply",
                    "data": {"text": assistant_text},
                }
            )
        if new_state.get("audio_output"):
            events.append(
                {
                    "type": "interviewer_audio",
                    "data": {"audio_base64": new_state.get("audio_output")},
                }
            )
        if new_state.get("is_finished"):
            events.append({"type": "session_completed", "data": {"done": True}})
        return events
