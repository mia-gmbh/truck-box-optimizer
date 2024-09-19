from importlib.resources import files
import pytest
from truck.model import ProblemDto, PackingDto
from truck.service import pack_truck
from . import resources

def load_example(name: str) -> tuple[ProblemDto, PackingDto | None]:
    input_data = (files(resources) / f"{name}.json").read_text()
    try:
        result_data = (files(resources) / f"{name}.packing.json").read_text()
    except OSError:
        result_data = None
    return (ProblemDto.model_validate_json(input_data), None if result_data is None else PackingDto.model_validate_json(result_data))


@pytest.mark.asyncio()
async def test_satisfiable_example(subtests):
    problem, expected_packing = load_example("example1")
    packing = await pack_truck(problem)
    assert packing == expected_packing
