from ortools.sat.python import cp_model

model = cp_model.CpModel()

Voxel = tuple[int, int, int]
Dimensions = tuple[int, int, int]

def add(voxel, offset):
    return (voxel[0] + offset[0], voxel[1] + offset[1], voxel[2] + offset[2])

truck: Dimensions = (4, 5, 5)

# Space of voxel to model our problem with
space: list[Voxel] = {(x, y, z) for x in range(0, truck[0]) for y in range(0, truck[1]) for z in range(0, truck[2])}

box_sizes: list[Dimensions] = [
    (2, 1, 3),
    (4, 2, 1),
    (1, 4, 4),
    (3, 2, 2),
]

BoxId = int
Stop = int
route_order: dict[BoxId, Stop] = {
    0: 0,
    1: 0,
    2: 1,
    3: 2,
}

boxes: list[set[Voxel]] = [
    {(x, y, z) for x in range(0, size[0]) for y in range(0, size[1]) for z in range(0, size[2])}
    for size in box_sizes
]

print("Boxes:")
for box in boxes:
    print(box)

# Voxels of a box #idx for given offset
offset_boxes: dict[tuple[int, Voxel], set[Voxel]] = {}
# Variable to describe whether Box #idx has a specific offset
box_offset_var: dict[tuple[int, Voxel], "IntVar"] = {}
for idx, box in enumerate(boxes):
    for offset in space:
        offset_box = {add(voxel, offset) for voxel in box}
        # Make sure the box is contained in the space
        if all(voxel in space for voxel in offset_box):
            offset_boxes[(idx, offset)] = offset_box
            box_offset_var[(idx, offset)] = model.NewBoolVar(f"box_{idx}_offset_{offset}")

# Constraint: Each box must have exactly one offset
for box_idx in range(len(boxes)):
    model.Add(
        sum(var for ((idx, offset), var) in box_offset_var.items() if idx == box_idx) == 1
    )

voxel_var: dict[Voxel, "IntVar"] = {
    voxel: sum(var for ((idx, offset), var) in box_offset_var.items() if voxel in offset_boxes[(idx, offset)])
    for voxel in space
}
for voxel in space:
    # Constraint: Each voxel must only be occupied at most one box
    model.Add(voxel_var[voxel] <= 1)

    # Constraint: The voxels below a box must all be occupied
    below = add(voxel, (0, -1, 0))
    if below in space:
        model.Add(voxel_var[voxel] <= voxel_var[below])

# Track z-position of the boxes
box_front_z_var: list["IntVar"] = [
    model.NewIntVar(0, truck[1] - box_sizes[box_idx][1], f"box_front_z_{box_idx}")
    for box_idx in range(len(box_sizes))
]
for box_idx in range(len(box_sizes)):
    model.Add(box_front_z_var[box_idx] == sum(
        (truck[2] - box_sizes[box_idx][2] - z) * var
        for ((idx, (x, y, z)), var) in box_offset_var.items()
        if idx == box_idx
    ))

# Optimize order to be suitable for route
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


def paint(box_idx: int | None) -> str:
    if box_idx is None:
        return "×"
    return str(box_idx)


for y in range(0, truck[1]):
    for z in range(0, truck[2]):
        print(" ".join(paint(box_at_voxel.get((x, y, z))) for x in range(0, truck[0])))
    print()
