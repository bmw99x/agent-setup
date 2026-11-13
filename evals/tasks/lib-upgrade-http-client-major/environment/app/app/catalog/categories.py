from app.http import supplier_client


def fetch_categories() -> list[dict]:
    response = supplier_client().get("/categories")
    return response.json()["items"]
