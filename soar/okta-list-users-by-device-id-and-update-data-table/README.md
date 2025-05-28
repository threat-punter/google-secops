# Example Code for Google SecOps SOAR

## Okta - List Users by Device ID and Update Data Table

These example Google SecOps SOAR job and manager objects do the following:

* Retrieve a list of devices and information on their associated users via Okta's API
* Populate a data table in Google SecOps with metadata about devices and associated users.

Please refer to the following blog post on the Google Cloud Security Community for further details: Link to blog after it's published

To import these artifacts into Google SecOps, add the files and folders in this directory to a ZIP file (excluding this readme file) and [import](https://cloud.google.com/chronicle/docs/soar/respond/ide/building-a-custom-integration#import-integrations) it in Google SecOps under `Response` - `IDE`.