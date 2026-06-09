"""Tests for embedding service batching without loading the real model."""

from app.wiki.embedding_service import BGEEmbeddingService


class FakeModel:
    """Small fake sentence-transformers-compatible model."""

    def encode(self, texts, **kwargs):
        _ = kwargs
        return [[float(index), 1.0] for index, _text in enumerate(texts)]


async def test_embedding_service_filters_empty_texts(monkeypatch) -> None:
    service = BGEEmbeddingService()

    async def fake_get_model():
        return FakeModel()

    monkeypatch.setattr(service, "_get_model", fake_get_model)

    embeddings = await service.embed_texts([" first ", "", "second"])

    assert embeddings == [[0.0, 1.0], [1.0, 1.0]]
