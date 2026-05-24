from __future__ import annotations

import time
from collections.abc import Sequence

from .protocol import ControllerState, apply_deadzone


SONY_VENDOR_ID = 0x054C
DS4_PRODUCT_IDS = (0x05C4, 0x09CC)

DPAD_TO_HAT = {
    0: (0, -1),
    1: (1, -1),
    2: (1, 0),
    3: (1, 1),
    4: (0, 1),
    5: (-1, 1),
    6: (-1, 0),
    7: (-1, -1),
    8: (0, 0),
}


def uint8_axis(value: int) -> int:
    return max(-32767, min(32767, (int(value) - 128) * 257))


def trigger_axis(value: int) -> int:
    return max(0, min(255, int(value))) * 255


def parse_report(
    report: bytes | bytearray | Sequence[int],
    *,
    vendor_id: int,
    product_id: int,
    name: str,
    seq: int,
    connection: str = "unknown",
) -> ControllerState | None:
    data = bytes(report)
    if not data:
        return None

    report_id = data[0]
    if report_id == 0x01 and len(data) >= 10:
        offset = 1
    elif report_id == 0x11 and len(data) >= 12:
        offset = 3
    else:
        return None

    lx, ly, rx, ry = data[offset : offset + 4]
    buttons_1 = data[offset + 4]
    buttons_2 = data[offset + 5]
    buttons_3 = data[offset + 6]
    l2_value = data[offset + 7]
    r2_value = data[offset + 8]

    dpad = buttons_1 & 0x0F
    hat_x, hat_y = DPAD_TO_HAT.get(dpad, (0, 0))

    return ControllerState(
        vendor_id=vendor_id,
        product_id=product_id,
        name=name or "Sony Computer Entertainment Wireless Controller",
        axes={
            "lx": apply_deadzone(uint8_axis(lx)),
            "ly": apply_deadzone(uint8_axis(ly)),
            "rx": apply_deadzone(uint8_axis(rx)),
            "ry": apply_deadzone(uint8_axis(ry)),
            "l2": trigger_axis(l2_value),
            "r2": trigger_axis(r2_value),
            "hat_x": hat_x,
            "hat_y": hat_y,
        },
        buttons={
            "square": int(bool(buttons_1 & 0x10)),
            "cross": int(bool(buttons_1 & 0x20)),
            "circle": int(bool(buttons_1 & 0x40)),
            "triangle": int(bool(buttons_1 & 0x80)),
            "l1": int(bool(buttons_2 & 0x01)),
            "r1": int(bool(buttons_2 & 0x02)),
            "l2": int(bool(buttons_2 & 0x04)),
            "r2": int(bool(buttons_2 & 0x08)),
            "share": int(bool(buttons_2 & 0x10)),
            "options": int(bool(buttons_2 & 0x20)),
            "l3": int(bool(buttons_2 & 0x40)),
            "r3": int(bool(buttons_2 & 0x80)),
            "ps": int(bool(buttons_3 & 0x01)),
            "touchpad": int(bool(buttons_3 & 0x02)),
        },
        seq=seq,
        timestamp=time.time(),
        connection=connection,
    )
