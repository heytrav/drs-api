disclose = {
    "$schema": "http://drs/disclose.json",
    "definitions": {},
    "id": "http://drs/disclose.json",
    "required": [
        "flag",
        "fields"
    ],
    "properties": {
        "fields": {
            "id": "/properties/fields",
            "items": {
                "enum": [
                    "name",
                    "address",
                    "company",
                    "telephone",
                    "fax",
                    "email"
                ],
                "id": "/properties/fields/items",
                "type": "string"
            },
            "maxItems": 6,
            "minItems": 1,
            "type": "array",
            "uniqueItems": True
        },
        "flag": {
            "enum": [
                1,
                0
            ],
            "id": "/properties/flag",
            "type": "integer"
        }
    },
    "type": "object"
}
