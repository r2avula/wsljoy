from wsljoy.controllers.common import hid_connection


def test_hid_connection_from_bus_type():
    assert hid_connection({"bus_type": 1}) == "usb"
    assert hid_connection({"bus_type": 2}) == "bluetooth"


def test_hid_connection_from_path():
    assert hid_connection({"path": rb"\\?\hid#vid_054c&pid_05c4"}) == "usb"
    assert hid_connection({"path": rb"\\?\bthledevice#{00001812}"}) == "bluetooth"
