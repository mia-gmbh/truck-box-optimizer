from math import floor, ceil
from typing import Generator
from .model import Coords, Box, Dimensions, Voxel, BoxDto

def possible_grids(voxel_limit: int) -> Generator[Dimensions, None, None]:
    max_div = floor(voxel_limit ** (1/3)) * 3
    for divide_width in range(1, max_div + 1):
        for divide_height in range(1, floor(voxel_limit / divide_width) + 1):
            for divide_length in range(6, floor(voxel_limit / (divide_width * divide_height)) + 1):
                yield Dimensions(divide_width, divide_height, divide_length)

def rasterize(truck: Coords, boxes: list[BoxDto], voxel_limit: int = 2000) -> tuple[Dimensions, Coords, list[Box]]:
    """Find a way to divide the ruck into voxel units with a limit on the number of voxels."""
    best = None
    best_error = float('Infinity')
    for grid in possible_grids(voxel_limit):
        factors = (grid.width / truck[0], grid.height / truck[1], grid.length / truck[2])

        error = sum(
            ceil(box.size[0] * factors[0]) / factors[0] - box.size[0]
            + ceil(box.size[1] * factors[1]) / factors[1] - box.size[1]
            + ceil(box.size[2] * factors[2]) / factors[2] - box.size[2]
            for box in boxes
        )

        if error < best_error:
            best_error = error

            scaled_boxes = [Box(
                box_id=box.box_id,
                size=scale_box(box.size, factors),
                route_order=box.route_order,
            ) for box in boxes]

            best = (grid, factors, scaled_boxes)

        if error == 0:
            break

    if best is None:
        raise ValueError
    return best


def scale_box(size: Coords, factors: Coords) -> Dimensions:
    return Dimensions(
        ceil(size[0] * factors[0]),
        ceil(size[1] * factors[1]),
        ceil(size[2] * factors[2]),
    )

def scale_back_offset(offset: Voxel, factors: Coords) -> Coords:
    return (
        offset.x / factors[0],
        offset.y / factors[1],
        offset.z / factors[2],
    )

