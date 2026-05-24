from piglets.types import Question, WorkflowState

from .protocol import WorkflowStage


class WorkflowRunner:
    """Run workflow stages in order."""

    def __init__(self, stages: list[WorkflowStage]):
        self.stages = stages

    def run(
        self,
        state: WorkflowState | None = None,
        *,
        question: Question | str | None = None,
    ) -> WorkflowState:
        if state is None:
            state = WorkflowState()
        if question is not None:
            question = _coerce_question(question)
            if state.question is not None and state.question != question:
                raise ValueError(
                    "WorkflowState question differs from the provided question"
                )
            if state.question is None:
                state = state.model_copy(update={"question": question})
        for stage in self.stages:
            state = stage.run(state)
        return state


def _coerce_question(question: Question | str) -> Question:
    if isinstance(question, Question):
        return question
    return Question(natural_language_question=question)
