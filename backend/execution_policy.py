"""Current workflow: collect questions, then evaluate with fixed scripts."""


def validate_experiment(config):
    if config.get("ai_control"):
        raise ValueError("AI evaluation is disabled. Collect questions with ai_control=false, then run fixed metrics.")


def reject_ai_evaluation():
    raise ValueError("AI evaluation is disabled. Run fixed metric scripts after collecting all questions.")
