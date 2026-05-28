"""
Intentions de Messes - Web App
Backend FastAPI + logique métier complète (port du skill intention-messe)
"""

import os
import httpx
from datetime import date, timedelta
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import math

app = FastAPI(title="Intentions de Messes")
templates = Jinja2Templates(directory="templates")

# ── Configuration ──────────────────────────────────────────────────────────────
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DS_ID = "2d183ba0-7414-8018-ae4d-fee6db4c950d"
NOTION_VIEW_URL = "https://www.notion.so/2d183ba074148018ae4dfee6db4c950d"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
MAX_SEARCH_DAYS = 365


# ── Helpers Notion ─────────────────────────────────────────────────────────────
def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


async def fetch_all_intentions() -> list[dict]:
    """Charge toutes les intentions depuis Notion avec pagination complète."""
    if not NOTION_TOKEN:
        raise HTTPException(status_code=500, detail="NOTION_TOKEN absent. Vérifiez les variables d'environnement Railway.")
    results = []
    cursor = None
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            body = {
                "page_size": 100,
                "sorts": [{"property": "Date", "direction": "ascending"}],
            }
            if cursor:
                body["start_cursor"] = cursor
            r = await client.post(
                f"{NOTION_API}/databases/{NOTION_DS_ID}/query",
                headers=notion_headers(),
                json=body,
            )
            if not r.is_success:
                raise HTTPException(
                    status_code=502,
                    detail=f"Notion API {r.status_code} : {r.text[:300]}"
                )
            data = r.json()
            for page in data.get("results", []):
                props = page.get("properties", {})
                nom_prop = props.get("Nom", {})
                nom = ""
                if nom_prop.get("title"):
                    nom = "".join(t.get("plain_text", "") for t in nom_prop["title"])
                date_prop = props.get("Date", {}).get("date") or {}
                demandeur_prop = props.get("Demandeur", {})
                demandeur = ""
                if demandeur_prop.get("rich_text"):
                    demandeur = "".join(t.get("plain_text", "") for t in demandeur_prop["rich_text"])
                desc_prop = props.get("Description", {})
                description = ""
                if desc_prop.get("rich_text"):
                    description = "".join(t.get("plain_text", "") for t in desc_prop["rich_text"])
                if date_prop.get("start"):
                    results.append({
                        "id": page["id"],
                        "nom": nom,
                        "demandeur": demandeur,
                        "description": description,
                        "date_start": date.fromisoformat(date_prop["start"]),
                        "date_end": date.fromisoformat(date_prop["end"]) if date_prop.get("end") else None,
                        "fixe": nom.rstrip().endswith("♦"),
                    })
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
    return results


async def notion_create(nom: str, demandeur: str, description: str, d: date, d_end: Optional[date] = None):
    date_val = {"start": d.isoformat()}
    if d_end:
        date_val["end"] = d_end.isoformat()
    props = {
        "Nom": {"title": [{"text": {"content": nom}}]},
        "Date": {"date": date_val},
    }
    if demandeur:
        props["Demandeur"] = {"rich_text": [{"text": {"content": demandeur}}]}
    if description:
        props["Description"] = {"rich_text": [{"text": {"content": description}}]}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{NOTION_API}/pages",
            headers=notion_headers(),
            json={"parent": {"database_id": NOTION_DS_ID}, "properties": props},
        )
        r.raise_for_status()
        return r.json()


async def notion_update_date(page_id: str, new_start: date, new_end: Optional[date] = None):
    date_val = {"start": new_start.isoformat()}
    if new_end:
        date_val["end"] = new_end.isoformat()
    else:
        date_val["end"] = None
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.patch(
            f"{NOTION_API}/pages/{page_id}",
            headers=notion_headers(),
            json={"properties": {"Date": {"date": date_val}}},
        )
        r.raise_for_status()


