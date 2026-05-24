import os

import pytest

from wsljoy import setup_uinput


def test_non_root_preflight_exits_without_sudo_when_uinput_is_writable(monkeypatch, capsys):
    called = False

    def fake_sudo():
        nonlocal called
        called = True

    monkeypatch.setattr(setup_uinput, "_has_uinput_write_access", lambda: True)
    monkeypatch.setattr(setup_uinput, "_run_with_sudo", fake_sudo)

    with pytest.raises(SystemExit) as exc:
        setup_uinput._non_root_preflight("avula")

    assert exc.value.code == 0
    assert called is False
    assert "No sudo needed" in capsys.readouterr().out


def test_non_root_preflight_uses_sudo_only_when_user_missing_input_group(monkeypatch):
    called = False

    def fake_sudo():
        nonlocal called
        called = True
        raise SystemExit(0)

    monkeypatch.setattr(setup_uinput, "_has_uinput_write_access", lambda: False)
    monkeypatch.setattr(setup_uinput, "_user_in_input_group", lambda user: False)
    monkeypatch.setattr(setup_uinput, "_run_with_sudo", fake_sudo)

    with pytest.raises(SystemExit):
        setup_uinput._non_root_preflight("avula")

    assert called is True


def test_non_root_preflight_does_not_sudo_when_user_already_in_input_group(monkeypatch):
    called = False

    def fake_sudo():
        nonlocal called
        called = True

    monkeypatch.setattr(setup_uinput, "_has_uinput_write_access", lambda: False)
    monkeypatch.setattr(setup_uinput, "_user_in_input_group", lambda user: True)
    monkeypatch.setattr(setup_uinput, "_run_with_sudo", fake_sudo)

    with pytest.raises(SystemExit) as exc:
        setup_uinput._non_root_preflight("avula")

    assert called is False
    assert "newgrp input" in str(exc.value)
