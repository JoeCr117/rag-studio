from studio.databases.catalog import DEFAULTS, embedder_name, invalid_settings
from studio.databases.status import AssignmentStatus, assignment_status, database_warnings
from studio.runtimes import RUNTIMES


def test_assignment_status_compares_synced_and_current_fingerprints():
    assert assignment_status(True, True, "abc", "abc") is AssignmentStatus.SYNCED
    assert assignment_status(True, True, "abd", "abc") is AssignmentStatus.CHANGED
    assert assignment_status(True, True, "abc", "") is AssignmentStatus.NEVER_SYNCED
    assert assignment_status(True, False, "abc", "abc") is AssignmentStatus.MISSING
    assert assignment_status(False, True, "abc", "abc") is AssignmentStatus.DISCONNECTED


def test_database_warnings_name_rebuild_disconnected_and_unsynced():
    assert database_warnings(False, [AssignmentStatus.SYNCED]) == []
    warnings = database_warnings(True, [AssignmentStatus.DISCONNECTED, AssignmentStatus.CHANGED])
    assert [warning.split(":")[0].split(" ")[0] for warning in warnings] == ["Settings", "A", "Some"]


def test_settings_must_come_from_the_offered_options():
    assert invalid_settings(DEFAULTS, ["pgvector"], RUNTIMES) == []
    assert invalid_settings(DEFAULTS | {"embedder_runtime": "tpu"}, ["pgvector"], RUNTIMES) == [
        "embedder_runtime='tpu'"
    ]
    assert invalid_settings(DEFAULTS | {"chunk_min_tokens": 300, "chunk_max_tokens": 256}, ["pgvector"], RUNTIMES) == [
        "chunk_min_tokens must be below chunk_max_tokens"
    ]


def test_databases_with_the_same_model_and_runtime_share_an_embedder():
    assert embedder_name("qwen3-embedding-0.6b-q8", "cpu") == "embed-cpu-qwen3-embedding-0-6b-q8"
    assert embedder_name("qwen3-embedding-0.6b-q8", "gpu") != embedder_name("qwen3-embedding-0.6b-q8", "cpu")
