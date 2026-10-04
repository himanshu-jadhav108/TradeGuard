from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field
from app.domain.models import ParsedIntent


class InterpretationResult(BaseModel):
    success: bool
    intent: Optional[ParsedIntent] = None
    clarification: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class BaseInterpreter(ABC):
    """
    Abstract interpreter provider.
    Separates natural language intent parsing from execution and validation.
    Rule-based interpreter serves as the authoritative, deterministic baseline.
    """

    @abstractmethod
    def parse(self, prompt: str) -> InterpretationResult:
        """Parse natural language prompt into a structured intent or clarification."""
        pass
