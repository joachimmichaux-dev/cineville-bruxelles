"""
Etape 2 : pour chaque film Cineville, chercher sa fiche AlloCine
et recuperer :
- les critiques presse (note moyenne + notes/citations par titre de presse)
- la note moyenne spectateurs

Utilise "corrections_titres.json" si present : un dictionnaire
{"Titre Cineville": "Titre a chercher sur AlloCine"} pour les cas ou
la recherche automatique ne trouve pas le bon film (ex: titres en VO).
"""
import json
import os
import re
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def charger_corrections():
    if os.path.exists("corrections_titres.json"):
        with open("corrections_titres.json", encoding="utf-8") as f:
            return json.load(f)
    return {}


def rechercher_film_allocine(page, titre):
    url = "https://www.allocine.fr/rechercher/?q=" + titre.replace(" ", "+")
    page.goto(url)
    page.wait_for_timeout(1500)

    soup = BeautifulSoup(page.content(), "html.parser")
    section = soup.find("section", class_="movies-results")
    if not section:
        return None

    items = section.find_all("li", class_="mdl")
    if not items:
        return None

    link = items[0].select_one(".meta-title-link")
    if not link:
        return None

    href = link.get("href", "")
    match = re.search(r"cfilm=(\d+)|fichefilm-(\d+)", href)
    if not match:
        return None

    return match.group(1) or match.group(2)


def extraire_note_moyenne(soup):
    note_tag = soup.select_one(".big-note .note")
    if not note_tag:
        return None
    txt = note_tag.get_text(strip=True).replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return None


def recuperer_critiques_presse(page, allocine_id):
    url = f"https://www.allocine.fr/film/fichefilm-{allocine_id}/critiques/presse/"
    page.goto(url)
    page.wait_for_timeout(1500)

    soup = BeautifulSoup(page.content(), "html.parser")
    note_moyenne = extraire_note_moyenne(soup)

    critiques = []
    for item in soup.find_all("div", class_="item", id=lambda x: x and x.startswith("pressreview")):
        titre_presse_tag = item.find("h2", class_="title")
        titre_presse = titre_presse_tag.get_text(strip=True) if titre_presse_tag else None

        note = None
        rating_div = item.select_one(".rating-mdl")
        if rating_div:
            for c in rating_div.get("class", []):
                m = re.match(r"^n(\d+)$", c)
                if m:
                    note = int(m.group(1)) / 10
                    break

        author_span = item.find("span", class_="author")
        auteur = author_span.get_text(strip=True).replace("par ", "") if author_span else None

        text_tag = item.find("p", class_="text")
        citation = text_tag.get_text(strip=True) if text_tag else None

        critiques.append({
            "titre_presse": titre_presse,
            "note": note,
            "auteur": auteur,
            "citation": citation,
        })

    return {
        "allocine_url_presse": url,
        "note_moyenne_presse": note_moyenne,
        "nb_critiques_presse": len(critiques),
        "critiques_presse": critiques,
    }


def recuperer_note_spectateurs(page, allocine_id):
    url = f"https://www.allocine.fr/film/fichefilm-{allocine_id}/critiques/spectateurs/"
    page.goto(url)
    page.wait_for_timeout(1500)

    soup = BeautifulSoup(page.content(), "html.parser")
    note_moyenne = extraire_note_moyenne(soup)

    nb_notes = None
    count_tag = soup.select_one(".user-note-count")
    if count_tag:
        m = re.search(r"[\d\s]+", count_tag.get_text(strip=True))
        if m:
            nb_notes = int(m.group(0).replace(" ", "").replace("\xa0", ""))

    return {
        "allocine_url_spectateurs": url,
        "note_moyenne_spectateurs": note_moyenne,
        "nb_notes_spectateurs": nb_notes,
    }


def enrichir_films(films, corrections, max_films=None):
    resultats = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        films_a_traiter = films[:max_films] if max_films else films

        for i, film in enumerate(films_a_traiter):
            titre_cineville = film["titre"]
            titre_recherche = corrections.get(titre_cineville, titre_cineville)

            info_correction = " (corrigé)" if titre_recherche != titre_cineville else ""
            print(f"[{i+1}/{len(films_a_traiter)}] Recherche AlloCiné pour : {titre_recherche}{info_correction}")

            allocine_id = rechercher_film_allocine(page, titre_recherche)

            if not allocine_id:
                print(f"   -> Pas trouvé sur AlloCiné")
                film["allocine"] = None
                resultats.append(film)
                continue

            print(f"   -> ID AlloCiné trouvé : {allocine_id}")

            infos_presse = recuperer_critiques_presse(page, allocine_id)
            print(f"   -> Presse : {infos_presse['nb_critiques_presse']} critique(s), moyenne {infos_presse['note_moyenne_presse']}")

            infos_spectateurs = recuperer_note_spectateurs(page, allocine_id)
            print(f"   -> Spectateurs : moyenne {infos_spectateurs['note_moyenne_spectateurs']} ({infos_spectateurs['nb_notes_spectateurs']} notes)")

            film["allocine"] = {
                "allocine_id": allocine_id,
                **infos_presse,
                **infos_spectateurs,
            }
            resultats.append(film)

            time.sleep(0.5)

        browser.close()

    return resultats


if __name__ == "__main__":
    with open("films_bruxelles.json", encoding="utf-8") as f:
        films = json.load(f)

    corrections = charger_corrections()
    if corrections:
        print(f"{len(corrections)} correction(s) de titre chargée(s) depuis corrections_titres.json\n")

    print(f"{len(films)} films à enrichir avec AlloCiné\n")

    resultats = enrichir_films(films, corrections, max_films=None)

    with open("films_avec_allocine.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

    print("\nSauvegardé dans films_avec_allocine.json")