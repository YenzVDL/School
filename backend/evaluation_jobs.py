"""Historical AI judgment schema; AI evaluation execution is disabled."""
from pydantic import Field
from typing import Literal
from .schema import Strict
from .execution_policy import reject_ai_evaluation


class AICriterion(Strict):
    value: Literal['Yes', 'No']
    explanation: str = Field(min_length=1, max_length=2000)
    context: str = Field(min_length=1, max_length=3000)


class AIJudgment(Strict):
    usefulness: AICriterion
    context_fit: AICriterion
    correctness: AICriterion


class EvaluationJobsMixin:
    def evaluation_preview(self, raw):
        reject_ai_evaluation()

    def evaluation_task(self, raw):
        reject_ai_evaluation()

    def _assess(self, job, output, model, settings, calibration=False):
        reject_ai_evaluation()

    def _evaluation(self, job):
        reject_ai_evaluation()

    def calibrate(self, raw):
        reject_ai_evaluation()
