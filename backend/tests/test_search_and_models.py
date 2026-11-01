from studio.databases.catalog import EMBEDDING_MODELS, form_options
from studio.databases.engines.base import vector_preview
from studio.databases.engines.pgvector_engine import column_type, schema_sql


def test_vectors_above_hnsw_limit_are_stored_as_halfvec():
    assert column_type(1024) == "vector"
    assert column_type(2000) == "vector"
    assert column_type(2560) == "halfvec"
    assert "halfvec_cosine_ops" in schema_sql(2560)
    assert "vector_cosine_ops" in schema_sql(768)


def test_vector_preview_shows_leading_values_and_norm():
    values, norm = vector_preview([3.0, 4.0] + [0.0] * 20)
    assert values == [3.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert norm == 5.0


def test_form_options_report_each_models_download_status():
    options = form_options(
        ["pgvector"], {"bge-m3-q8": "downloading", "nomic-embed-text-v1.5-q8": "downloaded"}, ("cpu",)
    )
    status = {model["key"]: model["download_status"] for model in options["embedding_models"]}
    assert status["bge-m3-q8"] == "downloading"
    assert status["nomic-embed-text-v1.5-q8"] == "downloaded"
    assert status["qwen3-embedding-0.6b-q8"] == "missing"
    assert set(status) == set(EMBEDDING_MODELS)
    assert options["runtimes"] == ["cpu"]
