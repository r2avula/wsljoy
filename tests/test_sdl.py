from wsljoy.controllers.sdl import _guid_ids


def test_guid_ids_use_sdl_little_endian_fields():
    assert _guid_ids("030000005e0400008e02000000000000") == (0x045E, 0x028E)
