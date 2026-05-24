from __future__ import annotations

import os
import time
from collections.abc import Iterator

from wsljoy.protocol import ControllerState, apply_deadzone


def _pygame():
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: install the Windows extra with "
            "`uv sync --extra windows` or `python -m pip install -e \".[windows]\"`."
        ) from exc
    return pygame


def _axis_to_i16(value: float) -> int:
    return apply_deadzone(max(-32767, min(32767, int(float(value) * 32767))))


def _trigger_to_u16(value: float) -> int:
    normalized = (float(value) + 1.0) / 2.0
    return max(0, min(65025, int(normalized * 65025)))


def _button(joystick, index: int) -> int:
    if index >= joystick.get_numbuttons():
        return 0
    return int(bool(joystick.get_button(index)))


def _axis(joystick, index: int) -> float:
    if index >= joystick.get_numaxes():
        return 0.0
    return float(joystick.get_axis(index))


def _hat(joystick) -> tuple[int, int]:
    if joystick.get_numhats() < 1:
        return 0, 0
    x, y = joystick.get_hat(0)
    return int(x), int(-y)


def _guid_ids(guid: str) -> tuple[int, int]:
    if len(guid) < 20:
        return 0, 0
    try:
        vendor_id = int.from_bytes(bytes.fromhex(guid[8:12]), "little")
        product_id = int.from_bytes(bytes.fromhex(guid[16:20]), "little")
    except ValueError:
        return 0, 0
    return vendor_id, product_id


def list_controllers() -> list[dict]:
    pygame = _pygame()
    pygame.init()
    pygame.joystick.init()
    devices = []
    for index in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(index)
        joystick.init()
        guid = joystick.get_guid()
        vendor_id, product_id = _guid_ids(guid)
        devices.append(
            {
                "backend": "sdl",
                "index": index,
                "vendor_id": vendor_id,
                "product_id": product_id,
                "product_string": joystick.get_name(),
                "path": f"sdl:{index}",
                "guid": guid,
                "connection": "unknown",
            }
        )
    return devices


def iter_states(index: int = 0, poll_interval: float = 0.004) -> Iterator[ControllerState]:
    pygame = _pygame()
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() <= index:
        raise SystemExit("No SDL-supported game controller found on Windows.")

    joystick = pygame.joystick.Joystick(index)
    joystick.init()
    vendor_id, product_id = _guid_ids(joystick.get_guid())
    name = joystick.get_name() or "SDL Game Controller"
    seq = 0

    while True:
        pygame.event.pump()
        hat_x, hat_y = _hat(joystick)
        yield ControllerState(
            vendor_id=vendor_id,
            product_id=product_id,
            name=name,
            axes={
                "lx": _axis_to_i16(_axis(joystick, 0)),
                "ly": _axis_to_i16(_axis(joystick, 1)),
                "rx": _axis_to_i16(_axis(joystick, 2)),
                "ry": _axis_to_i16(_axis(joystick, 3)),
                "l2": _trigger_to_u16(_axis(joystick, 4)),
                "r2": _trigger_to_u16(_axis(joystick, 5)),
                "hat_x": hat_x,
                "hat_y": hat_y,
            },
            buttons={
                "cross": _button(joystick, 0),
                "circle": _button(joystick, 1),
                "square": _button(joystick, 2),
                "triangle": _button(joystick, 3),
                "share": _button(joystick, 4),
                "ps": _button(joystick, 5),
                "options": _button(joystick, 6),
                "l3": _button(joystick, 7),
                "r3": _button(joystick, 8),
                "l1": _button(joystick, 9),
                "r1": _button(joystick, 10),
                "l2": int(_axis(joystick, 4) > 0.25),
                "r2": int(_axis(joystick, 5) > 0.25),
                "touchpad": _button(joystick, 15),
            },
            seq=seq,
            timestamp=time.time(),
            connection="unknown",
        )
        seq += 1
        time.sleep(poll_interval)
