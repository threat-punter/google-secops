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
"""This Cloud Run function validates that a GitHub Enterprise health check rule in Google SecOps has generated a recent detection and alert."""

import datetime
import json
import logging
import os

# Import the Google Cloud Logging client library (https://cloud.google.com/logging/docs/setup/python#view_the_logs)
import google.cloud.logging

from secops_api import secops_auth
from secops_api.detection_engine.search_detections import search_detections
from secops_api.search.search_rules_alerts import search_rules_alerts
from common import datetime_converter

client = google.cloud.logging.Client()  # Instantiate the logging client
# Retrieve a Cloud Logging handler based on the environment you're running in and integrates the handler with the
# Python logging module. By default this captures all logs at INFO level and higher
client.setup_logging()

# Initialize an authorized HTTP session with Google SecOps
HTTP_SESSION = secops_auth.initialize_http_session(
    google_secops_api_credentials=json.loads(os.environ["GOOGLE_SECOPS_API_CREDENTIALS"]),
    scopes=json.loads(os.environ["GOOGLE_SECOPS_AUTHORIZATION_SCOPES"]).get("GOOGLE_SECOPS_API"),
)

# Rule ID for the GitHub rule that we're triggering regularly via a separate health check job (Cloud Run function)
RULE_ID = os.environ["GITHUB_HEALTH_CHECK_RULE_ID"]

# Generate start & end times that will be used to search for detections and alerts from the rule
# Convert time to string format %Y-%m-%dT%H:%M:%SZ for UDM search query
CURRENT_TIME = datetime.datetime.now()
END_TIME = datetime_converter.strftime(CURRENT_TIME)
START_TIME = datetime_converter.strftime(
    CURRENT_TIME - datetime.timedelta(hours=int(os.environ["SEARCH_TIME_WINDOW_HOURS"]))
)


def validate_detection_generation():
    """Validate that the GitHub Enterprise rule in Google SecOps generated a recent detection."""
    raw_detections = []
    next_page_token = None

    logging.info(
        "Searching for detections for rule ID %s with start time %s and end time %s", RULE_ID, START_TIME, END_TIME
    )

    while True:
        retrieved_detections, next_page_token = search_detections(
            http_session=HTTP_SESSION,
            rule_id=RULE_ID,
            start_time=START_TIME,
            end_time=END_TIME,
            list_basis="CREATED_TIME",
            page_token=next_page_token,
        )

        if retrieved_detections is None:
            logging.error(
                "No detections found for rule ID %s between %s and %s. Check data pipeline and rule for issues.",
                RULE_ID,
                START_TIME,
                END_TIME,
            )
            raise Exception(
                f"No detections found for rule ID {RULE_ID} between {START_TIME} and {END_TIME}. Check data pipeline and rule for issues."
            )

        else:
            logging.info("Retrieved %s detections for rule ID %s", len(retrieved_detections), RULE_ID)
            raw_detections.extend(retrieved_detections)

        if next_page_token:
            logging.info(
                "Attempting to retrieve detections for rule ID %s with page token %s", RULE_ID, next_page_token
            )
        else:
            break  # Break if there are no more pages of detections to retrieve

    logging.info("Retrieved a total of %s detections for rule ID %s", len(raw_detections), RULE_ID)


def validate_alert_generation():
    """Validate that the GitHub Enterprise rule in Google SecOps generated a recent alert."""
    logging.info("Searching for alerts generated by rules with start time %s and end time %s", START_TIME, END_TIME)

    retrieved_alerts = search_rules_alerts(http_session=HTTP_SESSION, start_time=START_TIME, end_time=END_TIME)

    if not retrieved_alerts:
        logging.error("No alerts found for any rules between %s and %s", START_TIME, END_TIME)
        raise Exception(
            f"No alerts found for any rules between {START_TIME} and {END_TIME}. Check data pipeline and rule for issues."
        )

    relevant_alerts = []

    for alert in retrieved_alerts["ruleAlerts"]:
        if alert["ruleMetadata"]["ruleId"] == RULE_ID:
            relevant_alerts.append(alert)

    if len(relevant_alerts) == 0:
        logging.error("No alerts found for rule ID %s between %s and %s", RULE_ID, START_TIME, END_TIME)
        raise Exception(
            f"No alerts found for rule ID {RULE_ID} between {START_TIME} and {END_TIME}. Check data pipeline and rule for issues."
        )

    else:
        logging.info(
            "Retrieved %s alerts for rule ID %s between %s and %s", len(relevant_alerts), RULE_ID, START_TIME, END_TIME
        )


def main(payload):
    """Entry point for Cloud Run function."""
    validate_detection_generation()
    validate_alert_generation()
    return "OK"
