import importlib


def test_news_fetcher_exists():
    module = importlib.import_module("backend.auth.feature")
    assert hasattr(module, "fetch_news_headlines")
    assert callable(module.fetch_news_headlines)
