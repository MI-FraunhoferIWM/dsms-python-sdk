import time

from dsms import DSMS

dsms = DSMS(env="../.env")

id = "b24b3720-851a-445f-8028-77f526fc90b9"

kitem = dsms[id]

print("doing it synchronously")
job = kitem.kitem_apps.by_title["Fetch from CKAN"].run(transform=True)
print(job.artifacts)


print("doing it asychronously")
job = kitem.kitem_apps.by_title["Fetch from CKAN"].run(
    transform=True, wait=False
)
while True:
    time.sleep(1)
    print("waiting...")
    if job.status.phase == "Succeeded":
        print("succeeded!")
        break
    print("task not ready yet...")
print(job.artifacts)
