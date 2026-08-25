"""
Etape 1 : recuperer la liste des FILMS UNIQUES actuellement a l'affiche a Bruxelles (Cineville)
"""
import requests
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

FUSEAU_BRUXELLES = ZoneInfo("Europe/Brussels")

API_URL = "https://api.cinevillepass.be/events/search"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json; charset=UTF-8",
    "locale": "fr-BE",
    "origin": "https://cinevillepass.be",
    "referer": "https://cinevillepass.be/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

VILLE = "brussels"
JOURS_A_VENIR = 7


def fetch_all_events():
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=JOURS_A_VENIR)

    all_events = []
    after_cursor = None

    while True:
        body = {
            "productionId": {"isNull": False},
            "startDate": {
                "gte": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "lt": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            },
            "venue": {"collection": {"cities": {"in": [VILLE]}}},
            "page": {"limit": 100},
            "isHidden": {"eq": False},
            "embed": {"production": True, "venue": True},
            "sort": {"startDate": "asc"},
        }

        url = API_URL
        if after_cursor:
            url = f"{API_URL}?page[limit]=100&page[after]={after_cursor}"

        response = requests.post(url, headers=HEADERS, json=body)
        response.raise_for_status()
        data = response.json()

        events = data.get("_embedded", {}).get("events", [])
        all_events.extend(events)

        next_link = data.get("_links", {}).get("next", {}).get("href")
        if not next_link:
            break
        if "page[after]=" in next_link:
            after_cursor = next_link.split("page[after]=")[1].split("&")[0]
        else:
            break
        if len(all_events) >= data.get("totalCount", 0):
            break

    return all_events


def safe_get(d, *keys):
    """Recupere une valeur imbriquee en toute securite, meme si un niveau intermediaire est None."""
    for key in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(key)
    return d


def build_unique_films(events):
    films = {}

    for ev in events:
        production = ev.get("_embedded", {}).get("production") or {}
        venue = ev.get("_embedded", {}).get("venue") or {}
        prod_id = ev.get("productionId")
        if not prod_id or not production:
            continue

        start_iso = ev.get("startDate")
        start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00")) if start_iso else None

        if prod_id not in films:
            attrs = production.get("attributes") or {}
            loc_attrs = production.get("localizableAttributes") or {}

            films[prod_id] = {
                "titre": production.get("title"),
                "annee": attrs.get("releaseYear"),
                "duree_minutes": attrs.get("duration"),
                "realisateurs": attrs.get("directors"),
                "synopsis": loc_attrs.get("description"),
                "affiche_url": safe_get(production, "assets", "poster", "url") or safe_get(production, "assets", "cover", "url"),
                "seances": [],
            }

        films[prod_id]["seances"].append({
            "heure": start_dt.astimezone(FUSEAU_BRUXELLES).strftime("%d/%m %H:%M") if start_dt else None,
            "cinema": venue.get("name"),
        })

    return list(films.values())


if __name__ == "__main__":
    print("Récupération des séances en cours...")
    raw_events = fetch_all_events()
    print(f"Total séances récupérées : {len(raw_events)}")

    films = build_unique_films(raw_events)
    films.sort(key=lambda f: f["titre"] or "")

    with open("films_bruxelles.json", "w", encoding="utf-8") as f:
        json.dump(films, f, ensure_ascii=False, indent=2)

    print(f"\n{len(films)} film(s) unique(s) à l'affiche à Bruxelles\n")
    for f in films:
        nb_seances = len(f["seances"])
        print(f"- {f['titre']} ({f['annee']}) — {nb_seances} séance(s)")

    print("\nSauvegardé dans films_bruxelles.json")
