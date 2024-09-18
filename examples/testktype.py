from dsms import DSMS, KItem, KType

dsms = DSMS(env="../.env")

dsms.kitems
for ktype in dsms.ktypes:
    print(ktype)