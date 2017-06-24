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
    "minItems": 0,
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

ip_addr = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "definitions": {},
    "id": "http://example.com/example.json",
    "items": {
        "id": "/items",
        "anyOf": [
            {
                "properties": {
                    "ip": {
                        "id": "/items/properties/ip",
                        "type": "string"
                    },
                    "type": {
                        "id": "/items/properties/type",
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
    "type": "array",
    "minItems": 1
}

nameserver = {
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
            "type": "array",
            "minItems": 1
        },
        "host": {
            "id": "/properties/host",
            "type": "string"
        }
    },
    "required": [
        "host",
        "addr"
    ],
    "type": "object"
}
