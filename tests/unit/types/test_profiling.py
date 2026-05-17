from piglets.types import TableProfileColumnResult, TableProfileResult


def test_table_profile_result_can_describe_relevant_columns():
    result = TableProfileResult(
        relevant=True,
        relevant_columns=[
            TableProfileColumnResult(
                column_name="status",
                relevance_reason="Identifies cancelled orders.",
                observations="Values include cancelled and complete.",
            )
        ],
        table_summary="Order status table relevant to cancellation analysis.",
    )

    assert result.relevant is True
    assert len(result.relevant_columns) == 1
    assert result.relevant_columns[0].column_name == "status"
    assert result.table_summary
