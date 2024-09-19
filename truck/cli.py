from .model import Dimensions, Box, Voxel, BoxId, InfeasibleError
from .solver import pack_truck

truck = Dimensions(width=4, height=5, length=5)

boxes: list[Box] = [
    Box(box_id="1", size=Dimensions(2, 1, 3), route_order=0),
    Box(box_id="2", size=Dimensions(4, 2, 1), route_order=0),
    Box(box_id="3", size=Dimensions(1, 4, 4), route_order=1),
    Box(box_id="4", size=Dimensions(3, 2, 2), route_order=2),
]

print("Boxes:")
for box in boxes:
    print(box)

try:
    box_offsets, box_at_voxel = pack_truck(truck, boxes)
except InfeasibleError:
    print("Unable to find a solution")
    exit()

def paint(box_id: BoxId | None) -> str:
    if box_id is None:
        return "×"
    return str(box_id)

print()
print("\033[32;1;7mSolution\033[0m")
for (box_id, offset) in box_offsets.items():
    print(f"Box {box_id} is at {offset}")


for y in range(0, truck.height):
    for z in range(0, truck.length):
        print(" ".join(paint(box_at_voxel.get(Voxel(x, y, z))) for x in range(0, truck.width)))
    print()

