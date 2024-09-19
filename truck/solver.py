from ortools.sat.python import cp_model

from .model import Voxel, Dimensions, BoxId, Box, Packing, InfeasibleError

def pack_truck(truck: Dimensions, boxes: list[Box], time_limit: int = 60) -> tuple[dict[Voxel, BoxId], dict[BoxId, Voxel]]:
    """Find a packing of boxes in the truck."""

    model = cp_model.CpModel()

    # Space of voxel to model our problem with
    space: set[Voxel] = truck.voxels

    # Voxels of a box for given offset
    offset_boxes: dict[tuple[BoxId, Voxel], set[Voxel]] = {}
    # Variable to describe whether Box has a specific offset
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
        model.NewIntVar(0, truck.length, f"box_front_z_{box.box_id}")
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
    if stop_count > 1:
        model.Minimize(
            sum(
                (1 - 2 * box.route_order / (stop_count - 1)) * box_front_z_var[box.box_id]
                for box in boxes
            )
        )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.solve(model)

    if status == cp_model.INFEASIBLE:
        raise InfeasibleError
    elif status == cp_model.MODEL_INVALID:
        raise ValueError("Invalid inputs. Could not create a valid model.")

    box_at_voxel: dict[Voxel, BoxId] = {}
    box_offsets: dict[BoxId, Voxel] = {}

    for ((id, offset), var) in box_offset_var.items():
        if solver.Value(var):
            box_offsets[id] = offset
            for voxel in offset_boxes[(id, offset)]:
                box_at_voxel[voxel] = id

    return Packing(box_offsets, box_at_voxel)
