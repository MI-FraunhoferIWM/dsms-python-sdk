"""Example of creating and running apps"""

import time

from dsms import DSMS, AppConfig, KItem

print("\nConnect to DSMS")
dsms = DSMS(env="../.env")

print("\nCreate app specification")
AppConfig(
    name="testapp",
    specification="../../dsms-app-initiator/excel_tensile_test.argo.yaml",
)

print("\nCreate kitem")
item = KItem(
    name="test123",
    ktype_id=dsms.ktypes.Dataset,
    kitem_apps=[
        {
            "executable": "testapp",
            "title": "data2rdf",
            "additional_properties": {
                "triggerUponUpload": True,
                "triggerUponUploadFileExtensions": [".xlsx"],
            },
        }
    ],
)
print("\nCommit KItem")
dsms.commit()

print("\nAdd attachment")
item.attachments = ["../../Desktop/AFZ1-Fz-S1D.xlsx"]


print("\nUpload attachment and trigger app")
dsms.commit()

print(item)

print("\nRun pipeline manually")
job = item.kitem_apps.by_title["data2rdf"].run(
    attachment_name=item.attachments[0].name, set_token=True, set_host_url=True
)

print("\nSee job status")
print(job.status)
print("\n See job logs:")
print(job.logs)

print("\nRun pipeline manually in the background")
job = item.kitem_apps.by_title["data2rdf"].run(
    attachment_name=item.attachments[0].name,
    set_token=True,
    set_host_url=True,
    wait=False,
)

print("\nMonitor job status")
while True:
    time.sleep(1)
    print("\n Current status:")
    print(job.status)
    print("\n Current logs:")
    print(job.logs)
    if job.status.phase != "Running":
        break
