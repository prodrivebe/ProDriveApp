"""Report and search endpoint tests."""

from fastapi.testclient import TestClient


def _create_customer(client: TestClient, headers: dict[str, str], name: str) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": name},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_reports_kpi_dashboard(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can read KPI dashboard report."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers, "Report Customer GmbH")
    client.post(
        "/api/v1/orders",
        headers=headers,
        json={"customer_id": customer_id},
    )

    response = client.get("/api/v1/reports/kpi", headers=headers)
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total_orders"] >= 1
    assert body["total_customers"] >= 1
    assert body["fleet"]["drivers"]["total"] >= 0
    assert body["fleet"]["trucks"]["total"] >= 0
    assert body["fleet"]["trailers"]["total"] >= 0


def test_reports_orders_by_status(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Orders report includes status breakdown."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.get("/api/v1/reports/orders", headers=headers)
    assert response.status_code == 200
    assert "by_status" in response.json()["data"]


def test_global_search_finds_customer(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Global search returns matching customers."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    _create_customer(client, headers, "Searchable Transport BV")

    response = client.get(
        "/api/v1/search",
        headers=headers,
        params={"q": "Searchable"},
    )
    assert response.status_code == 200
    customers = response.json()["data"]["customers"]
    assert len(customers) >= 1


def test_ai_score_order(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """AI order quality endpoint returns a score."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers, "AI Score Customer")
    order_response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"customer_id": customer_id},
    )
    order_id = order_response.json()["data"]["id"]

    response = client.post(
        "/api/v1/ai/score-order",
        headers=headers,
        json={"order_id": order_id},
    )
    assert response.status_code == 200
    assert 0 <= response.json()["data"]["score"] <= 1
