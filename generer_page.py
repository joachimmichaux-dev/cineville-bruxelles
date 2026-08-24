"""
Etape finale : generer une page HTML avec la programmation Cineville + les infos AlloCine
Tri : 1) meilleure note presse, 2) plus grand nombre de critiques presse a note egale,
      3) plus grand nombre de seances a egalite, 4) films sans note presse a la fin (par nb seances)
"""
import json
import html


def note_html(note, max_note=5):
    if note is None:
        return "<span class='no-note'>—</span>"
    return f"<span class='note'>{note:.1f}/5</span>"


def score_tri(film):
    """Renvoie (groupe, -note_presse, -nb_critiques_presse, -nb_seances) pour le tri.
    Groupe 0 = a une note presse (triee par note desc, puis nb critiques desc, puis nb seances desc).
    Groupe 1 = pas de note presse (triee par nb seances desc)."""
    allocine = film.get("allocine")
    nb_seances = len(film.get("seances") or [])

    note_presse = allocine.get("note_moyenne_presse") if allocine else None

    if note_presse is None:
        return (1, 0, 0, -nb_seances)

    nb_critiques = allocine.get("nb_critiques_presse") or 0
    return (0, -note_presse, -nb_critiques, -nb_seances)


def generer_html(films):
    films_tries = sorted(films, key=score_tri)

    cartes = []
    for film in films_tries:
        titre = html.escape(film.get("titre") or "Titre inconnu")
        annee = film.get("annee") or ""
        duree = film.get("duree_minutes")
        duree_txt = f"{duree} min" if duree else ""
        realisateurs = ", ".join(film.get("realisateurs") or []) or "Réalisateur inconnu"
        synopsis = html.escape(film.get("synopsis") or "")
        affiche = film.get("affiche_url")

        seances = film.get("seances") or []
        seances_html = "".join(
            f"<li>{html.escape(s.get('heure') or '')} — {html.escape(s.get('cinema') or '')}</li>"
            for s in seances
        )

        allocine = film.get("allocine") or {}
        note_presse = allocine.get("note_moyenne_presse")
        nb_presse = allocine.get("nb_critiques_presse") or 0
        note_spect = allocine.get("note_moyenne_spectateurs")
        nb_spect = allocine.get("nb_notes_spectateurs")
        url_presse = allocine.get("allocine_url_presse")

        critiques = allocine.get("critiques_presse") or []
        critiques_html = ""
        if critiques:
            lignes = []
            for c in critiques[:6]:
                titre_presse = html.escape(c.get("titre_presse") or "")
                note_c = c.get("note")
                note_c_txt = f"{note_c:.1f}/5" if note_c is not None else "—"
                citation = html.escape(c.get("citation") or "")
                lignes.append(
                    f"<li><strong>{titre_presse}</strong> ({note_c_txt}) — <em>{citation}</em></li>"
                )
            critiques_html = f"<details><summary>Voir {len(critiques)} critique(s) presse</summary><ul class='critiques'>{''.join(lignes)}</ul></details>"

        poster_html = f"<img src='{html.escape(affiche)}' alt='{titre}' class='poster'>" if affiche else "<div class='poster poster-placeholder'>🎬</div>"

        badge = ""
        if not allocine:
            badge = "<span class='badge badge-warn'>Non trouvé sur AlloCiné</span>"

        carte = f"""
        <div class="carte">
            {poster_html}
            <div class="contenu">
                <h2>{titre} <span class="annee">({annee})</span></h2>
                <p class="meta">{html.escape(realisateurs)} · {duree_txt} · {len(seances)} séance(s)</p>
                {badge}
                <p class="synopsis">{synopsis}</p>

                <div class="notes">
                    <div class="note-bloc">
                        <span class="label">Presse AlloCiné</span>
                        {note_html(note_presse)}
                        <span class="count">{nb_presse} critique(s)</span>
                    </div>
                    <div class="note-bloc">
                        <span class="label">Spectateurs AlloCiné</span>
                        {note_html(note_spect)}
                        <span class="count">{nb_spect or 0} note(s)</span>
                    </div>
                </div>

                {critiques_html}

                <details>
                    <summary>Séances ({len(seances)})</summary>
                    <ul class="seances">{seances_html}</ul>
                </details>

                {"<a class='lien-allocine' href='" + url_presse + "' target='_blank'>Voir sur AlloCiné →</a>" if url_presse else ""}
            </div>
        </div>
        """
        cartes.append(carte)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Cineville Bruxelles + AlloCiné</title>
<style>
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #14161a;
        color: #e8e8e8;
        margin: 0;
        padding: 20px;
    }}
    h1 {{
        text-align: center;
        margin-bottom: 30px;
        color: #ffd447;
    }}
    .grille {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 20px;
        max-width: 1400px;
        margin: 0 auto;
    }}
    .carte {{
        background: #1e2126;
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }}
    .poster {{
        width: 100%;
        height: 280px;
        object-fit: cover;
    }}
    .poster-placeholder {{
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 60px;
        background: #2a2d33;
    }}
    .contenu {{
        padding: 16px;
    }}
    h2 {{
        font-size: 18px;
        margin: 0 0 6px 0;
    }}
    .annee {{
        color: #999;
        font-weight: normal;
        font-size: 14px;
    }}
    .meta {{
        color: #aaa;
        font-size: 13px;
        margin: 0 0 6px 0;
    }}
    .badge {{
        display: inline-block;
        font-size: 11px;
        padding: 3px 8px;
        border-radius: 4px;
        margin-bottom: 10px;
    }}
    .badge-warn {{
        background: #4a3a1a;
        color: #ffb347;
    }}
    .synopsis {{
        font-size: 14px;
        color: #ccc;
        margin-bottom: 14px;
        line-height: 1.4;
    }}
    .notes {{
        display: flex;
        gap: 12px;
        margin-bottom: 12px;
    }}
    .note-bloc {{
        flex: 1;
        background: #2a2d33;
        border-radius: 6px;
        padding: 8px;
        text-align: center;
    }}
    .label {{
        display: block;
        font-size: 11px;
        color: #999;
        margin-bottom: 4px;
    }}
    .note {{
        display: block;
        font-size: 18px;
        font-weight: bold;
        color: #ffd447;
    }}
    .no-note {{
        display: block;
        font-size: 18px;
        color: #555;
    }}
    .count {{
        display: block;
        font-size: 11px;
        color: #777;
        margin-top: 2px;
    }}
    details {{
        margin-top: 10px;
        font-size: 13px;
    }}
    summary {{
        cursor: pointer;
        color: #7bb8ff;
    }}
    ul.critiques, ul.seances {{
        margin: 8px 0 0 0;
        padding-left: 18px;
    }}
    ul.critiques li, ul.seances li {{
        margin-bottom: 6px;
        color: #ccc;
    }}
    .lien-allocine {{
        display: inline-block;
        margin-top: 12px;
        color: #ffd447;
        text-decoration: none;
        font-size: 13px;
    }}
    .lien-allocine:hover {{
        text-decoration: underline;
    }}
</style>
</head>
<body>
    <h1>🎬 Cineville Bruxelles — {len(films)} films à l'affiche</h1>
    <div class="grille">
        {"".join(cartes)}
    </div>
</body>
</html>"""


if __name__ == "__main__":
    with open("films_avec_allocine.json", encoding="utf-8") as f:
        films = json.load(f)

    page = generer_html(films)

    with open("programmation.html", "w", encoding="utf-8") as f:
        f.write(page)

    print(f"Page générée : programmation.html ({len(films)} films)")