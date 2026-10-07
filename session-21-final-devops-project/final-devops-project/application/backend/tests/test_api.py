def new_ticket(client, **extra):
    body = {"title": "VPN not connecting", "priority": "HIGH", "category": "NETWORK", "requester": "Shubham"}
    body.update(extra)
    return client.post("/api/tickets", json=body)


def test_health(client):
    assert client.get("/health").json() == {"status": "UP"}


def test_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "HelpDesk API"


def test_create_ticket(client):
    response = new_ticket(client)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "VPN not connecting"
    assert data["status"] == "OPEN"
    assert data["id"] > 0


def test_create_ticket_validation_error(client):
    # empty title and unknown priority must be rejected
    assert client.post("/api/tickets", json={"title": ""}).status_code == 422
    assert client.post("/api/tickets", json={"title": "x", "priority": "URGENT"}).status_code == 422


def test_list_and_get_ticket(client):
    ticket_id = new_ticket(client).json()["id"]
    new_ticket(client, title="Laptop screen broken", category="HARDWARE")
    tickets = client.get("/api/tickets").json()
    assert len(tickets) == 2
    assert client.get(f"/api/tickets/{ticket_id}").json()["title"] == "VPN not connecting"


def test_update_ticket(client):
    ticket_id = new_ticket(client).json()["id"]
    response = client.put(f"/api/tickets/{ticket_id}", json={"status": "RESOLVED"})
    assert response.status_code == 200
    assert response.json()["status"] == "RESOLVED"


def test_delete_ticket(client):
    ticket_id = new_ticket(client).json()["id"]
    assert client.delete(f"/api/tickets/{ticket_id}").status_code == 204
    assert client.get(f"/api/tickets/{ticket_id}").status_code == 404


def test_stats(client):
    new_ticket(client)
    second = new_ticket(client, title="Need Jira access", category="ACCESS").json()["id"]
    client.put(f"/api/tickets/{second}", json={"status": "IN_PROGRESS"})
    assert client.get("/api/tickets/stats").json() == {"total": 2, "open": 1, "inProgress": 1, "resolved": 0}


def test_metrics_endpoint(client):
    client.get("/api/tickets")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
