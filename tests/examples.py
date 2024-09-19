from importlib.resources import files
from typing import Generator
from truck.model import ProblemDto, PackingDto
from . import resources

def load_example(name: str) -> tuple[ProblemDto, PackingDto | None]:
    input_data = (files(resources) / f"{name}.json").read_text()
    try:
        result_data = (files(resources) / f"{name}.packing.json").read_text()
    except OSError:
        result_data = None
    return (ProblemDto.model_validate_json(input_data), None if result_data is None else PackingDto.model_validate_json(result_data))

def iter_examples() -> Generator[tuple[str, ProblemDto, PackingDto | None], None, None]:
    for file in files(resources).iterdir():
        filename = str(file)
        if not filename.endswith(".json") or filename.endswith(".packing.json"):
            continue
        example_name = file.name[:-5]

        yield (example_name, *load_example(example_name))


