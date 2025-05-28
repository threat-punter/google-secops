import logging
from typing import Any

from google.auth.transport import requests

LOGGER = logging.getLogger()

class DataTableManager:
    def __init__(self, google_secops_api_base_url):
        self.google_secops_api_base_url = google_secops_api_base_url

    def bulk_create_data_table_rows(
        self,
        http_session: requests.AuthorizedSession,
        resource_name: str,
        row_values: list[list[str]],
        max_retries: int = 3,
        ) -> dict[str, Any]:
        """Create data table rows in bulk.

        Args:
            http_session: Authorized session for HTTP requests.
            resource_name: The resource name of the data table to create rows for.
                Format - projects/{project}/locations/{location}/instances/{instance}/dataTables/{data_table_name}
            row_values: The values for the row. These values should be in the same order
                as data table's columns. Example:
                [["user1", "desktop1"], ["user2", "desktop2"]] A maximum of 1,000 rows can be created in a single request.
            max_retries (optional): Maximum number of times to retry HTTP request if
                certain response codes are returned. For example: HTTP response status
                code 429 (Too Many Requests)

        Returns:
            New data table rows.

        Raises:
            requests.exceptions.HTTPError: HTTP request resulted in an error
            (response.status_code >= 400).
            requests.exceptions.JSONDecodeError: If the server response is not valid
            JSON.
        """
        url = f"{self.google_secops_api_base_url}/{resource_name}/dataTableRows:bulkCreate"

        # Populate a list of data table row requests. Reference:
        # https://cloud.google.com/chronicle/docs/reference/rest/v1alpha/projects.locations.instances.dataTables.dataTableRows/bulkCreate#CreateDataTableRowRequest
        data_table_row_requests = []
        for row in row_values:
            data_table_row_requests.append({
                "parent": resource_name,
                "data_table_row": {"values": row},
            })

        body = {"requests": data_table_row_requests}

        response = None

        for _ in range(max(max_retries, 0) + 1):
            response = http_session.request(method="POST", url=url, json=body)

            if response.status_code >= 400:
                LOGGER.warning(response.text)

            if response.status_code == 429:
                LOGGER.warning(
                    "API rate limit exceeded. Sleeping for 60s before retrying"
                )
                time.sleep(60)
            else:
                break

        response.raise_for_status()

        return response.json()

    def bulk_replace_data_table_rows(
        self,
        http_session: requests.AuthorizedSession,
        resource_name: str,
        row_values: list[list[str]],
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Replace all rows in a data table.

        Args:
            http_session: Authorized session for HTTP requests.
            resource_name: The resource name of the data table to replace rows for.
                Format - projects/{project}/locations/{location}/instances/{instance}/dataTables/{data_table_name}
            row_values: The values for the row. These values should be in the same order
                as data table's columns. Example:
                [["user1", "desktop1"], ["user2", "desktop2"]]
            max_retries (optional): Maximum number of times to retry HTTP request if
                certain response codes are returned. For example: HTTP response status
                code 429 (Too Many Requests)

        Returns:
            New data table rows.

        Raises:
            requests.exceptions.HTTPError: HTTP request resulted in an error
            (response.status_code >= 400).
            requests.exceptions.JSONDecodeError: If the server response is not valid
            JSON.
        """
        url = f"{self.google_secops_api_base_url}/{resource_name}/dataTableRows:bulkReplace"

        # Populate a list of data table row requests. Reference:
        # https://cloud.google.com/chronicle/docs/reference/rest/v1alpha/projects.locations.instances.dataTables.dataTableRows/bulkCreate#CreateDataTableRowRequest
        data_table_row_requests = []
        for row in row_values:
            data_table_row_requests.append(
                {
                    "parent": resource_name,
                    "data_table_row": {"values": row},
                }
            )

        body = {"requests": data_table_row_requests}

        response = None

        for _ in range(max(max_retries, 0) + 1):
            response = http_session.request(method="POST", url=url, json=body)

            if response.status_code >= 400:
                LOGGER.warning(response.text)

            if response.status_code == 429:
                LOGGER.warning(
                    "API rate limit exceeded. Sleeping for 60s before retrying"
                )
                time.sleep(60)
            else:
                break

        response.raise_for_status()

        return response.json()


    def update_remote_data_table_rows(
        self,
        http_session: requests.AuthorizedSession,
        data_table_name: str,
        data_table_resource_name: str,
        row_values: list[str],
        ):
        """Update the content (rows) for a data table in Google SecOps.

        This function takes a list of data table row values as input and does the following.

        1. Replaces the rows in the data table using the first 1,000 row values provided as input.
        2. If more than 1,000 row values were provided as input, create the rows in the data table in batches of 1,000.

        Args:
            http_session: Authorized session for HTTP requests.
            data_table_name: The name of the data table.
            data_table_resource_name: The resource name of the data table to update. Format:
                projects/{project}/locations/{location}/instances/{instance}/dataTables/{data_table_name}
            row_values: A list of data table row values.
                Example: [["user1", "desktop1"], ["user2", "desktop2"]]

        Returns:
            None.
        """
        total_row_count = len(row_values)

        # Use the dataTableRows.bulkReplace API method to replace all rows in the
        # data table with a maximum of 1,000 rows. The remaining rows (if there are
        # more than 1,000) will be written using the dataTableRows.bulkCreate API
        # method
        rows_to_create = row_values[:1000]
        LOGGER.info(f"Attempting to replace all rows in data table {data_table_name} with {len(rows_to_create)} rows")

        self.bulk_replace_data_table_rows(
            http_session=http_session,
            resource_name=data_table_resource_name,
            row_values=rows_to_create,
        )
        LOGGER.info(f"Successfully replaced all rows in data table {data_table_name} with {len(rows_to_create)} rows")

        # Use the dataTableRows.bulkCreate API method to populate the data table
        # with the remaining rows from the local file (if there are any). Maximum
        # of 1,000 rows per request.
        if total_row_count > 1000:
        # Store the remaining number of rows that need to be created
            rows_to_create = row_values[1000:]

            LOGGER.info(f"Attempting to create {len(rows_to_create)} remaining rows in data table {data_table_name}")
            start_index = 0
            while start_index < len(rows_to_create):
                end_index = min(start_index + 1000, len(rows_to_create))
                batch = rows_to_create[start_index:end_index]
                LOGGER.info(f"Attempting to create rows {start_index + 1001}-{end_index + 1000} in data table {data_table_name}")

                self.bulk_create_data_table_rows(
                    http_session=http_session,
                    resource_name=data_table_resource_name,
                    row_values=batch,
                )
                LOGGER.info(f"Successfully created rows {start_index + 1001}-{end_index + 1000} in data table {data_table_name}")
                start_index = end_index

        LOGGER.info(f"Created a total of {total_row_count} rows in data table {data_table_name}")

        return