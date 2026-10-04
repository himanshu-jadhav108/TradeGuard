from app.services.interpreter.base import BaseInterpreter, InterpretationResult
from app.services.interpreter.rule_based import RuleBasedInterpreter


class InterpreterProvider:
    """
    Interpreter provider factory.
    Authoritative baseline is RuleBasedInterpreter.
    Designed for pluggable LLM interpreters with strict JSON schema validation when configured.
    """

    _default_interpreter: BaseInterpreter = RuleBasedInterpreter()

    @classmethod
    def get_interpreter(cls) -> BaseInterpreter:
        return cls._default_interpreter

    @classmethod
    def parse(cls, prompt: str) -> InterpretationResult:
        return cls.get_interpreter().parse(prompt)
