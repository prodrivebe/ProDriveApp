"""Customer endpoint tests."""

from fastapi.testclient import TestClient


def test_dispatcher_can_list_customers(client: TestClient) -> None:
    """Dispatcher can access customer endpoints."""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "dispatcher@example.com",
            "password": "Dispatch123!",
        },
    )
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/customers", headers=headers)

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_admin_can_create_and_get_customer(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can create and read a customer."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    create_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "company_name": "Acme Logistics",
            "vat_number": "NL123456789B01",
            "address": "Harbor Street 10",
            "city": "Rotterdam",
            "country": "NL",
            "email": "info@acme-logistics.example.com",
            "phone": "+31123456789",
            "notes": "Preferred customer",
        },
    )

    assert create_response.status_code == 201
    customer_id = create_response.json()["data"]["id"]

    get_response = client.get(f"/api/v1/customers/{customer_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["company_name"] == "Acme Logistics"


def test_customer_search_filters_results(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Customer list supports search filtering."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Searchable Motors", "city": "Berlin"},
    )
    client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Other Transport", "city": "Paris"},
    )

    response = client.get(
        "/api/v1/customers",
        headers=headers,
        params={"search": "Searchable"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["pagination"]["total"] == 1
    assert body["data"][0]["company_name"] == "Searchable Motors"


def test_admin_can_update_and_delete_customer(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can update and soft delete a customer."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    create_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Delete Me BV", "city": "Amsterdam"},
    )
    customer_id = create_response.json()["data"]["id"]

    update_response = client.put(
        f"/api/v1/customers/{customer_id}",
        headers=headers,
        json={
            "company_name": "Updated Customer BV",
            "city": "Utrecht",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["city"] == "Utrecht"

    delete_response = client.delete(
        f"/api/v1/customers/{customer_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200

    list_response = client.get("/api/v1/customers", headers=headers)
    assert list_response.json()["meta"]["pagination"]["total"] == 0


def test_admin_can_manage_customer_contacts(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can create, update, and delete customer contacts."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Contact Customer GmbH"},
    )
    customer_id = customer_response.json()["data"]["id"]

    create_response = client.post(
        f"/api/v1/customers/{customer_id}/contacts",
        headers=headers,
        json={
            "first_name": "Anna",
            "last_name": "Planner",
            "email": "anna@contact-customer.example.com",
            "is_primary": True,
        },
    )
    assert create_response.status_code == 201
    contact_id = create_response.json()["data"]["id"]

    update_response = client.put(
        f"/api/v1/customers/{customer_id}/contacts/{contact_id}",
        headers=headers,
        json={
            "first_name": "Anna",
            "last_name": "Updated",
            "email": "anna@contact-customer.example.com",
            "job_title": "Logistics Manager",
            "is_primary": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["job_title"] == "Logistics Manager"

    list_response = client.get(
        f"/api/v1/customers/{customer_id}/contacts",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1

    delete_response = client.delete(
        f"/api/v1/customers/{customer_id}/contacts/{contact_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200


def test_only_one_primary_contact_is_kept(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Setting a contact as primary clears other primary contacts."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Primary Contact Ltd"},
    )
    customer_id = customer_response.json()["data"]["id"]

    first_response = client.post(
        f"/api/v1/customers/{customer_id}/contacts",
        headers=headers,
        json={
            "first_name": "First",
            "last_name": "Contact",
            "is_primary": True,
        },
    )
    first_contact_id = first_response.json()["data"]["id"]

    client.post(
        f"/api/v1/customers/{customer_id}/contacts",
        headers=headers,
        json={
            "first_name": "Second",
            "last_name": "Contact",
            "is_primary": True,
        },
    )

    first_contact_response = client.get(
        f"/api/v1/customers/{customer_id}/contacts",
        headers=headers,
    )
    contacts = first_contact_response.json()["data"]
    primary_contacts = [contact for contact in contacts if contact["is_primary"]]
    assert len(primary_contacts) == 1
    assert primary_contacts[0]["id"] != first_contact_id


def test_customer_history_returns_empty_when_no_orders(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Customer history is empty before any orders exist."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "History Customer SA"},
    )
    customer_id = customer_response.json()["data"]["id"]

    response = client.get(
        f"/api/v1/customers/{customer_id}/history",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == []
    assert body["meta"]["pagination"]["total"] == 0
