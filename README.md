# wsljoy

`wsljoy` mirrors a controller connected to Windows over USB or Bluetooth into WSL2 as a normal Linux joystick device.

## Python

Use Python 3.10. The project is pinned to Python 3.10 because the Windows controller dependencies have the most reliable wheel support there.

## Windows Host

With `uv`:

```cmd
uv python install 3.10
uv sync --extra windows
uv run python -m wsljoy list
uv run python -m wsljoy host
```

With standard `venv` and `pip`:

```cmd
py -3.10 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e ".[windows]"
python -m wsljoy list
python -m wsljoy host
```

## WSL2 Guest

With `uv`:

```bash
uv sync --extra linux
uv run python -m wsljoy setup-uinput
uv run python -m wsljoy guest
```

With standard `venv` and `pip`:

```bash
python3.10 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[linux]"
python -m wsljoy setup-uinput
python -m wsljoy guest
```

`setup-uinput` first checks whether `/dev/uinput` is already writable. It only asks for sudo when your user needs to be added to the `input` group; after that, start a new WSL shell or run `newgrp input`, then run the guest without sudo.

It creates a virtual Linux input device through `/dev/uinput` using the Linux uinput API. The `/dev/input/event*` device appears after the guest receives the first packet from Windows. The `/dev/input/js*` device appears when the Linux `joydev` module is available and loaded.

Check the guest side:

```bash
ls -l /dev/uinput
groups
python -m wsljoy guest
```

In a second WSL terminal, after the Windows host is running:

```bash
ls -l /dev/input/event* /dev/input/js*
```

If `event*` exists but `js*` does not, try:

```bash
sudo modprobe joydev
```

## Network Setup

By default the Windows host targets WSL2. On Windows, `wsljoy` resolves the current WSL2 IP by running `wsl.exe hostname -I`.

With `uv`:

```cmd
uv run python -m wsljoy host
```

```bash
uv run python -m wsljoy guest --listen 0.0.0.0 --port 27414
```

With an activated venv:

```cmd
python -m wsljoy host
```

```bash
python -m wsljoy guest --listen 0.0.0.0 --port 27414
```

If you have multiple WSL distros, name the one running the guest:

```cmd
python -m wsljoy host --wsl-distro Ubuntu-22.04
```

To bypass WSL auto-resolution, pass an explicit IP address:

```cmd
python -m wsljoy host --target 172.25.121.7
```

## Controller Support

The Windows host has two reader backends:

- `ds4-hid`: exact DualShock 4 HID parser for USB and Bluetooth, preferred automatically for DS4 devices.
- `sdl`: generic SDL/pygame joystick reader, used for common Xbox, PlayStation, 8BitDo, Nintendo, Logitech, PowerA, Razer, and compatible controllers.

If the same controller is visible through both APIs, `list` shows the exact backend and hides the duplicate SDL entry. `host --backend auto` prefers `ds4-hid`; use `host --backend sdl` to force SDL.

Auto detection is the default:

```cmd
python -m wsljoy list
python -m wsljoy host --backend auto
```

Force the generic backend:

```cmd
python -m wsljoy host --backend sdl
```

The exact DS4 path supports:

- Sony vendor ID `054c`
- Product IDs `05c4` and `09cc`
- USB reports and Bluetooth reports

The SDL path covers many usual-suspect controllers but depends on the mapping SDL exposes for that device. The WSL side creates a virtual Linux gamepad with the detected vendor/product IDs when available and Linux-style axes/buttons available through `/dev/input/event*` and `/dev/input/js*`.

## Development

With `uv`:

```bash
uv python install 3.10
uv sync --all-extras --dev
uv run pytest
```

With standard `venv` and `pip`:

```bash
python3.10 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```
