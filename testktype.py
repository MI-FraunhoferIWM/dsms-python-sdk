from dsms import DSMS, KItem, KType

dsms = DSMS(env=".env")

# type = dsms.context.ktypes()
type = KType( 
        id='batch',
        name='Batch'
)
dsms.commit()
print(type)
# for i in range(15):
#         if(i!=0):
#                 ktype=dsms.context.ktypes['testtype'+str(i+1)]
#                 print(ktype)
#                 del dsms[ktype]
#                 dsms.commit()
# for ktype in dsms.context.ktypes:
#         print(ktype)