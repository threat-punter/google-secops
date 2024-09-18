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
"""Perform a UDM search in Google SecOps using the Search API endpoint.

API reference: https://cloud.google.com/chronicle/docs/reference/search-api#udmsearch"""

import os
from typing import Mapping, Any

from google.auth.transport import requests


def udm_search(
    http_session: requests.AuthorizedSession, query: str, start_time: str, end_time: str, limit: int = None
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
    """
    url = f"{os.environ['GOOGLE_SECOPS_BACKSTORY_API_BASE_URL']}/events:udmSearch"
    params = {"query": query, "time_range.start_time": start_time, "time_range.end_time": end_time, "limit": limit}

    response = http_session.request(method="GET", url=url, params=params)

    if response.status_code >= 400:
        print(response.text)
        response.raise_for_status()

    return response.json()
