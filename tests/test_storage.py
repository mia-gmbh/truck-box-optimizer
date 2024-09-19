from truck.service import get_route, set_box_size

def test_update_box_size():
    assert get_route("example1").boxes[0].size == (2, 1, 3)
    set_box_size("1", (1, 2, 1))
    assert get_route("example1").boxes[0].size == (1, 2, 1)
