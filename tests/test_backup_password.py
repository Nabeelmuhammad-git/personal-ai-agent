import importlib


def test_backup_password_module_and_validation():
    module = importlib.import_module("backend.auth.config")
    assert hasattr(module, "BACKUP_PASSWORD")
    assert module.BACKUP_PASSWORD
    assert isinstance(module.BACKUP_PASSWORD, str)