# ── Logique métier ─────────────────────────────────────────────────────────────
def paques(year: int) -> date:
    """Calcul de la date de Pâques (algorithme de Butcher)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d_ = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d_ - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def ascension(year: int) -> date:
    return paques(year) + timedelta(days=39)


def capacite(jour: date) -> int:
    if jour.month in (7, 8):
        return 1
    if (jour.month, jour.day) == (12, 25):
        return 3
    if (jour.month, jour.day) == (11, 2):
        return 3
    if (jour.month, jour.day) == (11, 1):
        return 2
    if jour == ascension(jour.year):
        return 2
    if jour.weekday() == 6:
        return 2
    return 1


def build_map_jour(intentions: list[dict]) -> dict[date, list[dict]]:
    """Construit un dictionnaire date → liste d'intentions couvrant ce jour."""
    m: dict[date, list[dict]] = {}
    for intention in intentions:
        d_start = intention["date_start"]
        d_end = intention["date_end"] or d_start
        cur = d_start
        while cur <= d_end:
            m.setdefault(cur, []).append(intention)
            cur += timedelta(days=1)
    return m


def est_inamovible(intention: dict, today: date) -> bool:
    d_start = intention["date_start"]
    d_end = intention["date_end"] or d_start
    return d_start <= today <= d_end


def est_libre(jour: date, map_jour: dict, cap: Optional[int] = None) -> bool:
    n = len(map_jour.get(jour, []))
    c = cap if cap is not None else capacite(jour)
    return n < c


def trouver_premiere_date_libre(depuis: date, map_jour: dict, duree: int = 1) -> Optional[date]:
    """
    Trouve la première date (ou début de bloc pour duree > 1) libre.
    Pour duree=1 : première date libre.
    Pour duree > 1 : premier bloc de `duree` jours sans ♦ ni inamovible.
    """
    today = date.today()
    plafond = depuis + timedelta(days=MAX_SEARCH_DAYS)
    cur = depuis
    while cur <= plafond:
        if duree == 1:
            if est_libre(cur, map_jour):
                return cur
        else:
            # Bloc entier sans ♦ ni inamovible
            ok = True
            for offset in range(duree):
                j = cur + timedelta(days=offset)
                occupants = map_jour.get(j, [])
                for occ in occupants:
                    if occ["fixe"] or est_inamovible(occ, today):
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return cur
        cur += timedelta(days=1)
    return None


def detect_violations(intentions: list[dict]) -> list[dict]:
    """Détecte toutes les violations de capacité dans la base."""
    map_jour = build_map_jour(intentions)
    violations = []
    for jour, occs in map_jour.items():
        cap = capacite(jour)
        if len(occs) > cap:
            violations.append({
                "date": jour.isoformat(),
                "capacite": cap,
                "count": len(occs),
                "intentions": [{"nom": o["nom"], "demandeur": o["demandeur"]} for o in occs],
            })
    return sorted(violations, key=lambda v: v["date"])


# ── Modèles Pydantic ───────────────────────────────────────────────────────────
class InsertionRequest(BaseModel):
    nom: str
    demandeur: Optional[str] = ""
    description: Optional[str] = ""
    date_souhaitee: Optional[str] = None   # ISO date ou None = prochaine libre
    force_date: bool = False               # ignorer les conflits (usage interne)


class DateLibreRequest(BaseModel):
    depuis: str   # ISO date
    duree: int = 1


# ── Routes API ─────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/diagnostic")
async def diagnostic():
    """Vérifie la connexion Notion et liste les propriétés de la base."""
    token_ok = bool(NOTION_TOKEN)
    result = {
        "token_present": token_ok,
        "token_prefix": NOTION_TOKEN[:12] + "..." if token_ok else None,
        "database_id": NOTION_DS_ID,
    }
    if not token_ok:
        result["erreur"] = "NOTION_TOKEN absent ou vide"
        return result
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{NOTION_API}/databases/{NOTION_DS_ID}",
                headers=notion_headers(),
            )
            result["status_http"] = r.status_code
            if r.status_code == 200:
                data = r.json()
                result["database_title"] = "".join(
                    t.get("plain_text", "") for t in data.get("title", [])
                )
                result["proprietes"] = {
                    k: v.get("type") for k, v in data.get("properties", {}).items()
                }
            else:
                result["erreur_notion"] = r.text[:300]
    except Exception as e:
        result["exception"] = str(e)
    return result


