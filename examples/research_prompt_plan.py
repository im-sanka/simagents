"""Flagship example: research -> prompt plan -> final prompt execution."""

from simagents import AgentSpec, EasyOrchestrator, RunConfig, TaskSpec, WorkflowSpec
from simagents.core.models import WorkflowMode


def build_example() -> EasyOrchestrator:
    agents = [
        AgentSpec(
            name="researcher",
            role="Technical researcher",
            instructions="Gather accurate facts and trends with concise bullets.",
            model="gpt-4o-mini",
            temperature=0.2,
        ),
        AgentSpec(
            name="planner",
            role="Prompt planner",
            instructions=(
                "Create a high-quality prompt blueprint with goals, constraints, sections, "
                "tone, and evaluation criteria."
            ),
            model="gpt-4o-mini",
            temperature=0.3,
        ),
        AgentSpec(
            name="writer",
            role="Execution writer",
            instructions="Use the prompt plan strictly to produce final markdown output.",
            model="gpt-4o-mini",
            temperature=0.6,
        ),
    ]

    tasks = [
        TaskSpec(
            name="research",
            agent_name="researcher",
            prompt_template=(
                "Research this topic and provide key trends, tools, risks, and references:\n\n{input}"
            ),
        ),
        TaskSpec(
            name="prompt_plan",
            agent_name="planner",
            prompt_template=(
                "Using this research, create a prompt plan with sections:\n"
                "- Objective\n- Audience\n- Constraints\n- Tone\n- Required structure\n"
                "- Quality checklist\n\nResearch:\n{research}"
            ),
        ),
        TaskSpec(
            name="final_output",
            agent_name="writer",
            prompt_template=(
                "Use this prompt plan to produce final markdown output.\n\n"
                "Prompt Plan:\n{prompt_plan}\n\nOriginal topic:\n{input}"
            ),
        ),
    ]

    workflow = WorkflowSpec(mode=WorkflowMode.LINEAR)
    run_config = RunConfig(output_dir="runs", save_artifacts=True, debug=False)

    return EasyOrchestrator(agents=agents, tasks=tasks, workflow=workflow, run_config=run_config)


if __name__ == "__main__":
    orchestrator = build_example()
    result = orchestrator.run(input_text="How AI is changing bioinformatics workflows")
    print("\n=== FINAL OUTPUT ===\n")
    print(result.final_output)
    print("\nArtifacts:", result.artifacts_dir)
