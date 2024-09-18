from typing import NamedTuple
from ortools.sat.python import cp_model

model = cp_model.CpModel()

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

truck = Dimensions(4, 5, 5)

# Space of voxel to model our problem with
space: set[Voxel] = truck.voxels

box_sizes: list[Dimensions] = [
    Dimensions(2, 1, 3),
    Dimensions(4, 2, 1),
    Dimensions(1, 4, 4),
    Dimensions(3, 2, 2),
]

BoxIdx = int
Stop = int
route_order: dict[BoxIdx, Stop] = {
    0: 0,
    1: 0,
    2: 1,
    3: 2,
}

boxes: list[set[Voxel]] = [size.voxels for size in box_sizes]

print("Boxes:")
for box in boxes:
    print(box)

# Voxels of a box #idx for given offset
offset_boxes: dict[tuple[BoxIdx, Voxel], set[Voxel]] = {}
# Variable to describe whether Box #idx has a specific offset
box_offset_var: dict[tuple[BoxIdx, Voxel], cp_model.IntVar] = {}
for idx, box in enumerate(boxes):
    for offset in space:
        offset_box = {voxel + offset for voxel in box}
        # Make sure the box is contained in the space
        if all(voxel in space for voxel in offset_box):
            offset_boxes[(idx, offset)] = offset_box
            box_offset_var[(idx, offset)] = model.NewBoolVar(f"box_{idx}_offset_{offset}")

# Constraint: Each box must have exactly one offset
for box_idx in range(len(boxes)):
    model.Add(
        sum(var for ((idx, offset), var) in box_offset_var.items() if idx == box_idx) == 1
    )

voxel_var: dict[Voxel, cp_model.IntVar] = {
    voxel: sum(var for ((idx, offset), var) in box_offset_var.items() if voxel in offset_boxes[(idx, offset)])
    for voxel in space
}
for voxel in space:
    # Constraint: Each voxel must only be occupied at most one box
    model.Add(voxel_var[voxel] <= 1)

    # Constraint: The voxels below a box must all be occupied
    below = voxel + Voxel(0, -1, 0)
    if below in space:
        model.Add(voxel_var[voxel] <= voxel_var[below])

# Track z distance from the truck opening to the box
# This variable is not strictly necessary, but helps in making the model cleaner
box_front_z_var: list[cp_model.IntVar] = [
    model.NewIntVar(0, truck.height - box_sizes[box_idx].height, f"box_front_z_{box_idx}")
    for box_idx in range(len(box_sizes))
]
for box_idx in range(len(box_sizes)):
    model.Add(box_front_z_var[box_idx] == sum(
        (truck.length - box_sizes[box_idx].length - z) * var
        for ((idx, (x, y, z)), var) in box_offset_var.items()
        if idx == box_idx
    ))

# Optimize order to be suitable for route
# The box with the latest stop should be the furthest back in the truck → their z-distance can be greatest
stop_count = max(route_order.values()) + 1
model.Minimize(
    sum(
        (1 - 2 * route_order[box_idx] / (stop_count - 1)) * box_front_z_var[box_idx]
        for box_idx in range(len(box_sizes))
    )
)

solver = cp_model.CpSolver()
status = solver.solve(model)

if status == cp_model.INFEASIBLE:
    print("Unable to find a solution")
    exit()

box_at_voxel = {}

print("Solution")
for ((idx, offset), var) in box_offset_var.items():
    if solver.Value(var):
        print(f"Box {idx} is at {offset} -> {solver.Value(box_front_z_var[idx])}")
        for voxel in offset_boxes[(idx, offset)]:
            box_at_voxel[voxel] = idx

print(box_at_voxel)


def paint(box_idx: BoxIdx | None) -> str:
    if box_idx is None:
        return "×"
    return str(box_idx)


for y in range(0, truck[1]):
    for z in range(0, truck[2]):
        print(" ".join(paint(box_at_voxel.get(Voxel(x, y, z))) for x in range(0, truck[0])))
    print()
