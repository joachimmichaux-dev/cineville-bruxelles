"""
Complement : recupere l'affiche manquante depuis AlloCine (og:image)
pour les films qui n'ont pas d'affiche_url venant de Cineville.
Ne retraite que les films avec allocine_id deja connu (rapide, pas de nouvelle recherche).
"""
import json
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def recuperer_affiche(page, allocine_id):
    url = f"https://www.allocine.fr/film/fichefilm-{allocine_id}/"
    page.goto(url)
    page.wait_for_timeout(1000)

    soup = BeautifulSoup(page.content(), "html.parser")
    meta = soup.find("meta", property="og:image")
    if meta:
        return meta.get("content")
    return None


if __name__ == "__main__":
    with open("films_avec_allocine.json", encoding="utf-8") as f:
        films = json.load(f)

    a_completer = [
        f for f in films
        if not f.get("affiche_url") and f.get("allocine") and f["allocine"].get("allocine_id")
    ]
    print(f"{len(a_completer)} film(s) sans affiche à compléter\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, film in enumerate(a_completer):
            allocine_id = film["allocine"]["allocine_id"]
            print(f"[{i+1}/{len(a_completer)}] {film['titre']}...")

            affiche = recuperer_affiche(page, allocine_id)
            if affiche:
                film["affiche_url"] = affiche
                print(f"   -> Affiche trouvée")
            else:
                print(f"   -> Aucune affiche trouvée")

            time.sleep(0.3)

        browser.close()

    with open("films_avec_allocine.json", "w", encoding="utf-8") as f:
        json.dump(films, f, ensure_ascii=False, indent=2)

    print("\nMis à jour dans films_avec_allocine.json")