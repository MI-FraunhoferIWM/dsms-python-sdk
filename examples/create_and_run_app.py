"""Example of creating and running apps"""

import time

from dsms import DSMS, AppConfig, KItem

print("\nConnect to DSMS")
dsms = DSMS(env="../.env")

configname = "testapp2"
kitem_name = "test item"

data = """A,B,C
1.2,1.3,1.5
1.7,1.8,1.9
2.0,2.1,2.3
2.5,2.6,2.8
3.0,3.2,3.4
3.6,3.7,3.9
4.1,4.3,4.4
4.7,4.8,5.0
5.2,5.3,5.5
5.8,6.0,6.1
"""

extension = ".csv"

parameters = [
    {"name": "parser", "value": "csv"},
    {"name": "time_series_header_length", "value": 1},
    {"name": "metadata_length", "value": 0},
    {"name": "metadata_sep", "value": ","},
    {"name": "time_series_sep", "value": ","},
    {
        "name": "mapping",
        "value": """
            [
                {
                    "key": "A",
                    "iri": "https://w3id.org/steel/ProcessOntology/TestTime",
                    "unit": "s"
                },
                {
                    "key": "B",
                    "iri": "https://w3id.org/steel/ProcessOntology/StandardForce",
                    "unit": "kN"
                },
                {
                    "key": "C",
                    "iri": "https://w3id.org/steel/ProcessOntology/AbsoluteCrossheadTravel",
                    "unit": "mm"
                }
            ]
            """,
    },
]

specification = {
    "apiVersion": "argoproj.io/v1alpha1",
    "kind": "Workflow",
    "metadata": {"generateName": "data2rdf-"},
    "spec": {
        "entrypoint": "execute_pipeline",
        "workflowTemplateRef": {"name": "dsms-data2rdf"},
        "arguments": {"parameters": parameters},
    },
}

print("\nCreate app specification")
appspec = AppConfig(
    name=configname,
    specification=specification,  # this can also be a file path instead of a dict
)

print("\nCreate kitem")
item = KItem(
    name=kitem_name,
    ktype_id=dsms.ktypes.Dataset,
    kitem_apps=[
        {
            "executable": appspec.name,
            "title": "data2rdf",
            "additional_properties": {
                "triggerUponUpload": True,
                "triggerUponUploadFileExtensions": [extension],
            },
        }
    ],
    avatar={"include_qr": True},
)

print("\nCommit KItem")
dsms.commit()

print("\nAdd attachment")
# here we are setting the content directly,
# but `item.attachments` can also be a list with a filepath
# e.g. item.attachments = ["path/to/my/file.csv"]
item.attachments = [{"name": "dummy_data.csv", "content": data}]

print(item)

print("\nUpload attachment and trigger app")
dsms.commit()

print("\nGet dataframe")
if not item.dataframe:
    time.sleep(5)
    item.refresh()
print(item.dataframe.StandardForce.convert_to("N"))


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

print("\nGet dataframe")
print(item.dataframe.StandardForce.convert_to("N"))

print("\nMonitor job status")
while True:
    time.sleep(1)
    print("\n Current status:")
    print(job.status)
    print("\n Current logs:")
    print(job.logs)
    if job.status.phase != "Running":
        break

item.refresh()

print(item.url)

print("\nGet dataframe")
print(item.dataframe.StandardForce.convert_to("N"))

print("\nCleanup")
del dsms[item]
del dsms[appspec]
