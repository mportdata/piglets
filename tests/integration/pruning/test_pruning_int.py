from piglets import (
    Database, 
    DeletionColumns,
    DeletionSet,
    PreservationColumns, 
    PreservationSet,
    Pruner,
    Table
)


def test_get_tables_and_fields_to_preserve(
    model_name,
    natural_language_query,
    logical_plan,
    duckdb_database,
):
    pruner = Pruner(model_name=model_name)
    fields_to_preserve = pruner.get_tables_and_fields_to_preserve(
        natural_language_query=natural_language_query, 
        database=duckdb_database,
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
    natural_language_query,
    logical_plan,
    duckdb_database,
):
    pruner = Pruner(model_name=model_name)
    fields_to_delete = pruner.get_tables_and_fields_to_delete(
        natural_language_query=natural_language_query,
        database=duckdb_database,
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

def test_preservation_set_to_database_type(
    model_name,
    natural_language_query,
    logical_plan,
    duckdb_database,
):
    pruner = Pruner(model_name=model_name)
    fields_to_preserve = pruner.get_tables_and_fields_to_preserve(
        natural_language_query=natural_language_query, 
        database=duckdb_database,
        logical_plan=logical_plan
    )

    preserved_database = fields_to_preserve.to_database_type(duckdb_database)

    assert isinstance(preserved_database, Database)
    assert preserved_database.name == duckdb_database.name
    assert isinstance(preserved_database.tables, list)
    assert all(isinstance(table, Table) for table in preserved_database.tables)


def test_deletion_set_to_database_type(
    model_name,
    natural_language_query,
    logical_plan,
    duckdb_database,
):
    pruner = Pruner(model_name=model_name)
    fields_to_delete = pruner.get_tables_and_fields_to_delete(
        natural_language_query=natural_language_query,
        database=duckdb_database,
        logical_plan=logical_plan
    )

    deleted_database = fields_to_delete.to_database_type(duckdb_database)

    assert isinstance(deleted_database, Database)
    assert deleted_database.name == duckdb_database.name
    assert isinstance(deleted_database.tables, list)
    assert all(isinstance(table, Table) for table in deleted_database.tables)

def test_dual_pathway_pruning(
    model_name,
    natural_language_query,
    logical_plan,
    duckdb_database,
):
    pruner = Pruner(model_name=model_name)
    pruned_database: Database = pruner.dual_pathway_pruning(
        natural_language_query=natural_language_query,
        database=duckdb_database,
        logical_plan=logical_plan
    )

    assert isinstance(pruned_database, Database)
