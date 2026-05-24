from __future__ import annotations

import ipaddress
import socket
import subprocess
import time
from collections.abc import Iterator

from .controllers import ds4_hid, sdl
from .controllers.common import decode_hid_path, is_known_gamepad
from .protocol import ControllerState


def _hid():
    try:
        import hid
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: install the Windows extra with "
            "`uv sync --extra windows` or `python -m pip install -e \".[windows]\"`."
        ) from exc
    return hid


def list_controllers() -> list[dict]:
    devices = []
    try:
        hid = _hid()
    except SystemExit:
        hid = None

    if hid is not None:
        for device in hid.enumerate():
            if not is_known_gamepad(device):
                continue
            backend = "ds4-hid" if ds4_hid.supports(device) else "sdl"
            devices.append({**device, "backend": backend})

    exact_hid_ids = {
        (int(device.get("vendor_id") or 0), int(device.get("product_id") or 0))
        for device in devices
        if device.get("backend") == "ds4-hid"
    }
    try:
        for device in sdl.list_controllers():
            device_id = (int(device.get("vendor_id") or 0), int(device.get("product_id") or 0))
            if device_id in exact_hid_ids:
                continue
            if not any(
                existing.get("backend") == "sdl"
                and existing.get("index") == device.get("index")
                for existing in devices
            ):
                devices.append(device)
    except SystemExit:
        pass

    return devices


def _select_device(path: str | None = None, backend: str = "auto") -> dict:
    devices = list_controllers()
    if path:
        for device in devices:
            if decode_hid_path(device.get("path")) == path:
                return device
            if str(device.get("path")) == path:
                return device
        if path.startswith("sdl:"):
            return {
                "backend": "sdl",
                "path": path,
                "index": int(path.split(":", 1)[1]),
                "product_string": "SDL Game Controller",
            }
        raise SystemExit(f"No controller matched path: {path}")

    if backend != "auto":
        devices = [device for device in devices if device.get("backend") == backend]

    if not devices:
        raise SystemExit("No supported game controller found on Windows.")

    devices.sort(key=lambda device: 0 if device.get("backend") == "ds4-hid" else 1)
    return devices[0]


def open_controller(path: str | None = None, backend: str = "auto"):
    hid = _hid()
    metadata = _select_device(path, backend)
    if metadata.get("backend") != "ds4-hid":
        raise SystemExit("open_controller only supports the ds4-hid backend.")
    return ds4_hid.open_device(hid, metadata), metadata


def iter_states(
    path: str | None = None,
    poll_interval: float = 0.002,
    backend: str = "auto",
) -> Iterator[ControllerState]:
    metadata = _select_device(path, backend)
    selected_backend = metadata.get("backend")
    if selected_backend == "ds4-hid":
        hid = _hid()
        yield from ds4_hid.iter_states(hid, metadata, poll_interval)
        return
    if selected_backend == "sdl":
        index = int(metadata.get("index") or 0)
        yield from sdl.iter_states(index, poll_interval=max(poll_interval, 0.004))
        return
    raise SystemExit(f"Unsupported controller backend: {selected_backend}")


def resolve_target(target: str, wsl_distro: str | None = None) -> str:
    if target.lower() not in {"wsl", "wsl2"}:
        return target

    command = ["wsl.exe"]
    if wsl_distro:
        command.extend(["-d", wsl_distro])
    command.extend(["hostname", "-I"])
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise SystemExit("Could not find wsl.exe. Use --target with an explicit WSL IP address.") from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or str(exc)).strip()
        raise SystemExit(f"Could not resolve WSL IP with {' '.join(command)}: {message}") from exc

    for token in result.stdout.split():
        try:
            address = ipaddress.ip_address(token)
        except ValueError:
            continue
        if address.version == 4 and not address.is_loopback:
            return str(address)
    raise SystemExit("Could not find a non-loopback IPv4 address from `wsl.exe hostname -I`.")


def run_host(
    target: str = "wsl",
    port: int = 27414,
    path: str | None = None,
    backend: str = "auto",
    rate_limit_hz: float = 250.0,
    wsl_distro: str | None = None,
) -> None:
    interval = 1.0 / rate_limit_hz if rate_limit_hz > 0 else 0.0
    next_send = 0.0
    resolved_target = resolve_target(target, wsl_distro)
    if resolved_target != target:
        print(f"Resolved {target} to {resolved_target}")
    address = (resolved_target, port)
    print(f"Sending controller state to {resolved_target}:{port}", flush=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for state in iter_states(path, backend=backend):
        now = time.monotonic()
        if now < next_send:
            continue
        sock.sendto(state.to_bytes(), address)
        next_send = now + interval
