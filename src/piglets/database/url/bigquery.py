import os
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import quote_plus, urlencode


class BigQueryURL:
    def __init__(
        self,
        project_id: str | None = None,
        dataset: str | None = None,
        credentials_path: str | None = None,
        credentials_base64: str | None = None,
        location: str | None = None,
        arraysize: int | None = None,
        list_tables_page_size: int | None = None,
        clustering_fields: Sequence[str] | None = None,
        create_disposition: str | None = None,
        destination: str | None = None,
        destination_encryption_configuration: str | None = None,
        dry_run: bool | None = None,
        labels: Mapping[str, str] | None = None,
        maximum_bytes_billed: int | None = None,
        priority: str | None = None,
        schema_update_options: Sequence[str] | None = None,
        use_query_cache: bool | None = None,
        write_disposition: str | None = None,
        user_supplied_client: bool | None = None,
    ):
        self.project_id = project_id
        self.dataset = dataset
        self.credentials_path = credentials_path
        self.credentials_base64 = credentials_base64
        self.location = location
        self.arraysize = arraysize
        self.list_tables_page_size = list_tables_page_size
        self.clustering_fields = clustering_fields
        self.create_disposition = create_disposition
        self.destination = destination
        self.destination_encryption_configuration = destination_encryption_configuration
        self.dry_run = dry_run
        self.labels = labels
        self.maximum_bytes_billed = maximum_bytes_billed
        self.priority = priority
        self.schema_update_options = schema_update_options
        self.use_query_cache = use_query_cache
        self.write_disposition = write_disposition
        self.user_supplied_client = user_supplied_client

    @staticmethod
    def _format_bool(value: bool) -> str:
        return "true" if value else "false"

    @staticmethod
    def _format_sequence(value: Sequence[str]) -> str:
        return ",".join(value)

    @staticmethod
    def _format_labels(value: Mapping[str, str]) -> str:
        return ",".join(f"{key}:{label_value}" for key, label_value in value.items())

    def _query_parameters(self, hide_password: bool = False) -> dict[str, Any]:
        credentials_base64 = (
            "***"
            if hide_password and self.credentials_base64
            else self.credentials_base64
        )
        query = {
            "credentials_path": self.credentials_path,
            "credentials_base64": credentials_base64,
            "location": self.location,
            "arraysize": self.arraysize,
            "list_tables_page_size": self.list_tables_page_size,
            "clustering_fields": (
                self._format_sequence(self.clustering_fields)
                if self.clustering_fields is not None
                else None
            ),
            "create_disposition": self.create_disposition,
            "destination": self.destination,
            "destination_encryption_configuration": (
                self.destination_encryption_configuration
            ),
            "dry_run": self._format_bool(self.dry_run)
            if self.dry_run is not None
            else None,
            "labels": self._format_labels(self.labels)
            if self.labels is not None
            else None,
            "maximum_bytes_billed": self.maximum_bytes_billed,
            "priority": self.priority,
            "schema_update_options": (
                self._format_sequence(self.schema_update_options)
                if self.schema_update_options is not None
                else None
            ),
            "use_query_cache": self._format_bool(self.use_query_cache)
            if self.use_query_cache is not None
            else None,
            "write_disposition": self.write_disposition,
            "user_supplied_client": self._format_bool(self.user_supplied_client)
            if self.user_supplied_client is not None
            else None,
        }
        return {key: str(value) for key, value in query.items() if value is not None}

    def render_as_string(self, hide_password: bool = True) -> str:
        project_id = self.project_id or os.getenv("GOOGLE_CLOUD_PROJECT_ID")

        if project_id and self.dataset:
            connection_string = (
                f"bigquery://{quote_plus(project_id)}/{quote_plus(self.dataset)}"
            )
        elif project_id:
            connection_string = f"bigquery://{quote_plus(project_id)}"
        elif self.dataset:
            connection_string = f"bigquery:///{quote_plus(self.dataset)}"
        else:
            connection_string = "bigquery:///"

        query = self._query_parameters(hide_password=hide_password)
        if query:
            connection_string += "?" + urlencode(query)
        elif not self.dataset and not project_id:
            connection_string = "bigquery://"

        return connection_string
