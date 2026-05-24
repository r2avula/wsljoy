from __future__ import annotations

import time
from collections.abc import Iterator

from wsljoy.ds4 import DS4_PRODUCT_IDS, SONY_VENDOR_ID, parse_report
from wsljoy.controllers.common import hid_connection
from wsljoy.protocol import ControllerState


def supports(device: dict) -> bool:
    return (
        int(device.get("vendor_id") or 0) == SONY_VENDOR_ID
        and int(device.get("product_id") or 0) in DS4_PRODUCT_IDS
    )


def open_device(hid, metadata: dict):
    controller = hid.device()
    controller.open_path(metadata["path"])
    controller.set_nonblocking(True)
    return controller


def iter_states(hid, metadata: dict, poll_interval: float = 0.002) -> Iterator[ControllerState]:
    controller = open_device(hid, metadata)
    info = controller.get_manufacturer_string(), controller.get_product_string()
    name = (
        " ".join(part for part in info if part)
        or metadata.get("product_string")
        or "Sony Computer Entertainment Wireless Controller"
    )
    vendor_id = int(metadata.get("vendor_id") or SONY_VENDOR_ID)
    product_id = int(metadata.get("product_id") or 0x05C4)
    connection = hid_connection(metadata)
    seq = 0

    while True:
        report = controller.read(128)
        if not report:
            time.sleep(poll_interval)
            continue
        state = parse_report(
            report,
            vendor_id=vendor_id,
            product_id=product_id,
            name=name,
            seq=seq,
            connection=connection,
        )
        if state is None:
            continue
        seq += 1
        yield state
