from wsljoy.__main__ import main


def test_module_cli_help(capsys):
    main(["--help"])
    output = capsys.readouterr().out
    assert "python -m wsljoy" in output
    assert "host" in output
    assert "setup-uinput" in output
