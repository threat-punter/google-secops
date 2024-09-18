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
"""Search detections in Google SecOps.

API reference: https://cloud.google.com/chronicle/docs/reference/rest/v1alpha/projects.locations.instances.legacy/legacySearchDetections
"""

import os
from typing import Tuple, List, Dict

from google.auth.transport import requests


def search_detections(
    http_session: requests.AuthorizedSession,
    rule_id: str,
    alert_state: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    list_basis: str | None = None,
    page_size: int | None = None,
    page_token: str | None = None,
) -> Tuple[List[Dict], str]:
    """Search detections in Google SecOps.

    Args:
        http_session: Authorized session for HTTP requests.
        rule_id: The specific rule revision to search detections for.
            There are four acceptable formats:
            - {rule_id} retrieves detections for the latest revision of the Rule with
              rule ID |rule_id| - {rule_id}@{revision_id} retrieves detections for the Rule revision with
              rule ID |rule_id| and revision ID |revision_id|.
            - {rule_id}@{wildcard} retrieves detections for all revisions of the Rule with rule ID |rule_id|.
            - {wildcard} retrieves detections for all revisions of all Rules.
        alert_state (optional): Filter which detections are returned by their AlertState.
            API reference: https://cloud.google.com/chronicle/docs/reference/rest/v1alpha/SecurityResult#AlertState
        start_time (optional): The time to start search detections from.
            A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional
            digits. Examples: "2014-10-02T15:01:23Z" and "2014-10-02T15:01:23.045123456Z".
        end_time (optional): The time to end searching detections to.
            A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional
            digits. Examples: "2014-10-02T15:01:23Z" and "2014-10-02T15:01:23.045123456Z".
        list_basis (optional): Basis for determining whether to apply start_time and end_time filters for detection
            time or creation time of the detection.
            API reference: https://cloud.google.com/chronicle/docs/reference/rest/v1alpha/projects.locations.instances.legacy/legacySearchDetections#ListBasis
        page_size (optional): Maximum number of detections to return.
        page_token (optional): A page token, received from a previous LegacySearchDetections call. Provide this to
            retrieve the subsequent page.
            When paginating, all other parameters provided to LegacySearchDetections must match the call that provided
            the page token.

    Returns:
        List of detections corresponding to the provided rule ID and a page token for the next page of rules, if there
        are any.

    Raises:
        requests.exceptions.HTTPError: HTTP request resulted in an error (response.status_code >= 400).
    """
    url = f"{os.environ['GOOGLE_SECOPS_API_BASE_URL']}/{os.environ['GOOGLE_SECOPS_INSTANCE']}/legacy:legacySearchDetections"
    params = {
        "rule_id": rule_id,
        "alert_state": alert_state,
        "start_time": start_time,
        "end_time": end_time,
        "list_basis": list_basis,
        "page_size": page_size,
        "page_token": page_token,
    }

    response = http_session.request(method="GET", url=url, params=params)

    if response.status_code >= 400:
        print(response.text)
        response.raise_for_status()

    response_json = response.json()

    return response_json.get("detections"), response_json.get("nextPageToken")
