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
"""This function performs a basic read operation via GitHub's API as part of a health check.

The health check that this job is a part of is designed to validate that GitHub Enterprise audit logs are being
ingested into Google SecOps.
"""

import json
import logging
import os

import requests

# Import the Google Cloud Logging client library (https://cloud.google.com/logging/docs/setup/python#view_the_logs)
import google.cloud.logging

client = google.cloud.logging.Client()  # Instantiate the logging client
# Retrieve a Cloud Logging handler based on the environment you're running in and integrates the handler with the
# Python logging module. By default this captures all logs at INFO level and higher
client.setup_logging()


def ping_github_api(payload):
    """Perform a simple read operation via GitHub's API.

    This function carries out a small, basic, read operation via GitHub's API as part of a health check to validate that
    GitHub Enterprise audit logs are being sent to Google SecOps for ingestion.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ['HEALTH_CHECK_GITHUB_PAT']}",
    }

    logging.info("Performing GitHub API health check")

    github_org_name = os.environ["HEALTH_CHECK_GITHUB_ORG_NAME"]
    logging.info("Attempting to retrieve GitHub organization information for %s", github_org_name)
    response = requests.get(f"https://api.github.com/orgs/{github_org_name}", headers=headers)

    if response.status_code >= 400:
        print(response.text)
        response.raise_for_status()

    logging.info("GitHub API is reachable and authentication is successful.")
    logging.info(
        "Logging information for GitHub organization %s.\n%s",
        github_org_name,
        json.dumps(response.json(), indent=4),
    )

    return "OK"
