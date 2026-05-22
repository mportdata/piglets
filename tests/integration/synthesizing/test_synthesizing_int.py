import json

import pytest

from piglets import (
    DatabaseProfileResult,
    ParallelDataProfiler,
    SearchSpace,
    GlobalSynthesizer,
)


@pytest.fixture
def profiler(model_name, pruned_duckdb_database_schema) -> ParallelDataProfiler:
    return ParallelDataProfiler(
        model_name=model_name,
        search_space=SearchSpace(database_schema=pruned_duckdb_database_schema),
    )


@pytest.fixture
def synthesizer(model_name, pruned_duckdb_database_schema, duckdb_connector) -> GlobalSynthesizer:
    return GlobalSynthesizer(
        search_space=SearchSpace(database_schema=pruned_duckdb_database_schema),
        database_connector=duckdb_connector,
        model_name=model_name,
        model_provider=None,
    )


@pytest.fixture
def database_profile_result(
    profiler,
    question,
    pruned_duckdb_database_schema,
    duckdb_connector,
    semantic_linking_result,
) -> DatabaseProfileResult:
    return profiler.profile_database(
        search_space=SearchSpace(database_schema=pruned_duckdb_database_schema),
        database_connector=duckdb_connector,
        question=question,
        semantic_linking_result=semantic_linking_result,
    )


def test_synthesize_observations(
    synthesizer,
    question,
    semantic_linking_result,
    database_profile_result,
):
    synthesis_run = synthesizer.synthesize_observations(
        question=question,
        semantic_linking_result=semantic_linking_result,
        database_profile_result=database_profile_result,
    )

    print("Synthesis Run Result")
    print("=" * 80)
    print(json.dumps(synthesis_run.model_dump(), indent=2))
