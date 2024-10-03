# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""This health check validates that GitHub Enterprise audit logs are being ingested into Google SecOps."""

import datetime
import json
import logging
import os

# Import the Google Cloud Logging client library (https://cloud.google.com/logging/docs/setup/python#view_the_logs)
import google.cloud.logging

from common import datetime_converter
from secops_api import secops_auth
from secops_api.search.udm_search import udm_search

client = google.cloud.logging.Client()  # Instantiate the logging client
# Retrieve a Cloud Logging handler based on the environment you're running in and integrates the handler with the
# Python logging module. By default this captures all logs at INFO level and higher
client.setup_logging()


def validate_github_log_ingestion(payload):
    """Validate that test events were ingested into Google SecOps."""
    http_session = secops_auth.initialize_http_session(
        google_secops_api_credentials=json.loads(os.environ["GOOGLE_SECOPS_API_CREDENTIALS"]),
        scopes=json.loads(os.environ["GOOGLE_SECOPS_AUTHORIZATION_SCOPES"]).get("GOOGLE_SECOPS_API"),
        )

    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(hours=int(os.environ["SEARCH_TIME_WINDOW_HOURS"]))

    # Convert time to string format %Y-%m-%dT%H:%M:%SZ for UDM search query
    start_time = datetime_converter.strftime(start_time)
    end_time = datetime_converter.strftime(end_time)

    udm_search_query = {
        "query": 'metadata.log_type = "GITHUB" AND metadata.product_name = "GITHUB" AND metadata.product_event_type = "api.request" AND extracted.fields["org"] = "threatpunter1" AND network.http.method = "GET" AND extracted.fields["user_programmatic_access_name"] = "github-api-health-check"',
        "start_time": start_time,
        "end_time": end_time,
    }

    logging.info(
        "Running UDM search to validate GitHub log ingestion: \n%s",
        json.dumps(udm_search_query, indent=4),
    )

    response = udm_search(
        http_session=http_session,
        query=udm_search_query["query"],
        start_time=udm_search_query["start_time"],
        end_time=udm_search_query["end_time"],
    )

    if not response.get("events"):
        logging.error(
            "0 events returned from UDM search:\n%s",
            json.dumps(udm_search_query, indent=4),
        )
        raise Exception(f"0 events returned from UDM search:\n{json.dumps(udm_search_query, indent=4)}")
    else:
        logging.info(
            "%s events returned from UDM search:\n%s", len(response["events"]), json.dumps(udm_search_query, indent=4)
        )

        return "OK"
