from dsms import DSMS, KItem

dsms = DSMS(host_url="https://stahldigital.materials-data.space", env="../.env")

uuid = "8d6b034e-efb4-427a-a0d3-666e62762cba"
item = dsms[uuid]


item.hdf5.get("Standardkraft").convert_to("kN")

item.custom_properties.content.Projektnummer.convert_to("kPa")
