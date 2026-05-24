from wsljoy.ds4 import parse_report


def test_parse_usb_report_buttons_and_axes():
    report = bytes(
        [
            0x01,
            128,
            0,
            255,
            128,
            0x20 | 2,
            0x01 | 0x20,
            0x01,
            10,
            20,
        ]
    )

    state = parse_report(
        report,
        vendor_id=0x054C,
        product_id=0x05C4,
        name="Wireless Controller",
        seq=7,
        connection="usb",
    )

    assert state is not None
    assert state.axes["lx"] == 0
    assert state.axes["ly"] == -32767
    assert state.axes["rx"] == 32639
    assert state.axes["hat_x"] == 1
    assert state.axes["hat_y"] == 0
    assert state.axes["l2"] == 2550
    assert state.axes["r2"] == 5100
    assert state.buttons["cross"] == 1
    assert state.buttons["l1"] == 1
    assert state.buttons["options"] == 1
    assert state.buttons["ps"] == 1
    assert state.connection == "usb"


def test_parse_bluetooth_report_offset():
    report = bytes(
        [
            0x11,
            0xC0,
            0x00,
            128,
            128,
            128,
            128,
            8,
            0,
            0,
            0,
            255,
        ]
    )

    state = parse_report(
        report,
        vendor_id=0x054C,
        product_id=0x09CC,
        name="Wireless Controller",
        seq=1,
        connection="bluetooth",
    )

    assert state is not None
    assert state.axes["hat_x"] == 0
    assert state.axes["hat_y"] == 0
    assert state.axes["r2"] == 65025
    assert state.connection == "bluetooth"
