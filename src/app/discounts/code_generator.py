import uuid


def generate_discount_code() -> str:
    """Returns new 10 char discount code id good enough for demo purposes."""
    id_1 = str(uuid.uuid4()).upper()
    id_2 = str(uuid.uuid4()).upper()
    return id_1[:8] + id_2[:2]
