from piglets.types import Question, WorkflowContext

from .protocol import WorkflowStage


class WorkflowRunner:
    """Run workflow stages in order."""

    def __init__(self, stages: list[WorkflowStage]):
        self.stages = stages

    def run(self, question: Question) -> WorkflowContext:
        context = WorkflowContext(question=question)
        for stage in self.stages:
            context = stage.run(context)
        return context
