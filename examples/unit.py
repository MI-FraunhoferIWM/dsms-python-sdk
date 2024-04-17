from dsms import DSMS

dsms = DSMS(env="../.env")

item = dsms.search(query="AFZ1-Fz-S1Q", allow_fuzzy=False, limit=1)[0].hit

print(item)

print(item.custom_properties.OriginalWidth.convert_to("m"))

print(item.hdf5.PercentageExtension.get()[:100])
