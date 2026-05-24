from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any, ClassVar


PROTOCOL_VERSION = 1

STICK_DEADZONE = 1024


def apply_deadzone(value: int, deadzone: int = STICK_DEADZONE) -> int:
    value = int(value)
    if abs(value) <= deadzone:
        return 0
    return value


@dataclass(slots=True)
class ControllerState:
    vendor_id: int
    product_id: int
    name: str
    axes: dict[str, int]
    buttons: dict[str, int]
    seq: int
    timestamp: float
    connection: str = "unknown"
    protocol: int = PROTOCOL_VERSION

    REQUIRED_AXES: ClassVar[tuple[str, ...]] = (
        "lx",
        "ly",
        "rx",
        "ry",
        "l2",
        "r2",
        "hat_x",
        "hat_y",
    )
    REQUIRED_BUTTONS: ClassVar[tuple[str, ...]] = (
        "square",
        "cross",
        "circle",
        "triangle",
        "l1",
        "r1",
        "l2",
        "r2",
        "share",
        "options",
        "l3",
        "r3",
        "ps",
        "touchpad",
    )

    @classmethod
    def neutral(
        cls,
        vendor_id: int = 0x054C,
        product_id: int = 0x05C4,
        name: str = "Sony Computer Entertainment Wireless Controller",
    ) -> "ControllerState":
        return cls(
            vendor_id=vendor_id,
            product_id=product_id,
            name=name,
            axes={
                "lx": 0,
                "ly": 0,
                "rx": 0,
                "ry": 0,
                "l2": 0,
                "r2": 0,
                "hat_x": 0,
                "hat_y": 0,
            },
            buttons={button: 0 for button in cls.REQUIRED_BUTTONS},
            seq=0,
            timestamp=time.time(),
            connection="unknown",
        )

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self), separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_bytes(cls, payload: bytes) -> "ControllerState":
        data: dict[str, Any] = json.loads(payload.decode("utf-8"))
        if data.get("protocol") != PROTOCOL_VERSION:
            raise ValueError(f"unsupported protocol version: {data.get('protocol')}")
        axes = {axis: int(data["axes"].get(axis, 0)) for axis in cls.REQUIRED_AXES}
        buttons = {
            button: int(bool(data["buttons"].get(button, 0)))
            for button in cls.REQUIRED_BUTTONS
        }
        return cls(
            vendor_id=int(data["vendor_id"]),
            product_id=int(data["product_id"]),
            name=str(data["name"]),
            axes=axes,
            buttons=buttons,
            seq=int(data["seq"]),
            timestamp=float(data["timestamp"]),
            connection=str(data.get("connection") or "unknown"),
        )
