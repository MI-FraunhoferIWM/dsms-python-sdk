import os

from dotenv import load_dotenv

from dsms import DSMS, KItem

# set file paths
env = os.path.join("..", ".env")
file = "tensile_test.txt"

# start session
load_dotenv()
dsms = DSMS()

# find appropiate app
app_name = [
    app.filename
    for app in dsms.apps
    if "csv" in app.filename
    and "tensile" in app.filename
    and "test" in app.filename
]

# configure app
app = {
    "title": "CSV Tensile test RDF Pipeline",
    "description": "Pipeline for CSV Tensile test data into RDF Graph",
    "executable": app_name.pop(),
    "additional_properties": {
        "triggerUponUpload": True,
        "triggerUponUploadFileExtensions": ["." + file.split(".")[-1]],
    },
}

annotation = {
    "iri": "https://w3id.org/steel/ProcessOntology/TensileTest",
    "name": "Tensile test",
    "namespace": "https://w3id.org/steel/ProcessOntology",
}

# make kitem
item = KItem(
    name="DX56_A_FZ2_WR00_01_b",
    ktype_id=dsms.ktypes.Dataset,
    kitem_apps=[app],
    annotations=[annotation],
)

# commit the item
dsms.commit()

# upload attachment
item.attachments.append({"name": file})

# commit changes
dsms.commit()

# see result
print(item)
