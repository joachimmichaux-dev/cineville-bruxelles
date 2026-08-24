"""
Etape finale : generer une page HTML avec la programmation Cineville + les infos AlloCine
Tri films : 1) meilleure note presse, 2) plus de critiques presse a note egale,
            3) plus de seances a egalite, 4) films sans note presse a la fin (par nb seances)
Tri critiques : titres de presse prioritaires en premier
"""
import json
import html

TITRES_PRESSE_PRIORITAIRES = [
    "le monde",
    "libération",
    "télérama",
    "les inrockuptibles",
    "cahiers du cinéma",
    "positif",
]


def trier_critiques(critiques):
    """Fait remonter les titres de presse prioritaires en premier, dans l'ordre donné."""
    def cle_tri(c):
        titre = (c.get("titre_presse") or "").lower()
        for i, prioritaire in enumerate(TITRES_PRESSE_PRIORITAIRES):
            if prioritaire in titre:
                return (0, i)
        return (1, 0)
    return sorted(critiques, key=cle_tri)


def note_html(note, max_note=5):
    if note is None:
        return "<span class='no-note'>—</span>"
    return f"<span class='note'>{note:.1f}/5</span>"


def score_tri(film):
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

        critiques = trier_critiques(allocine.get("critiques_presse") or [])
        critiques_html = ""
        if critiques:
            lignes = []
            for c in critiques[:8]:
                titre_presse = html.escape(c.get("titre_presse") or "")
                note_c = c.get("note")
                note_c_txt = f"{note_c:.1f}/5" if note_c is not None else "—"
                citation = html.escape(c.get("citation") or "")
                lignes.append(
                    f"<li><strong>{titre_presse}</strong> ({note_c_txt}) — <em>{citation}</em></li>"
                )
            critiques_html = f"<details><summary>Voir {len(critiques)} critique(s) presse</summary><ul class='critiques'>{''.join(lignes)}</ul></details>"

        poster_html = f"<img src='{html.escape(affiche)}' alt='{titre}' class='poster' loading='lazy'>" if affiche else "<div class='poster poster-placeholder'>🎬</div>"

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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cineville Bruxelles + AlloCiné</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #000000;
        --bg-carte: #141414;
        --bg-bloc: #1f1f1f;
        --accent: #ffffff;
        --texte: #ffffff;
        --texte-att: #b3b3b3;
        --texte-faible: #7a7a7a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: var(--bg);
        color: var(--texte);
        margin: 0;
        padding: 24px;
        -webkit-font-smoothing: antialiased;
    }}
    h1 {{
        text-align: center;
        margin: 0 0 32px 0;
        font-size: 26px;
        font-weight: 700;
        color: var(--texte);
        letter-spacing: -0.3px;
    }}
    .grille {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
        gap: 24px;
        max-width: 1400px;
        margin: 0 auto;
    }}
    .carte {{
        background: var(--bg-carte);
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        border: 1px solid rgba(255,255,255,0.08);
    }}
    .poster {{
        width: 100%;
        height: 300px;
        object-fit: cover;
        display: block;
    }}
    .poster-placeholder {{
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 60px;
        background: var(--bg-bloc);
        height: 300px;
    }}
    .contenu {{
        padding: 20px;
    }}
    h2 {{
        font-size: 19px;
        font-weight: 600;
        margin: 0 0 8px 0;
        line-height: 1.3;
        letter-spacing: -0.2px;
    }}
    .annee {{
        color: var(--texte-faible);
        font-weight: 400;
        font-size: 15px;
    }}
    .meta {{
        color: var(--texte-att);
        font-size: 14px;
        margin: 0 0 10px 0;
    }}
    .badge {{
        display: inline-block;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 6px;
        margin-bottom: 12px;
    }}
    .badge-warn {{
        background: #2a2a2a;
        color: #b3b3b3;
    }}
    .synopsis {{
        font-size: 15px;
        color: var(--texte-att);
        margin-bottom: 18px;
        line-height: 1.55;
    }}
    .notes {{
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
    }}
    .note-bloc {{
        flex: 1;
        background: var(--bg-bloc);
        border-radius: 10px;
        padding: 12px 8px;
        text-align: center;
    }}
    .label {{
        display: block;
        font-size: 12px;
        color: var(--texte-faible);
        margin-bottom: 6px;
    }}
    .note {{
        display: block;
        font-size: 19px;
        font-weight: 700;
        color: var(--texte);
    }}
    .no-note {{
        display: block;
        font-size: 19px;
        color: #444444;
    }}
    .count {{
        display: block;
        font-size: 12px;
        color: var(--texte-faible);
        margin-top: 3px;
    }}
    details {{
        margin-top: 12px;
        font-size: 15px;
        border-top: 1px solid rgba(255,255,255,0.06);
        padding-top: 12px;
    }}
    summary {{
        cursor: pointer;
        color: var(--texte);
        font-weight: 500;
        padding: 10px 4px;
        margin: -10px -4px;
        border-radius: 8px;
        list-style: none;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    summary::-webkit-details-marker {{ display: none; }}
    summary::after {{
        content: '+';
        font-size: 20px;
        color: var(--texte-faible);
    }}
    details[open] summary::after {{
        content: '−';
    }}
    summary:active {{
        background: rgba(255,255,255,0.06);
    }}
    ul.critiques, ul.seances {{
        margin: 10px 0 0 0;
        padding: 0;
        list-style: none;
    }}
    ul.critiques li, ul.seances li {{
        margin-bottom: 10px;
        padding: 10px 12px;
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
        color: var(--texte-att);
        line-height: 1.5;
    }}
    ul.critiques li strong {{
        color: var(--texte);
    }}
    .lien-allocine {{
        display: inline-block;
        margin-top: 16px;
        color: var(--texte-att);
        text-decoration: underline;
        font-size: 14px;
        font-weight: 500;
        padding: 8px 4px;
    }}
    .lien-allocine:hover {{
        text-decoration: underline;
    }}

    /* Mobile : une seule colonne, zones cliquables agrandies */
    @media (max-width: 640px) {{
        body {{ padding: 14px; }}
        h1 {{ font-size: 22px; margin-bottom: 20px; }}
        .grille {{
            grid-template-columns: 1fr;
            gap: 18px;
        }}
        .poster, .poster-placeholder {{ height: 240px; }}
        h2 {{ font-size: 19px; }}
        summary {{ padding: 14px 6px; margin: -14px -6px; font-size: 16px; }}
        ul.critiques li, ul.seances li {{ padding: 12px 14px; font-size: 15px; }}
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
