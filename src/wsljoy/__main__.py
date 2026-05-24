from __future__ import annotations

import argparse
import sys
from collections.abc import Callable


COMMANDS = {
    "list": "List supported Windows controllers.",
    "host": "Send Windows controller state to WSL2.",
    "guest": "Create a virtual gamepad in Linux/WSL2.",
    "setup-uinput": "Configure /dev/uinput permissions.",
}


def _load_handler(command: str) -> Callable[[list[str] | None], None]:
    if command == "list":
        from .cli import list_main

        return list_main
    if command == "host":
        from .cli import host_main

        return host_main
    if command == "guest":
        from .cli import guest_main

        return guest_main
    if command == "setup-uinput":
        from .setup_uinput import main as setup_uinput_main

        return setup_uinput_main
    choices = ", ".join(COMMANDS)
    raise SystemExit(f"unknown command: {command}\nchoose one of: {choices}")


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        parser = argparse.ArgumentParser(prog="python -m wsljoy")
        subcommands = parser.add_subparsers(dest="command")
        for name, help_text in COMMANDS.items():
            subcommands.add_parser(name, help=help_text)
        parser.print_help()
        return

    command = args.pop(0)
    handler = _load_handler(command)
    try:
        handler(args)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
