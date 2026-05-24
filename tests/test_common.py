from wsljoy.controllers.common import is_known_gamepad


def test_known_gamepad_by_vendor():
    assert is_known_gamepad({"vendor_id": 0x045E})


def test_known_gamepad_by_hid_usage():
    assert is_known_gamepad({"usage_page": 0x01, "usage": 0x05})


def test_known_gamepad_by_name():
    assert is_known_gamepad({"product_string": "Ultimate 8BitDo Controller"})
