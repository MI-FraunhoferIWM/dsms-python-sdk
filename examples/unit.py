from dsms import DSMS

dsms = DSMS(env="../.env")

item = dsms.search(query="DX56_D_FZ2_WR00_43", allow_fuzzy=False, limit=1)[0]

print(item.custom_properties.SpecimenWidth.convert_to("m"))

print(item.hdf5.Extension.convert_to("m")[:100])

print(item)
