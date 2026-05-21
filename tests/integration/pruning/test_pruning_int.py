from piglets import (
    DatabaseSchema, 
    DeletionColumns,
    DeletionSet,
    DualPathwayPruner,
    PreservationColumns, 
    PreservationSet,
    SearchSpace,
    TableSchema
)


def test_get_tables_and_fields_to_preserve(
    model_name,
    question,
    logical_plan,
    duckdb_search_space,
):
    dual_pathway_pruner = DualPathwayPruner(model_name=model_name)
    fields_to_preserve = dual_pathway_pruner.get_tables_and_fields_to_preserve(
        question=question, 
        search_space=duckdb_search_space,
        logical_plan=logical_plan
    )

    assert isinstance(fields_to_preserve, PreservationSet)
    assert isinstance(fields_to_preserve.relevant_tables, list)
    assert isinstance(fields_to_preserve.relevant_columns, list)
    assert all(isinstance(col, PreservationColumns) for col in fields_to_preserve.relevant_columns)
    assert all(isinstance(table, str) for table in fields_to_preserve.relevant_tables)
    assert all(isinstance(col.table, str) for col in fields_to_preserve.relevant_columns)
    assert all(
        isinstance(column, str)
        for col in fields_to_preserve.relevant_columns
        for column in col.columns
    )


def test_get_tables_and_fields_to_delete(
    model_name,
    question,
    logical_plan,
    duckdb_search_space,
):
    dual_pathway_pruner = DualPathwayPruner(model_name=model_name)
    fields_to_delete = dual_pathway_pruner.get_tables_and_fields_to_delete(
        question=question,
        search_space=duckdb_search_space,
        logical_plan=logical_plan
    )

    assert isinstance(fields_to_delete, DeletionSet)
    assert isinstance(fields_to_delete.obviously_irrelevant_tables, list)
    assert isinstance(fields_to_delete.obviously_irrelevant_columns, list)
    assert all(isinstance(col, DeletionColumns) for col in fields_to_delete.obviously_irrelevant_columns)
    assert all(isinstance(table, str) for table in fields_to_delete.obviously_irrelevant_tables)
    assert all(isinstance(col.table, str) for col in fields_to_delete.obviously_irrelevant_columns)
    assert all(
        isinstance(column, str)
        for col in fields_to_delete.obviously_irrelevant_columns
        for column in col.columns
    )

def test_preservation_set_to_database_schema(
    model_name,
    question,
    logical_plan,
    duckdb_search_space,
    duckdb_database_schema,
):
    dual_pathway_pruner = DualPathwayPruner(model_name=model_name)
    fields_to_preserve = dual_pathway_pruner.get_tables_and_fields_to_preserve(
        question=question, 
        search_space=duckdb_search_space,
        logical_plan=logical_plan
    )

    preserved_database_schema = fields_to_preserve.to_database_schema(duckdb_database_schema)

    assert isinstance(preserved_database_schema, DatabaseSchema)
    assert preserved_database_schema.name == duckdb_database_schema.name
    assert preserved_database_schema.database_type == duckdb_database_schema.database_type
    assert isinstance(preserved_database_schema.table_schemas, list)
    assert all(isinstance(table, TableSchema) for table in preserved_database_schema.table_schemas)


def test_deletion_set_to_database_schema(
    model_name,
    question,
    logical_plan,
    duckdb_search_space,
    duckdb_database_schema,
):
    dual_pathway_pruner = DualPathwayPruner(model_name=model_name)
    fields_to_delete = dual_pathway_pruner.get_tables_and_fields_to_delete(
        question=question,
        search_space=duckdb_search_space,
        logical_plan=logical_plan
    )

    deleted_database_schema = fields_to_delete.to_database_schema(duckdb_database_schema)

    assert isinstance(deleted_database_schema, DatabaseSchema)
    assert deleted_database_schema.name == duckdb_database_schema.name
    assert deleted_database_schema.database_type == duckdb_database_schema.database_type
    assert isinstance(deleted_database_schema.table_schemas, list)
    assert all(isinstance(table, TableSchema) for table in deleted_database_schema.table_schemas)

def test_dual_pathway_pruning(
    model_name,
    question,
    logical_plan,
    duckdb_search_space,
):
    dual_pathway_pruner = DualPathwayPruner(model_name=model_name)
    pruned_search_space: SearchSpace = dual_pathway_pruner.dual_pathway_pruning(
        question=question,
        search_space=duckdb_search_space,
        logical_plan=logical_plan
    )
    pruned_database_schema = pruned_search_space.database_schema

    assert isinstance(pruned_search_space, SearchSpace)
    assert isinstance(pruned_database_schema, DatabaseSchema)
    assert duckdb_search_space.database_schema is not None
    assert pruned_database_schema.database_type == duckdb_search_space.database_schema.database_type
