"""Safe calculator skill."""

import ast
import operator
from typing import Any

from skills.base import Intent, Skill, SkillResponse


class CalculatorSkill(Skill):
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def __init__(self):
        super().__init__("calculator", "Safe arithmetic calculator")
        self.keywords = ["calculate", "math", "plus", "minus", "times", "divided"]
        self.example_intents = ["Calculate 2 + 2", "What is 12 divided by 3?"]

    def can_handle(self, intent: Intent) -> bool:
        return intent.intent_type == "calculate"

    def execute(self, intent: Intent) -> SkillResponse:
        expression = intent.parameters.get("expression") or intent.original_text
        try:
            result = self._evaluate(expression)
        except Exception as exc:
            return SkillResponse(f"I could not calculate that: {exc}", success=False)
        return SkillResponse(f"The result is {result:g}.", data={"expression": expression, "result": result})

    def _evaluate(self, expression: str) -> float:
        normalized = (
            expression.lower()
            .replace("calculate", "")
            .replace("what is", "")
            .replace("?", "")
            .replace("plus", "+")
            .replace("minus", "-")
            .replace("times", "*")
            .replace("multiplied by", "*")
            .replace("divided by", "/")
        )
        tree = ast.parse(normalized.strip(), mode="eval")
        return float(self._eval_node(tree.body))

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in self.OPERATORS:
            return self.OPERATORS[type(node.op)](self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.OPERATORS:
            return self.OPERATORS[type(node.op)](self._eval_node(node.operand))
        raise ValueError("unsupported expression")
