import importlib


def test_face_auth_module_exists_and_returns_int():
    module = importlib.import_module("backend.auth.recoganize")
    assert hasattr(module, "AuthenticateFace")
    result = module.AuthenticateFace()
    assert isinstance(result, int)