@app.get("/api/intentions")
async def api_intentions():
    """Retourne toutes les intentions triées par date."""
    intentions = await fetch_all_intentions()
    return [
        {
            "id": i["id"],
            "nom": i["nom"],
            "demandeur": i["demandeur"],
            "description": i["description"],
            "date_start": i["date_start"].isoformat(),
            "date_end": i["date_end"].isoformat() if i["date_end"] else None,
            "fixe": i["fixe"],
            "capacite": capacite(i["date_start"]),
        }
        for i in intentions
    ]


@app.post("/api/date-libre")
async def api_date_libre(req: DateLibreRequest):
    """Trouve la prochaine date libre à partir d'une date donnée."""
    depuis = date.fromisoformat(req.depuis)
    intentions = await fetch_all_intentions()
    map_jour = build_map_jour(intentions)
    result = trouver_premiere_date_libre(depuis, map_jour, req.duree)
    if result is None:
        raise HTTPException(status_code=404, detail="Aucune date libre dans les 365 prochains jours.")
    # Info sur le jour trouvé
    occupants = map_jour.get(result, [])
    return {
        "date": result.isoformat(),
        "capacite": capacite(result),
        "intentions_existantes": [
            {"nom": o["nom"], "demandeur": o["demandeur"]} for o in occupants
        ],
    }


@app.get("/api/violations")
async def api_violations():
    """Détecte et retourne toutes les violations de capacité."""
    intentions = await fetch_all_intentions()
    return detect_violations(intentions)


