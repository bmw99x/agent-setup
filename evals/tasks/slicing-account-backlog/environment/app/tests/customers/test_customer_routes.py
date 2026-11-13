from app.customers.models import Customer


async def test_read_me_returns_own_profile(client, session):
    """A customer reads their own profile."""
    customer = Customer(email="ana@example.com", full_name="Ana Silva")
    session.add(customer)
    await session.commit()

    response = await client.get("/customers/me", headers={"X-Customer-Id": str(customer.id)})

    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"


async def test_read_customer_requires_staff(client):
    """Customers cannot read other customers by id."""
    response = await client.get("/customers/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 403
