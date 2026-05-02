from piglets.semantic_linking import SemanticLinker

def test_semantic_linking(
        model_name,
        natural_language_query,
        logical_plan,
        duckdb_database,
    ):
    linker = SemanticLinker(model_name=model_name)
    linking_result = linker.link(
        natural_language_query=natural_language_query,
        database=duckdb_database,
        logical_plan=logical_plan,
    )
    
    assert linking_result is not None
    assert linking_result.database_structure != ""
    assert linking_result.query_specific_content_analysis != ""
    assert isinstance(linking_result.table_functions, dict)
    