@app.post("/api/inserer")
async def api_inserer(req: InsertionRequest):
    """
    Insère une intention en appliquant toutes les règles du skill :
    - Préfixe RIP si défunt
    - ♦ si date précise fournie
    - Déplacement des sans-♦ si nécessaire
    - Blocage sur ♦/♦ ou inamovible saturant
    """
    today = date.today()

    # Normalisation du nom
    nom = req.nom.strip()
    mots_rip = ["rip", "défunt", "défunte", "repos", "suffrage", "trentain", "décès"]
    if any(m in nom.lower() for m in mots_rip) and not nom.lower().startswith("rip"):
        nom = f"RIP - {nom}"

    # Chargement de l'état
    intentions = await fetch_all_intentions()
    map_jour = build_map_jour(intentions)

    # Détermination de la date cible
    if req.date_souhaitee:
        try:
            cible = date.fromisoformat(req.date_souhaitee)
        except ValueError:
            raise HTTPException(status_code=400, detail="Format de date invalide (attendu YYYY-MM-DD).")
        date_precise = True
    else:
        cible = trouver_premiere_date_libre(today, map_jour)
        if cible is None:
            raise HTTPException(status_code=404, detail="Aucune date libre dans les 365 prochains jours.")
        date_precise = False

    # Vérification date passée
    if cible < today and not req.force_date:
        return JSONResponse(
            status_code=409,
            content={
                "code": "DATE_PASSEE",
                "message": f"La date {cible.isoformat()} est dans le passé. Confirmez-vous l'insertion ?",
                "date": cible.isoformat(),
            }
        )

    # Analyse du jour cible
    occupants = map_jour.get(cible, [])
    cap = capacite(cible)

    deplacements = []
    if len(occupants) >= cap:
        # Classer les occupants
        inamovibles = [o for o in occupants if o["fixe"] or est_inamovible(o, today)]
        sans_fixe = [o for o in occupants if not o["fixe"] and not est_inamovible(o, today)]

        if len(inamovibles) >= cap:
            # Blocage total
            return JSONResponse(
                status_code=409,
                content={
                    "code": "JOUR_BLOQUE",
                    "message": f"Le {cible.isoformat()} est saturé par des intentions fixes ou inamovibles.",
                    "occupants": [{"nom": o["nom"], "demandeur": o["demandeur"]} for o in inamovibles],
                }
            )

        # Trier les sans-♦ : date_start le plus récent en premier (puis id)
        sans_fixe_sorted = sorted(sans_fixe, key=lambda o: (o["date_start"], o["id"]), reverse=True)
        nb_a_deplacer = len(occupants) - cap + 1
        a_deplacer = sans_fixe_sorted[:nb_a_deplacer]

        if len(a_deplacer) > 3 and not req.force_date:
            return JSONResponse(
                status_code=409,
                content={
                    "code": "TROP_DEPLACEMENTS",
                    "message": f"{len(a_deplacer)} intentions seraient déplacées. Confirmez-vous ?",
                    "intentions": [{"nom": o["nom"], "demandeur": o["demandeur"], "date": o["date_start"].isoformat()} for o in a_deplacer],
                }
            )

        # Effectuer les déplacements
        for intention in a_deplacer:
            # Point de départ : max(date_start + 1, cible + 1)
            d_from = max(intention["date_start"] + timedelta(days=1), cible + timedelta(days=1))
            # Recharger map_jour après chaque déplacement
            intentions_fresh = await fetch_all_intentions()
            map_jour_fresh = build_map_jour(intentions_fresh)

            duree = 1
            if intention["date_end"]:
                duree = (intention["date_end"] - intention["date_start"]).days + 1

            nouvelle_date = trouver_premiere_date_libre(d_from, map_jour_fresh, duree)
            if nouvelle_date is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Impossible de trouver une date de remplacement pour « {intention['nom']} » dans les 365 jours."
                )

            new_end = (nouvelle_date + timedelta(days=duree - 1)) if duree > 1 else None
            await notion_update_date(intention["id"], nouvelle_date, new_end)
            deplacements.append({
                "nom": intention["nom"],
                "demandeur": intention["demandeur"],
                "ancienne_date": intention["date_start"].isoformat(),
                "nouvelle_date": nouvelle_date.isoformat(),
            })

    # Ajout du ♦ si date précise
    nom_final = nom
    if date_precise and not nom_final.rstrip().endswith("♦"):
        nom_final = f"{nom_final} ♦"

    # Création
    await notion_create(nom_final, req.demandeur or "", req.description or "", cible)

    return {
        "succes": True,
        "intention": {
            "nom": nom_final,
            "demandeur": req.demandeur,
            "date": cible.isoformat(),
        },
        "deplacements": deplacements,
    }


@app.get("/api/calendrier")
async def api_calendrier(mois: int, annee: int):
    """Retourne les intentions d'un mois donné avec info de capacité."""
    intentions = await fetch_all_intentions()
    map_jour = build_map_jour(intentions)

    # Premier et dernier jour du mois
    premier = date(annee, mois, 1)
    if mois == 12:
        dernier = date(annee + 1, 1, 1) - timedelta(days=1)
    else:
        dernier = date(annee, mois + 1, 1) - timedelta(days=1)

    jours = []
    cur = premier
    while cur <= dernier:
        occs = map_jour.get(cur, [])
        cap = capacite(cur)
        jours.append({
            "date": cur.isoformat(),
            "capacite": cap,
            "count": len(occs),
            "libre": len(occs) < cap,
            "violation": len(occs) > cap,
            "intentions": [
                {
                    "nom": o["nom"],
                    "demandeur": o["demandeur"],
                    "fixe": o["fixe"],
                    "periode": o["date_end"] is not None,
                }
                for o in occs
            ],
        })
        cur += timedelta(days=1)

    return {"mois": mois, "annee": annee, "jours": jours}
