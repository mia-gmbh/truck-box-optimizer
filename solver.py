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

BoxId = str
Stop = int

class Box(NamedTuple):
    box_id: BoxId
    size: Dimensions
    route_order: Stop

truck = Dimensions(width=4, height=5, length=5)

boxes: list[Box] = [
    Box(box_id="1", size=Dimensions(2, 1, 3), route_order=0),
    Box(box_id="2", size=Dimensions(4, 2, 1), route_order=0),
    Box(box_id="3", size=Dimensions(1, 4, 4), route_order=1),
    Box(box_id="4", size=Dimensions(3, 2, 2), route_order=2),
]

# Space of voxel to model our problem with
space: set[Voxel] = truck.voxels

print("Boxes:")
for box in boxes:
    print(box)

# Voxels of a box #idx for given offset
offset_boxes: dict[tuple[BoxId, Voxel], set[Voxel]] = {}
# Variable to describe whether Box #idx has a specific offset
box_offset_var: dict[tuple[BoxId, Voxel], cp_model.IntVar] = {}
for box in boxes:
    for offset in space:
        offset_box = {voxel + offset for voxel in box.size.voxels}
        # Make sure the box is contained in the space
        if all(voxel in space for voxel in offset_box):
            offset_boxes[(box.box_id, offset)] = offset_box
            box_offset_var[(box.box_id, offset)] = model.NewBoolVar(f"box_{box.box_id}_offset_{offset}")

# Constraint: Each box must have exactly one offset
for box in boxes:
    model.Add(
        sum(var for ((id, offset), var) in box_offset_var.items() if id == box.box_id) == 1
    )

voxel_var: dict[Voxel, cp_model.IntVar] = {
    voxel: sum(var for ((id, offset), var) in box_offset_var.items() if voxel in offset_boxes[(id, offset)])
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
box_front_z_var: dict[BoxId, cp_model.IntVar] = {
    box.box_id:
    model.NewIntVar(0, truck.height - box.size.height, f"box_front_z_{box.box_id}")
    for box in boxes
}
for box in boxes:
    model.Add(box_front_z_var[box.box_id] == sum(
        (truck.length - box.size.length - z) * var
        for ((id, (x, y, z)), var) in box_offset_var.items()
        if id == box.box_id
    ))

# Optimize order to be suitable for route
# The box with the latest stop should be the furthest back in the truck → their z-distance can be greatest
stop_count = max(box.route_order for box in boxes) + 1
model.Minimize(
    sum(
        (1 - 2 * box.route_order / (stop_count - 1)) * box_front_z_var[box.box_id]
        for box in boxes
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


def paint(box_idx: BoxId | None) -> str:
    if box_idx is None:
        return "×"
    return str(box_idx)


for y in range(0, truck.height):
    for z in range(0, truck.length):
        print(" ".join(paint(box_at_voxel.get(Voxel(x, y, z))) for x in range(0, truck.width)))
    print()
