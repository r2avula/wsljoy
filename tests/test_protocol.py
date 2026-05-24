from wsljoy.protocol import ControllerState, apply_deadzone


def test_controller_state_round_trip():
    state = ControllerState.neutral()
    state.axes["lx"] = 123
    state.buttons["cross"] = 1

    restored = ControllerState.from_bytes(state.to_bytes())

    assert restored.axes["lx"] == 123
    assert restored.buttons["cross"] == 1
    assert restored.vendor_id == state.vendor_id
    assert restored.connection == "unknown"


def test_apply_deadzone_zeroes_small_stick_noise():
    assert apply_deadzone(257) == 0
    assert apply_deadzone(-1024) == 0
    assert apply_deadzone(1285) == 1285
