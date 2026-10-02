import pytest

from seed import seed


@pytest.fixture
def seeded(db):
    return seed(db)


def test_seed_counts_and_idempotent(db, seeded):
    assert seeded["destinations"] >= 30 and seeded["hotels"] >= 100 and seeded["places"] >= 150
    assert seed(db) == {"destinations": 0, "places": 0, "hotels": 0}


def test_list_and_filter(client, seeded):
    r = client.get("/api/destinations", params={"page_size": 5})
    body = r.json()
    assert r.status_code == 200 and len(body["items"]) == 5 and body["total"] >= 30
    pops = [d["popularity_score"] for d in body["items"]]
    assert pops == sorted(pops, reverse=True)

    mountains = client.get("/api/destinations", params={"category": "mountain", "page_size": 50}).json()
    assert mountains["total"] >= 4 and all(d["category"] == "mountain" for d in mountains["items"])
    assert client.get("/api/destinations", params={"category": "moon"}).status_code == 422


def test_search_matches_state_tags_and_escapes_wildcards(client, seeded):
    names = {d["name"] for d in client.get("/api/destinations/search", params={"q": "kerala"}).json()["items"]}
    assert {"Munnar", "Alleppey", "Kochi"} <= names
    tagged = client.get("/api/destinations/search", params={"q": "tiger-safari"}).json()["items"]
    assert {d["name"] for d in tagged} == {"Ranthambore", "Jim Corbett"}
    assert client.get("/api/destinations/search", params={"q": "%"}).json()["total"] == 0


def test_detail_and_hotels(client, seeded):
    dest = client.get("/api/destinations/search", params={"q": "Manali"}).json()["items"][0]
    detail = client.get(f"/api/destinations/{dest['id']}").json()
    assert detail["attraction_count"] >= 3 and detail["restaurant_count"] >= 1 and detail["hotel_count"] == 5

    hotels = client.get(f"/api/hotels/{dest['id']}").json()
    assert hotels["source"] == "sample" and "not real" in hotels["note"]
    prices = [h["price_per_night"] for h in hotels["items"]]
    assert prices == sorted(prices)
    budget = client.get(f"/api/hotels/{dest['id']}", params={"tier": "budget"}).json()["items"]
    assert len(budget) == 1 and budget[0]["tier"] == "budget"


def test_missing_destination_404(client, seeded):
    assert client.get("/api/destinations/99999").status_code == 404
    assert client.get("/api/hotels/99999").status_code == 404
