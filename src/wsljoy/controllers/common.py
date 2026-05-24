from __future__ import annotations


KNOWN_GAMEPAD_VENDORS = {
    0x044F: "Thrustmaster",
    0x045E: "Microsoft",
    0x046D: "Logitech",
    0x054C: "Sony",
    0x057E: "Nintendo",
    0x0738: "Mad Catz",
    0x0E6F: "PDP",
    0x1532: "Razer",
    0x20D6: "PowerA",
    0x24C6: "PowerA",
    0x2DC8: "8BitDo",
}


def is_known_gamepad(device: dict) -> bool:
    vendor_id = int(device.get("vendor_id") or 0)
    usage_page = int(device.get("usage_page") or 0)
    usage = int(device.get("usage") or 0)
    product = str(device.get("product_string") or "").lower()
    manufacturer = str(device.get("manufacturer_string") or "").lower()

    if vendor_id in KNOWN_GAMEPAD_VENDORS:
        return True
    if usage_page == 0x01 and usage in {0x04, 0x05}:
        return True
    return any(
        token in f"{manufacturer} {product}"
        for token in (
            "xbox",
            "dualshock",
            "dualsense",
            "wireless controller",
            "8bitdo",
            "gamepad",
            "controller",
        )
    )


def decode_hid_path(path: object) -> str:
    if isinstance(path, bytes):
        return path.decode(errors="replace")
    return str(path or "")


def hid_connection(device: dict) -> str:
    bus_type = int(device.get("bus_type") or 0)
    if bus_type == 1:
        return "usb"
    if bus_type == 2:
        return "bluetooth"

    path = decode_hid_path(device.get("path")).lower()
    if "bth" in path or "bluetooth" in path:
        return "bluetooth"
    if "usb" in path or "vid_" in path:
        return "usb"
    return "unknown"
