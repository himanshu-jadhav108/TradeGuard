from fastapi import HTTPException
from app.domain.models import ParsedIntent
from app.services.interpreter import InterpreterProvider, InterpretationResult


class IntentService:
    """
    Service layer for natural language trade intent interpretation.
    Enforces honest, grounded parsing through the InterpreterProvider without fake AI claims.
    """

    @classmethod
    def parse_natural_language(cls, prompt: str) -> ParsedIntent:
        result: InterpretationResult = InterpreterProvider.parse(prompt)

        if not result.success or not result.intent:
            detail_msg = result.error or result.clarification or "Unable to determine unambiguous trade intent."
            raise HTTPException(
                status_code=422,
                detail=detail_msg,
            )

        return result.intent

    @classmethod
    def parse_with_clarification(cls, prompt: str) -> InterpretationResult:
        """Returns structured result including clarification and suggestions when ambiguous."""
        return InterpreterProvider.parse(prompt)
