from piglets import SemanticLinker

def test_semantic_linking(
        model_name,
        question,
        hypothesis,
        duckdb_search_space,
    ):
    linker = SemanticLinker(model_name=model_name)
    linking_result = linker.link(
        question=question,
        search_space=duckdb_search_space,
        hypothesis=hypothesis,
    )
    
    assert linking_result is not None
    assert linking_result.database_structure != ""
    assert linking_result.query_specific_content_analysis != ""
    assert isinstance(linking_result.table_functions, dict)
    
