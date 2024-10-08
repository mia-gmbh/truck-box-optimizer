"""Define the main controller as FastAPI app."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .model import BoxId, Coords, ProblemDto, ProblemDtoWithSize, PositionedBoxDto, PackingDto, InfeasibleError
from .rasterize import rasterize, scale_back_offset
from .solver import pack_truck as pack_truck_solver
from tests.examples import iter_examples

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

routes: dict[str, ProblemDto] = {
    name: problem
    for (name, problem, _) in iter_examples(include_partials=True)
}

@app.get("/routes")
def get_routes() -> dict[str, ProblemDto]:
    return routes

@app.get("/routes/{routeName}")
def get_route(routeName: str) -> ProblemDto:
    return routes[routeName]

@app.post("/boxes/{box_id}/size")
def set_box_size(box_id: BoxId, size: Coords) -> int:
    """Update the size of a box in all routes

    Returns the number of boxes updated.
    """
    count = 0

    # TODO: scale values in App
    size = (size[0] * 100, size[1] * 100, size[2] * 100)

    # TODO: Detect what is up, right and left in App
    sorted_size = sorted(size)
    size = (sorted_size[0], sorted_size[2], sorted_size[1])

    for route in routes.values():
        for box in route.boxes:
            if box.box_id == box_id:
                box.size = size
                count += 1

    if not count:
        raise HTTPException(400)
    return count

@app.post("/truck:pack")
async def pack_truck(problem: ProblemDtoWithSize) -> PackingDto:
    # Scale model so the amount of voxels is limited
    grid, factors, scaled_boxes = rasterize(problem.truck, problem.boxes)

    try:
        packing = pack_truck_solver(grid, scaled_boxes)
    except InfeasibleError:
        raise HTTPException(500, "Unable to find a packing")
    except ValueError:
        raise HTTPException(400, "Could not create an optimizer model")

    return PackingDto(
        truck=problem.truck,
        boxes=[
            PositionedBoxDto(
                box_id=box.box_id,
                size=box.size,
                offset=scale_back_offset(packing.box_offsets[box.box_id], factors),
                route_order=box.route_order,
            )
            for box in problem.boxes
        ],
        grid=grid,
    )
