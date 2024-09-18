"""Define the main controller as FastAPI app."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .model import Box, Dimensions, InfeasibleError
from .solver import pack_truck as pack_truck_solver

app = FastAPI()

Coords = tuple[int, int, int]

class BoxData(BaseModel):
    box_id: str
    size: Coords
    route_order: int

class PositionedBox(BaseModel):
    box_id: str
    size: Coords
    offset: Coords

@app.post("/truck:pack")
async def pack_truck(truck: Coords, boxes: list[BoxData]) -> list[PositionedBox]:
    truck_model = Dimensions(*truck)
    boxes_model = [Box(
        box_id=box.box_id,
        size=Dimensions(*box.size),
        route_order=box.route_order,
    ) for box in boxes]

    try:
        box_at_voxel, box_offsets = pack_truck_solver(truck_model, boxes_model)
    except InfeasibleError:
        raise HTTPException(500)
    except ValueError:
        raise HTTPException(400)

    return [
        PositionedBox(
            box_id=box.box_id,
            size=box.size,
            offset=box_offsets[box.box_id],
        )
        for box in boxes_model
    ]
