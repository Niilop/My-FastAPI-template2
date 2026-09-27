from backend.models.schemas import ExampleRequest


def run_example_logic(data: ExampleRequest) -> str:
    return f"Hello {data.name}, your task '{data.task}' was processed successfully!"
