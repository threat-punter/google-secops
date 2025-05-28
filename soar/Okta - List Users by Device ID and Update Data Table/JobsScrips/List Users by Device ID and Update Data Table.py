import json
import logging

import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import service_account

from SiemplifyJob import SiemplifyJob
from DataTableManager import DataTableManager


INTEGRATION_NAME = "OKTA"
SCRIPT_NAME = "Okta - List Users by Device ID and Update Data Table"

SIEMPLIFY = SiemplifyJob()
OKTA_API_TOKEN = SIEMPLIFY.extract_job_param(param_name="Okta API Token")
OKTA_DOMAIN = SIEMPLIFY.extract_job_param(param_name="Okta Domain", print_value=True)
DATA_TABLE_NAME = SIEMPLIFY.extract_job_param("Data Table Name", print_value=True)
SERVICE_ACCOUNT_KEY = json.loads(SIEMPLIFY.extract_job_param("Service Account Key"))
GOOGLE_CLOUD_PROJECT_ID = SIEMPLIFY.extract_job_param("Google Cloud Project ID", print_value=True)
GOOGLE_CLOUD_PROJECT_REGION = SIEMPLIFY.extract_job_param("Google Cloud Project Region", print_value=True)
GOOGLE_SECOPS_CUSTOMER_ID = SIEMPLIFY.extract_job_param("Google SecOps Customer ID", print_value=True)
GOOGLE_SECOPS_API_BASE_URL = f"https://{GOOGLE_CLOUD_PROJECT_REGION}-chronicle.googleapis.com/v1alpha"
AUTHORIZATION_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
DATA_TABLE_MANAGER = DataTableManager(google_secops_api_base_url=GOOGLE_SECOPS_API_BASE_URL)

def list_device_ids(okta_domain: str, okta_api_token: str) -> list[str | None]:
    """List all device IDs in an Okta environment."""
    url = f"https://{okta_domain}/api/v1/devices"
    headers = {"Authorization": f"SSWS {okta_api_token}"}
    response = None

    next_page = 1
    retrieved_devices = []

    while next_page:
        response = requests.get(url, headers=headers)

        if response.status_code >= 400:
            SIEMPLIFY.LOGGER.warn(response.text)

        if response.status_code == 429:
            SIEMPLIFY.LOGGER.warn("API rate limit exceeded. Sleeping for 60s before retrying")
            time.sleep(60)

        response.raise_for_status()

        devices = response.json()
        retrieved_devices.extend(devices)
        SIEMPLIFY.LOGGER.info(f"Retrieved {len(devices)} devices")

        links = response.links

        if links.get("next"):
            next_page = links["next"]["url"]
            url = next_page
        else:
            next_page = None

    SIEMPLIFY.LOGGER.info(f"Retrieved a total of {len(retrieved_devices)} devices")

    device_ids = []

    for device in retrieved_devices:
        device_ids.append(device["id"])

    return device_ids


def list_device_id_users(okta_domain: str, okta_api_token: str, device_id: str) -> list[str]:
    """List all users associated with a device ID."""
    url = f"https://{okta_domain}/api/v1/devices/{device_id}/users"
    headers = {"Authorization": f"SSWS {okta_api_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code >= 400:
        SIEMPLIFY.LOGGER.warn(response.text)

    if response.status_code == 429:
        SIEMPLIFY.LOGGER.warn("API rate limit exceeded. Sleeping for 60s before retrying")
        time.sleep(60)

    response.raise_for_status()

    users = response.json()
    SIEMPLIFY.LOGGER.info(f"Retrieved {len(users)} users for device ID {device_id}")

    return users


def main():
    SIEMPLIFY.script_name = SCRIPT_NAME

    try:
        credentials = service_account.Credentials.from_service_account_info(
            SERVICE_ACCOUNT_KEY,
            scopes=AUTHORIZATION_SCOPES,
        )
        http_session = google_requests.AuthorizedSession(credentials)

        SIEMPLIFY.LOGGER.info(f"Attempting to retrieve all device IDs for Okta organization {OKTA_DOMAIN}")
        device_ids = list_device_ids(okta_domain=OKTA_DOMAIN, okta_api_token=OKTA_API_TOKEN)

        if not device_ids:
            SIEMPLIFY.LOGGER.info("No devices found")
            return

        device_ids_and_users = []

        SIEMPLIFY.LOGGER.info("Attempting to list users for each device ID")
        for device_id in device_ids:
            device_id_users = list_device_id_users(okta_domain=OKTA_DOMAIN, okta_api_token=OKTA_API_TOKEN, device_id=device_id)
            for user in device_id_users:
                device_ids_and_users.append(
                    [device_id, user["user"]["profile"]["login"], user["user"]["id"]]
                )

        SIEMPLIFY.LOGGER.info(f"Attempting to write device and user metadata ({len(device_ids_and_users)} rows) to data table {DATA_TABLE_NAME}")
        data_table_resource_name = f"projects/{GOOGLE_CLOUD_PROJECT_ID}/locations/{GOOGLE_CLOUD_PROJECT_REGION}/instances/{GOOGLE_SECOPS_CUSTOMER_ID}/dataTables/{DATA_TABLE_NAME}"
        DATA_TABLE_MANAGER.update_remote_data_table_rows(
            http_session = http_session,
            data_table_name = DATA_TABLE_NAME,
            data_table_resource_name = data_table_resource_name,
            row_values = device_ids_and_users
        )
        SIEMPLIFY.LOGGER.info(f"Successfully wrote device and user metadata ({len(device_ids_and_users)} rows) to data table {DATA_TABLE_NAME}")

    except Exception as e:
        SIEMPLIFY.LOGGER.error(f"General error performing Job {SCRIPT_NAME}")
        SIEMPLIFY.LOGGER.exception(e)
        raise

    SIEMPLIFY.end_script()


if __name__ == "__main__":
    main()