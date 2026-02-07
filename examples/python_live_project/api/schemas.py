"""
JSON Schema definitions for API response validation.
"""

USER_SCHEMA = {
    "type": "object",
    "required": ["id", "email", "name"],
    "properties": {
        "id": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "name": {"type": "string"},
        "phone": {"type": "string"},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
        "address": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"},
                "state": {"type": "string"},
                "zip": {"type": "string"},
                "country": {"type": "string"}
            }
        }
    }
}

PRODUCT_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "price"],
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "price": {"type": "number", "minimum": 0},
        "category": {"type": "string"},
        "stock": {"type": "integer", "minimum": 0},
        "sku": {"type": "string"},
        "images": {
            "type": "array",
            "items": {"type": "string"}
        },
        "rating": {"type": "number", "minimum": 0, "maximum": 5},
        "reviews_count": {"type": "integer"}
    }
}

ORDER_SCHEMA = {
    "type": "object",
    "required": ["id", "user_id", "items", "status", "total"],
    "properties": {
        "id": {"type": "string"},
        "user_id": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["product_id", "quantity", "price"],
                "properties": {
                    "product_id": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "price": {"type": "number"}
                }
            }
        },
        "status": {"type": "string", "enum": ["pending", "confirmed", "shipped", "delivered", "cancelled"]},
        "total": {"type": "number"},
        "shipping_address": {"type": "object"},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"}
    }
}

PRODUCT_LIST_SCHEMA = {
    "type": "object",
    "required": ["products", "total", "page"],
    "properties": {
        "products": {
            "type": "array",
            "items": PRODUCT_SCHEMA
        },
        "total": {"type": "integer"},
        "page": {"type": "integer"},
        "per_page": {"type": "integer"}
    }
}
