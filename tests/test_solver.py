from importlib.resources import files
from fastapi import HTTPException
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
async def test_examples(subtests):
    for file in files(resources).iterdir():
        filename = str(file)
        if not filename.endswith(".json") or filename.endswith(".packing.json"):
            continue
        example_name = filename[:-5]

        with subtests.test(test_name=f"{file.name}"):
            problem, expected_packing = load_example(example_name)
            if expected_packing is None:
                with pytest.raises(HTTPException):
                    await pack_truck(problem)
            else:
                packing = await pack_truck(problem)
                assert packing == expected_packing
