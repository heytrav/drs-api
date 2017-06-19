non_disclose = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "definitions": {},
    "id": "http://drs.drs/non_disclose.json",
    "items": {
        "enum": [
            "name",
            "company",
            "address",
            "telephone",
            "fax",
            "email"
        ],
        "id": "/items",
        "type": "string"
    },
    "maxItems": 6,
    "minItems": 1,
    "type": "array",
    "uniqueItems": True
}

street = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "definitions": {},
    "id": "http://drs.drs/street.json",
    "items": {
        "id": "/items",
        "type": "string"
    },
    "maxItems": 3,
    "minItems": 1,
    "type": "array"
}


ip_field = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "definitions": {},
    "id": "http://example.com/example.json",
    "properties": {
        "addr": {
            "id": "/properties/addr",
            "items": {
                "id": "/properties/addr/items",
                "anyOf": [
                {
                    "properties": {
                        "ip": {
                            "id": "/properties/addr/items/properties/ip",
                            "type": "string"
                        },
                        "type": {
                            "id": "/properties/addr/items/properties/type",
                            "type": "string"
                        }
                    },
                    "required": [
                        "ip",
                    ],
                    "type": "object"
                },
                    {"type": "string"}

                ]



            },
            "type": "array"
        },
        "name": {
            "id": "/properties/name",
            "type": "string"
        }
    },
    "required": [
        "name"
    ],
    "type": "object"
}

#{
    #"$schema": "http://json-schema.org/draft-04/schema#",
    #"definitions": {
        #"ip_field": {
            #"properties": {
                #"ip": { "type": "string" },
                #"type": {
                    #"type": "string",
                    #"enum": [
                        #"v4",
                        #"v6"
                    #]
                #}
            #},
            #"required": [
                #"ip",
            #],
            #"type": "object"
        #}
    #},
    #"id": "http://example.com/example.json",
    #"properties": {
        #"addr": {
            #"id": "/properties/addr",
            #"items": {
                    #"anyOf": [
                        #{"$ref": "#/definitions/ip_field"},
                        #{"type": "string"}
                    #]
            #},
            #"type": "array"
        #},
        #"name": {
            #"id": "/properties/name",
            #"type": "string"
        #}
    #},
    #"required": [
        #"name"
    #],
    #"type": "object"
#}
