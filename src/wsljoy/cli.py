from __future__ import annotations

import argparse


def list_main(argv: list[str] | None = None) -> None:
    from .controllers.common import decode_hid_path
    from .windows import list_controllers

    devices = list_controllers()
    if not devices:
        print("No supported game controllers found.")
        return
    for index, device in enumerate(devices):
        product = device.get("product_string") or "Wireless Controller"
        path = decode_hid_path(device.get("path"))
        vendor_id = int(device.get("vendor_id") or 0)
        product_id = int(device.get("product_id") or 0)
        print(
            f"{index}: [{device.get('backend', 'unknown')}] {product} "
            f"vid={vendor_id:04x} pid={product_id:04x} "
            f"path={path}"
        )


def host_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Send Windows controller state to WSL2.")
    parser.add_argument("--target", default="wsl", help="WSL/Linux UDP target address. Defaults to `wsl`, resolved via wsl.exe; explicit IPs are also allowed.")
    parser.add_argument("--wsl-distro", help="WSL distro name to use when --target is wsl/wsl2.")
    parser.add_argument("--port", type=int, default=27414, help="UDP target port.")
    parser.add_argument("--path", help="Controller path from wsljoy-list.")
    parser.add_argument(
        "--backend",
        choices=("auto", "ds4-hid", "sdl"),
        default="auto",
        help="Controller reader backend.",
    )
    parser.add_argument("--rate", type=float, default=250.0, help="Maximum send rate in Hz.")
    args = parser.parse_args(argv)

    from .windows import run_host

    try:
        run_host(
            target=args.target,
            port=args.port,
            path=args.path,
            backend=args.backend,
            rate_limit_hz=args.rate,
            wsl_distro=args.wsl_distro,
        )
    except KeyboardInterrupt:
        print("\nStopped.")


def guest_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Create a virtual gamepad in Linux/WSL2.")
    parser.add_argument("--listen", default="0.0.0.0", help="UDP listen address.")
    parser.add_argument("--port", type=int, default=27414, help="UDP listen port.")
    parser.add_argument("--stale-after", type=float, default=1.0, help="Neutralize after silence.")
    args = parser.parse_args(argv)

    from .linux import run_guest

    try:
        run_guest(listen=args.listen, port=args.port, stale_after=args.stale_after)
    except KeyboardInterrupt:
        print("\nStopped.")
