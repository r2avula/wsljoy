from types import SimpleNamespace

from wsljoy import windows


def test_resolve_target_passthrough_ip():
    assert windows.resolve_target("172.25.1.2") == "172.25.1.2"


def test_resolve_target_wsl_uses_first_non_loopback_ipv4(monkeypatch):
    calls = []

    def fake_run(command, check, capture_output, text):
        calls.append(command)
        return SimpleNamespace(stdout="127.0.0.1 172.25.121.7 fe80::1")

    monkeypatch.setattr(windows.subprocess, "run", fake_run)

    assert windows.resolve_target("wsl", "Ubuntu-22.04") == "172.25.121.7"
    assert calls == [["wsl.exe", "-d", "Ubuntu-22.04", "hostname", "-I"]]


def test_run_host_defaults_to_wsl(monkeypatch):
    captured = {}

    class FakeSocket:
        def sendto(self, payload, address):
            captured["address"] = address
            raise KeyboardInterrupt

    def fake_iter_states(path=None, backend="auto"):
        from wsljoy.protocol import ControllerState

        yield ControllerState.neutral()

    monkeypatch.setattr(windows, "resolve_target", lambda target, wsl_distro=None: "172.25.121.7")
    monkeypatch.setattr(windows, "iter_states", fake_iter_states)
    monkeypatch.setattr(windows.socket, "socket", lambda *args, **kwargs: FakeSocket())

    try:
        windows.run_host()
    except KeyboardInterrupt:
        pass

    assert captured["address"] == ("172.25.121.7", 27414)
