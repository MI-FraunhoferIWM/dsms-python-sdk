from dsms import DSMS, KItem, KType

dsms = DSMS(env=".env")

dsms.kitems
# type = dsms.context.ktypes()
# type = KType( 
#         id='testtype20',
#         name='newtype15'
# )
# dsms.commit()
# for i in range(15):
#         if(i!=0):
#                 ktype=dsms.context.ktypes['testtype'+str(i+1)]
#                 print(ktype)
#                 del dsms[ktype]
#                 dsms.commit()
for ktype in dsms.context.ktypes:
        print(ktype)