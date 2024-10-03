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
"""Perform a UDM search in Google SecOps.

API reference: https://cloud.google.com/chronicle/docs/reference/rest/v1alpha/projects.locations.instances/udmSearch"""

import os
import time
from typing import Mapping, Any

from google.auth.transport import requests


def udm_search(
    http_session: requests.AuthorizedSession,
    query: str,
    start_time: str,
    end_time: str,
    limit: int = None,
    max_retries: int = 3,
) -> Mapping[str, Any]:
    """Perform a UDM search in Google SecOps.

    API reference: https://cloud.google.com/chronicle/docs/reference/rest/v1alpha/projects.locations.instances/udmSearch

    Args:
        http_session: Authorized session for HTTP requests.
        query: UDM query used to search.
        start_time: Start time of the time range to search for.
            A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional
            digits. Examples: "2014-10-02T15:01:23Z" and "2014-10-02T15:01:23.045123456Z".
        end_time: End time of the time range to search for.
            A timestamp in RFC3339 UTC "Zulu" format, with nanosecond resolution and up to nine fractional
            digits. Examples: "2014-10-02T15:01:23Z" and "2014-10-02T15:01:23.045123456Z".
        limit:
            Maximum number of results to be returned for the query. Anything over 10000 will be coerced to 10000.
        max_retries (optional): Maximum number of times to retry HTTP request if certain response codes are returned.
            For example: HTTP response status code 429 (Too Many Requests)
    """
    url = f"{os.environ['GOOGLE_SECOPS_API_BASE_URL']}/{os.environ['GOOGLE_SECOPS_INSTANCE']}/:udmSearch"
    params = {"query": query, "time_range.start_time": start_time, "time_range.end_time": end_time, "limit": limit}
    response = None

    for _ in range(max_retries + 1):
        response = http_session.request(method="GET", url=url, params=params)

        if response.status_code != 429:
            break
        print(response.text)
        print("API rate limit exceeded. Sleeping for 60s before retrying")
        time.sleep(60)

    response.raise_for_status()

    return response.json()
