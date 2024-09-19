from fastapi import HTTPException
import pytest
from truck.service import pack_truck
from .examples import iter_examples

@pytest.mark.asyncio()
async def test_examples(subtests):
    for example_name, problem, expected_packing in iter_examples():
        with subtests.test(example_name):
            if expected_packing is None:
                with pytest.raises(HTTPException):
                    await pack_truck(problem)
            else:
                packing = await pack_truck(problem)
                assert packing == expected_packing
