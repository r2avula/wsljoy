from __future__ import annotations

import argparse
import getpass
import os
import platform
import shutil
import sys
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import grp


RULE_PATH = Path("/etc/udev/rules.d/70-wsljoy-uinput.rules")
MODULES_PATH = Path("/etc/modules-load.d/wsljoy-uinput.conf")
RULE_TEXT = 'KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"\n'
MODULES_TEXT = "uinput\n"


def _run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, text=True, capture_output=True)


def _current_login_user() -> str:
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        return sudo_user
    return getpass.getuser()


def _run_with_sudo() -> None:
    sudo = shutil.which("sudo")
    if sudo is None:
        raise SystemExit("Root access is required and sudo was not found.")
    os.execvp(sudo, [sudo, sys.executable, "-m", "wsljoy.setup_uinput"])


def _grp():
    import grp

    return grp


def _pwd():
    import pwd

    return pwd


def _ensure_linux() -> None:
    if platform.system() != "Linux":
        raise SystemExit("setup-uinput is only available on Linux/WSL2.")


def _ensure_input_group() -> None:
    grp = _grp()
    try:
        grp.getgrnam("input")
    except KeyError:
        _run(["groupadd", "--system", "input"])


def _user_groups(user: str) -> set[str]:
    grp = _grp()
    pwd = _pwd()
    user_info = pwd.getpwnam(user)
    groups = {group.gr_name for group in grp.getgrall() if user in group.gr_mem}
    groups.add(grp.getgrgid(user_info.pw_gid).gr_name)
    return groups


def _user_in_input_group(user: str) -> bool:
    return "input" in _user_groups(user)


def _ensure_user_in_group(user: str) -> bool:
    if _user_in_input_group(user):
        return False
    _run(["usermod", "-aG", "input", user])
    return True


def _write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text() == content:
        return False
    path.write_text(content)
    return True


def _load_uinput() -> None:
    if shutil.which("modprobe"):
        _run(["modprobe", "uinput"])


def _reload_udev() -> None:
    if shutil.which("udevadm"):
        _run(["udevadm", "control", "--reload-rules"], check=False)
        _run(["udevadm", "trigger", "--subsystem-match=misc"], check=False)


def _fix_current_device() -> None:
    device = Path("/dev/uinput")
    if not device.exists():
        return
    grp = _grp()
    gid = grp.getgrnam("input").gr_gid
    os.chown(device, 0, gid)
    os.chmod(device, 0o660)


def _has_uinput_write_access() -> bool:
    return os.access("/dev/uinput", os.W_OK)


def _non_root_preflight(user: str) -> None:
    if _has_uinput_write_access():
        print("/dev/uinput is already writable. No sudo needed.")
        print("Run without sudo with: python -m wsljoy guest")
        raise SystemExit(0)
    if not _user_in_input_group(user):
        print(f"{user} is not in the input group; requesting sudo once to add it.")
        _run_with_sudo()
    raise SystemExit(
        "Your user is already in the input group, but /dev/uinput is not writable. "
        "Start a new WSL shell or run `newgrp input`, then retry."
    )


def install() -> None:
    _ensure_linux()
    user = _current_login_user()
    if os.geteuid() != 0:
        _non_root_preflight(user)
    _ensure_input_group()
    added_group = _ensure_user_in_group(user)
    rule_changed = _write_if_changed(RULE_PATH, RULE_TEXT)
    modules_changed = _write_if_changed(MODULES_PATH, MODULES_TEXT)
    _load_uinput()
    _reload_udev()
    _fix_current_device()

    print("Configured /dev/uinput access for wsljoy.")
    if rule_changed:
        print(f"Wrote {RULE_PATH}")
    if modules_changed:
        print(f"Wrote {MODULES_PATH}")
    if added_group:
        print(f"Added {user} to the input group. Start a new WSL shell or run `newgrp input` before running without sudo.")
    else:
        print(f"{user} is already in the input group.")
    print("Run without sudo with: python -m wsljoy guest")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Configure /dev/uinput permissions for wsljoy.")
    parser.parse_args(argv)
    install()


if __name__ == "__main__":
    main()
