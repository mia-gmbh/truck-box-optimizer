from pydantic import BaseModel
from typing import NamedTuple


# Dto Classes

Coords = tuple[int, int, int]

class BoxDto(BaseModel):
    box_id: str
    size: Coords
    route_order: int

class ProblemDto(BaseModel):
    truck: Coords
    boxes: list[BoxDto]

class PositionedBoxDto(BaseModel):
    box_id: str
    size: Coords
    offset: Coords

class PackingDto(BaseModel):
    boxes: list[PositionedBoxDto]


# Domain model

class Voxel(NamedTuple):
    x: int
    y: int
    z: int

    def __add__(self, other):
        return (type(self))(self.x + other.x, self.y + other.y, self.z + other.z)

    def __repr__(self) -> str:
        return f"<{self.x}, {self.y}, {self.z}>"


class Dimensions(NamedTuple):
    width: int
    height: int
    length: int

    @property
    def voxels(self) -> set[Voxel]:
        return {
            Voxel(x, y, z)
            for x in range(0, self.width)
            for y in range(0, self.height)
            for z in range(0, self.length)
        }

    def __repr__(self) -> str:
        return f"{self.width}×{self.height}×{self.length}"

BoxId = str
Stop = int

class Box(NamedTuple):
    box_id: BoxId
    size: Dimensions
    route_order: Stop

class Packing(NamedTuple):
    box_offsets: dict[BoxId, Voxel]
    box_at_voxel: dict[Voxel, BoxId]

class InfeasibleError(Exception):
    pass
