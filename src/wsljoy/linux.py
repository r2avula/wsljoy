from __future__ import annotations

import fcntl
import os
import socket
import struct
import time
from contextlib import suppress

from .protocol import ControllerState


UINPUT_PATH = "/dev/uinput"

EV_SYN = 0x00
EV_KEY = 0x01
EV_ABS = 0x03
SYN_REPORT = 0x00

BUS_USB = 0x03
BUS_BLUETOOTH = 0x05

ABS_X = 0x00
ABS_Y = 0x01
ABS_Z = 0x02
ABS_RX = 0x03
ABS_RY = 0x04
ABS_RZ = 0x05
ABS_HAT0X = 0x10
ABS_HAT0Y = 0x11
ABS_CNT = 0x40

BTN_SOUTH = 0x130
BTN_EAST = 0x131
BTN_NORTH = 0x133
BTN_WEST = 0x134
BTN_TL = 0x136
BTN_TR = 0x137
BTN_TL2 = 0x138
BTN_TR2 = 0x139
BTN_SELECT = 0x13A
BTN_START = 0x13B
BTN_MODE = 0x13C
BTN_THUMBL = 0x13D
BTN_THUMBR = 0x13E
BTN_TRIGGER_HAPPY1 = 0x2C0

UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_SET_ABSBIT = 0x40045567

INPUT_EVENT = "llHHi"
UINPUT_USER_DEV = "80sHHHHI" + ("i" * ABS_CNT * 4)


class VirtualGamepad:
    def __init__(self, initial: ControllerState, devnode: str = UINPUT_PATH):
        try:
            self.fd = os.open(devnode, os.O_WRONLY | os.O_NONBLOCK)
        except PermissionError as exc:
            raise SystemExit(
                f"Permission denied opening {devnode}. Run `python -m wsljoy setup-uinput`, "
                "then start a new WSL shell or run `newgrp input` before starting the guest."
            ) from exc
        self.axis_codes = {
            "lx": ABS_X,
            "ly": ABS_Y,
            "rx": ABS_RX,
            "ry": ABS_RY,
            "l2": ABS_Z,
            "r2": ABS_RZ,
            "hat_x": ABS_HAT0X,
            "hat_y": ABS_HAT0Y,
        }
        self.button_codes = {
            "square": BTN_WEST,
            "cross": BTN_SOUTH,
            "circle": BTN_EAST,
            "triangle": BTN_NORTH,
            "l1": BTN_TL,
            "r1": BTN_TR,
            "l2": BTN_TL2,
            "r2": BTN_TR2,
            "share": BTN_SELECT,
            "options": BTN_START,
            "l3": BTN_THUMBL,
            "r3": BTN_THUMBR,
            "ps": BTN_MODE,
            "touchpad": BTN_TRIGGER_HAPPY1,
        }
        self._last_axes: dict[str, int] = {}
        self._last_buttons: dict[str, int] = {}
        self._setup_device(initial)
        print(
            f"Created virtual gamepad: {initial.name} "
            f"vid={initial.vendor_id:04x} pid={initial.product_id:04x} "
            f"connection={initial.connection}",
            flush=True,
        )
        self.apply(initial)

    def _setup_device(self, initial: ControllerState) -> None:
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_KEY)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_ABS)
        for code in self.button_codes.values():
            fcntl.ioctl(self.fd, UI_SET_KEYBIT, code)
        for code in self.axis_codes.values():
            fcntl.ioctl(self.fd, UI_SET_ABSBIT, code)

        absmin = [0] * ABS_CNT
        absmax = [0] * ABS_CNT
        absfuzz = [0] * ABS_CNT
        absflat = [0] * ABS_CNT
        for code in (ABS_X, ABS_Y, ABS_RX, ABS_RY):
            absmin[code] = -32767
            absmax[code] = 32767
            absfuzz[code] = 16
            absflat[code] = 128
        for code in (ABS_Z, ABS_RZ):
            absmin[code] = 0
            absmax[code] = 65025
        for code in (ABS_HAT0X, ABS_HAT0Y):
            absmin[code] = -1
            absmax[code] = 1

        bus_type = {
            "usb": BUS_USB,
            "bluetooth": BUS_BLUETOOTH,
        }.get(initial.connection, BUS_USB)
        name = initial.name.encode("utf-8", errors="replace")[:79]
        payload = struct.pack(
            UINPUT_USER_DEV,
            name,
            bus_type,
            initial.vendor_id,
            initial.product_id,
            0x0111,
            0,
            *absmax,
            *absmin,
            *absfuzz,
            *absflat,
        )
        os.write(self.fd, payload)
        fcntl.ioctl(self.fd, UI_DEV_CREATE)
        time.sleep(0.1)

    def _write(self, event_type: int, code: int, value: int) -> None:
        now = time.time()
        seconds = int(now)
        micros = int((now - seconds) * 1_000_000)
        os.write(self.fd, struct.pack(INPUT_EVENT, seconds, micros, event_type, code, value))

    def apply(self, state: ControllerState) -> None:
        changed = False
        for name, code in self.axis_codes.items():
            value = state.axes[name]
            if self._last_axes.get(name) == value:
                continue
            self._write(EV_ABS, code, value)
            self._last_axes[name] = value
            changed = True
        for name, code in self.button_codes.items():
            value = state.buttons[name]
            if self._last_buttons.get(name) == value:
                continue
            self._write(EV_KEY, code, value)
            self._last_buttons[name] = value
            changed = True
        if changed:
            self._write(EV_SYN, SYN_REPORT, 0)

    def close(self) -> None:
        with suppress(Exception):
            fcntl.ioctl(self.fd, UI_DEV_DESTROY)
        with suppress(Exception):
            os.close(self.fd)


def run_guest(
    listen: str = "0.0.0.0",
    port: int = 27414,
    stale_after: float = 1.0,
) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((listen, port))
    sock.settimeout(0.1)
    print(f"Listening for controller state on {listen}:{port}", flush=True)

    virtual: VirtualGamepad | None = None
    last_seen = time.monotonic()
    neutral = ControllerState.neutral()

    try:
        while True:
            try:
                payload, _addr = sock.recvfrom(8192)
            except socket.timeout:
                if virtual and time.monotonic() - last_seen > stale_after:
                    neutral.seq += 1
                    neutral.timestamp = time.time()
                    virtual.apply(neutral)
                continue

            state = ControllerState.from_bytes(payload)
            if virtual is None:
                print("Received first controller packet", flush=True)
                virtual = VirtualGamepad(state)
            virtual.apply(state)
            last_seen = time.monotonic()
    finally:
        if virtual:
            virtual.close()
