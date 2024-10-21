import json
from dsms import DSMS, KType
dsms = DSMS(env=".env")

# for ktype in dsms.ktypes:
#     print(ktype)
    # if ktype.webform is not None:
    #     print(ktype.webform)
webform = {
  "semantics_enabled": "true",
  "sections": [
    {
      "id": "id167cc4c989cd8",
      "name": "testsection",
      "inputs": [
        {
          "id": "id74979e625fa1a",
          "label": "test box",
          "widget": "Checkbox",
          "defaultValue": "",
          "value": "true",
          "check": "null",
          "error": "null",
          "feedback": "null",
          "hint": "a",
          "measurementUnit": "Pa",
          "mapping": "null",
          "knowledgeType": "null",
          "knowledgeServiceUrl": "null",
          "vocabularyServiceUrl": "null",
          "hidden": "false",
          "ignore": "false",
          "extra": {}
        }
      ],
      "hidden": "false"
    }
  ]
}
ktype = KType( 
        id='testabc',
        name='ABC',
        webform=webform
)
dsms.commit()
