from collectors.news_api import NewsDataCollector


def test_default_values_when_no_args_no_env(monkeypatch):
    monkeypatch.delenv("NEWS_CHUNK_SIZE", raising=False)
    monkeypatch.delenv("NEWS_CHUNK_OVERLAP", raising=False)

    collector = NewsDataCollector()

    assert collector.text_splitter._chunk_size == 1000
    assert collector.text_splitter._chunk_overlap == 200


def test_explicit_args_override_env(monkeypatch):
    monkeypatch.setenv("NEWS_CHUNK_SIZE", "9999")

    collector = NewsDataCollector(chunk_size=500, chunk_overlap=50)

    assert collector.text_splitter._chunk_size == 500
    assert collector.text_splitter._chunk_overlap == 50


def test_env_vars_used_when_no_args(monkeypatch):
    monkeypatch.setenv("NEWS_CHUNK_SIZE", "2000")
    monkeypatch.setenv("NEWS_CHUNK_OVERLAP", "400")

    collector = NewsDataCollector()

    assert collector.text_splitter._chunk_size == 2000
    assert collector.text_splitter._chunk_overlap == 400


def test_overlap_gte_chunk_size_clamped(monkeypatch):
    monkeypatch.delenv("NEWS_CHUNK_SIZE", raising=False)
    monkeypatch.delenv("NEWS_CHUNK_OVERLAP", raising=False)

    collector = NewsDataCollector(chunk_size=100, chunk_overlap=100)

    assert collector.text_splitter._chunk_overlap == 99


def test_invalid_env_chunk_size_defaults(monkeypatch):
    monkeypatch.setenv("NEWS_CHUNK_SIZE", "abc")
    monkeypatch.delenv("NEWS_CHUNK_OVERLAP", raising=False)

    collector = NewsDataCollector()

    assert collector.text_splitter._chunk_size == 1000


def test_zero_chunk_size_env_defaults(monkeypatch):
    monkeypatch.setenv("NEWS_CHUNK_SIZE", "0")
    monkeypatch.delenv("NEWS_CHUNK_OVERLAP", raising=False)

    collector = NewsDataCollector()

    assert collector.text_splitter._chunk_size == 1000
