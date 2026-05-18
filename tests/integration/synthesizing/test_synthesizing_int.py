import json

import pytest

from piglets import (
    DatabaseProfileResult,
    Profiler,
    Synthesizer,
)


@pytest.fixture
def profiler(model_name, pruned_duckdb_database) -> Profiler:
    return Profiler(model_name=model_name, database=pruned_duckdb_database)


@pytest.fixture
def synthesizer(model_name, pruned_duckdb_database, duckdb_connector) -> Synthesizer:
    return Synthesizer(
        database=pruned_duckdb_database,
        database_connector=duckdb_connector,
        model_name=model_name,
        model_provider=None,
    )


@pytest.fixture
def database_profile_result(
    profiler,
    natural_language_query,
    pruned_duckdb_database,
    duckdb_connector,
    semantic_linking_result,
) -> DatabaseProfileResult:
    return profiler.profile_database(
        database=pruned_duckdb_database,
        database_connector=duckdb_connector,
        natural_language_query=natural_language_query,
        semantic_linking_result=semantic_linking_result,
    )


def test_synthesize_observations(
    synthesizer,
    natural_language_query,
    semantic_linking_result,
    database_profile_result,
):
    synthesis_run = synthesizer.synthesize_observations(
        natural_language_question=natural_language_query,
        semantic_linking_result=semantic_linking_result,
        database_profile_result=database_profile_result,
    )

    print("Synthesis Run Result")
    print("=" * 80)
    print(json.dumps(synthesis_run.model_dump(), indent=2))
