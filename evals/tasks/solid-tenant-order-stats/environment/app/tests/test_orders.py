def test_list_orders_only_returns_the_calling_tenants_orders(client, seed_orders):
    seed_orders("acme", ("paid", 1000), ("pending", 500))
    seed_orders("globex", ("shipped", 700))

    response = client.get("/orders", headers={"X-Tenant": "globex"})

    assert response.status_code == 200
    assert [order["total_cents"] for order in response.json()] == [700]


def test_list_orders_filters_by_status(client, seed_orders):
    seed_orders("acme", ("paid", 1000), ("pending", 500))

    response = client.get("/orders", params={"status": "pending"}, headers={"X-Tenant": "acme"})

    assert [order["total_cents"] for order in response.json()] == [500]


def test_unknown_tenant_returns_404(client, tenant_dir):
    assert client.get("/orders", headers={"X-Tenant": "nobody"}).status_code == 404


def test_missing_tenant_header_returns_400(client):
    assert client.get("/orders").status_code == 400
