"""
Intentions de Messes - Web App
Backend FastAPI + logique métier conforme au skill intention-messe
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

app = FastAPI(title="Intentions de Messes")
templates = Jinja2Templates(directory="templates")

# ── Configuration ──────────────────────────────────────────────────────────────
NOTION_TOKEN  = os.environ.get("NOTION_TOKEN", "")
NOTION_DS_ID  = "2d183ba0-7414-8018-ae4d-fee6db4c950d"
NOTION_API    = "https://api.notion.com/v1"
NOTION_VER    = "2022-06-28"
MAX_SEARCH    = 365


# ── Helpers Notion ─────────────────────────────────────────────────────────────
def notion_headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VER,
        "Content-Type": "application/json",
    }


async def fetch_all_intentions() -> list[dict]:
    """Charge toutes les intentions avec pagination complète. Erreurs remontent en JSON."""
    if not NOTION_TOKEN:
        raise HTTPException(500, "NOTION_TOKEN absent. Vérifiez les variables d'environnement.")
    results = []
    cursor = None
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            body: dict = {
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
                raise HTTPException(502, f"Notion API {r.status_code} : {r.text[:300]}")
            data = r.json()
            for page in data.get("results", []):
                props     = page.get("properties", {})
                nom_prop  = props.get("Nom", {})
                nom       = "".join(t.get("plain_text", "") for t in nom_prop.get("title", []))
                date_prop = (props.get("Date") or {}).get("date") or {}
                dem_prop  = props.get("Demandeur", {})
                demandeur = "".join(t.get("plain_text", "") for t in dem_prop.get("rich_text", []))
                desc_prop = props.get("Description", {})
                description = "".join(t.get("plain_text", "") for t in desc_prop.get("rich_text", []))
                if date_prop.get("start"):
                    results.append({
                        "id":          page["id"],
                        "nom":         nom,
                        "demandeur":   demandeur,
                        "description": description,
                        "date_start":  date.fromisoformat(date_prop["start"]),
                        "date_end":    date.fromisoformat(date_prop["end"]) if date_prop.get("end") else None,
                        "fixe":        nom.rstrip().endswith("♦"),
                    })
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
    return results


async def notion_create(nom: str, demandeur: str, description: str,
                        d: date, d_end: Optional[date] = None) -> dict:
    """Crée une entrée. N'envoie jamais de chaîne vide pour Demandeur/Description (règle 14)."""
    date_val: dict = {"start": d.isoformat()}
    if d_end:
        date_val["end"] = d_end.isoformat()
    props: dict = {
        "Nom":  {"title": [{"text": {"content": nom}}]},
        "Date": {"date": date_val},
    }
    # Règle : omettre la propriété si vide, jamais envoyer ""
    if demandeur:
        props["Demandeur"]   = {"rich_text": [{"text": {"content": demandeur}}]}
    if description:
        props["Description"] = {"rich_text": [{"text": {"content": description}}]}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{NOTION_API}/pages",
            headers=notion_headers(),
            json={"parent": {"database_id": NOTION_DS_ID}, "properties": props},
        )
        if not r.is_success:
            raise HTTPException(502, f"Notion create {r.status_code} : {r.text[:300]}")
        return r.json()


async def notion_update_date(page_id: str, new_start: date,
                             new_end: Optional[date] = None) -> None:
    """Met à jour uniquement la propriété Date. Titre/demandeur/description intacts."""
    date_val: dict = {"start": new_start.isoformat(), "end": new_end.isoformat() if new_end else None}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.patch(
            f"{NOTION_API}/pages/{page_id}",
            headers=notion_headers(),
            json={"properties": {"Date": {"date": date_val}}},
        )
        if not r.is_success:
            raise HTTPException(502, f"Notion update {r.status_code} : {r.text[:300]}")


# ── Logique métier ─────────────────────────────────────────────────────────────
def paques(year: int) -> date:
    a = year % 19; b = year // 100; c = year % 100
    d_ = b // 4;   e = b % 4;       f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d_ - g + 15) % 30
    i = c // 4;    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day   = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def ascension(year: int) -> date:
    return paques(year) + timedelta(days=39)


def capacite(jour: date) -> int:
    if jour.month in (7, 8):                   return 1  # juillet-août sans exception
    if (jour.month, jour.day) == (12, 25):     return 3  # Noël
    if (jour.month, jour.day) == (11, 2):      return 3  # Commémoration
    if (jour.month, jour.day) == (11, 1):      return 2  # Toussaint
    if jour == ascension(jour.year):           return 2  # Ascension
    if jour.weekday() == 6:                    return 2  # Dimanche
    return 1


def build_map_jour(intentions: list[dict]) -> dict[date, list[dict]]:
    """date → toutes les intentions qui couvrent ce jour (périodes incluses)."""
    m: dict[date, list[dict]] = {}
    for intention in intentions:
        cur = intention["date_start"]
        end = intention["date_end"] or cur
        while cur <= end:
            m.setdefault(cur, []).append(intention)
            cur += timedelta(days=1)
    return m


def est_inamovible(intention: dict, today: date) -> bool:
    """Période en cours : date_start ≤ today ≤ date_end → intouchable."""
    d_end = intention["date_end"] or intention["date_start"]
    return intention["date_start"] <= today <= d_end


def est_libre(jour: date, map_jour: dict) -> bool:
    return len(map_jour.get(jour, [])) < capacite(jour)


def trouver_date_libre(depuis: date, map_jour: dict, duree: int = 1) -> Optional[date]:
    """
    Cherche la première date (ou début de bloc) libre à partir de `depuis`.
    duree=1 : jour simple libre.
    duree>1 : bloc de `duree` jours entièrement sans ♦ ni inamovible.
    Plafond : MAX_SEARCH jours.
    """
    today   = date.today()
    plafond = depuis + timedelta(days=MAX_SEARCH)
    cur     = depuis
    while cur <= plafond:
        if duree == 1:
            if est_libre(cur, map_jour):
                return cur
        else:
            ok = True
            for offset in range(duree):
                j = cur + timedelta(days=offset)
                for occ in map_jour.get(j, []):
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
    map_jour = build_map_jour(intentions)
    viol = []
    for jour, occs in map_jour.items():
        if len(occs) > capacite(jour):
            viol.append({
                "date":      jour.isoformat(),
                "capacite":  capacite(jour),
                "count":     len(occs),
                "intentions": [{"nom": o["nom"], "demandeur": o["demandeur"]} for o in occs],
            })
    return sorted(viol, key=lambda v: v["date"])


# ── Modèles Pydantic ───────────────────────────────────────────────────────────
class InsertionRequest(BaseModel):
    nom:            str
    demandeur:      Optional[str] = None
    description:    Optional[str] = None
    date_souhaitee: Optional[str] = None   # ISO YYYY-MM-DD ; None = prochaine libre
    date_fin:       Optional[str] = None   # Pour neuvaine/trentain
    force_date:     bool = False


class DateLibreRequest(BaseModel):
    depuis: str
    duree:  int = 1


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/diagnostic")
async def diagnostic():
    token_ok = bool(NOTION_TOKEN)
    result: dict = {
        "token_present": token_ok,
        "token_prefix":  NOTION_TOKEN[:12] + "..." if token_ok else None,
        "database_id":   NOTION_DS_ID,
    }
    if not token_ok:
        result["erreur"] = "NOTION_TOKEN absent"
        return result
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{NOTION_API}/databases/{NOTION_DS_ID}",
                                 headers=notion_headers())
            result["status_http"] = r.status_code
            if r.status_code == 200:
                data = r.json()
                result["database_title"] = "".join(
                    t.get("plain_text", "") for t in data.get("title", []))
                result["proprietes"] = {
                    k: v.get("type") for k, v in data.get("properties", {}).items()}
            else:
                result["erreur_notion"] = r.text[:300]
    except Exception as e:
        result["exception"] = str(e)
    return result


@app.get("/api/intentions")
async def api_intentions():
    intentions = await fetch_all_intentions()
    return [{
        "id":          i["id"],
        "nom":         i["nom"],
        "demandeur":   i["demandeur"],
        "description": i["description"],
        "date_start":  i["date_start"].isoformat(),
        "date_end":    i["date_end"].isoformat() if i["date_end"] else None,
        "fixe":        i["fixe"],
        "capacite":    capacite(i["date_start"]),
    } for i in intentions]


@app.post("/api/date-libre")
async def api_date_libre(req: DateLibreRequest):
    depuis     = date.fromisoformat(req.depuis)
    intentions = await fetch_all_intentions()
    map_jour   = build_map_jour(intentions)
    result     = trouver_date_libre(depuis, map_jour, req.duree)
    if result is None:
        raise HTTPException(404, "Aucune date libre dans les 365 prochains jours.")
    occupants = map_jour.get(result, [])
    return {
        "date":                 result.isoformat(),
        "capacite":             capacite(result),
        "intentions_existantes": [{"nom": o["nom"], "demandeur": o["demandeur"]}
                                   for o in occupants],
    }


@app.get("/api/violations")
async def api_violations():
    return detect_violations(await fetch_all_intentions())


@app.post("/api/inserer")
async def api_inserer(req: InsertionRequest):
    """
    Insertion conforme au skill :
    1. Charger état Notion
    2. Valider date (passée → bloquer sauf force_date)
    3. Identifier les déplacements nécessaires
       - ♦/inamovible saturant → bloquer
       - >3 déplacements → confirmer (sauf force_date)
    4. Déplacer un à un dans l'ordre chronologique de date_start,
       recharger Notion entre chaque
    5. Créer l'intention
    6. Vérification finale : recharger, vérifier chaque jour touché
    """
    today = date.today()

    # ── Normalisation du nom ──
    nom = req.nom.strip()
    mots_rip = ["rip", "défunt", "défunte", "repos", "suffrage", "trentain", "décès"]
    if any(m in nom.lower() for m in mots_rip) and not nom.lower().startswith("rip"):
        nom = f"RIP - {nom}"

    # ── 1. Charger l'état ──
    intentions = await fetch_all_intentions()
    map_jour   = build_map_jour(intentions)

    # ── Déterminer date cible et date_end ──
    if req.date_souhaitee:
        try:
            cible = date.fromisoformat(req.date_souhaitee)
        except ValueError:
            raise HTTPException(400, "Format de date invalide (attendu YYYY-MM-DD).")
        date_precise = True
    else:
        cible = trouver_date_libre(today, map_jour)
        if cible is None:
            raise HTTPException(404, "Aucune date libre dans les 365 prochains jours.")
        date_precise = False

    # date_fin explicite (neuvaine/trentain)
    cible_end: Optional[date] = None
    if req.date_fin:
        try:
            cible_end = date.fromisoformat(req.date_fin)
        except ValueError:
            raise HTTPException(400, "Format de date_fin invalide.")
    duree_bloc = (cible_end - cible).days + 1 if cible_end else 1

    # ── 2. Valider date passée ──
    if cible < today and not req.force_date:
        return JSONResponse(status_code=409, content={
            "code":    "DATE_PASSEE",
            "message": f"La date {cible.isoformat()} est dans le passé. Confirmez-vous l'insertion ?",
            "date":    cible.isoformat(),
        })

    # ── 3. Identifier les déplacements ──
    # Collecter tous les occupants sur l'ensemble du bloc cible
    occupants_bloc: list[dict] = []
    for offset in range(duree_bloc):
        j = cible + timedelta(days=offset)
        for occ in map_jour.get(j, []):
            if occ not in occupants_bloc:
                occupants_bloc.append(occ)

    cap_min = min(capacite(cible + timedelta(days=i)) for i in range(duree_bloc))
    inamovibles = [o for o in occupants_bloc if o["fixe"] or est_inamovible(o, today)]
    sans_fixe   = [o for o in occupants_bloc if not o["fixe"] and not est_inamovible(o, today)]

    # Vérifier si le bloc est saturé par des inamovibles/♦
    # Pour chaque jour du bloc, compter inamovibles vs capacité
    for offset in range(duree_bloc):
        j = cible + timedelta(days=offset)
        inamo_j = [o for o in map_jour.get(j, []) if o["fixe"] or est_inamovible(o, today)]
        if len(inamo_j) >= capacite(j):
            return JSONResponse(status_code=409, content={
                "code":      "JOUR_BLOQUE",
                "message":   f"Le {j.isoformat()} est saturé par des intentions fixes ou inamovibles.",
                "occupants": [{"nom": o["nom"], "demandeur": o["demandeur"]} for o in inamo_j],
            })

    # Calculer quels sans-♦ déplacer :
    # Pour chaque jour du bloc, si complet, prendre les sans-♦ avec date_start le plus récent
    a_deplacer: list[dict] = []
    for offset in range(duree_bloc):
        j   = cible + timedelta(days=offset)
        cap = capacite(j)
        occs_j        = map_jour.get(j, [])
        inamo_j       = [o for o in occs_j if o["fixe"] or est_inamovible(o, today)]
        sans_fixe_j   = [o for o in occs_j if not o["fixe"] and not est_inamovible(o, today)]
        places_libres = cap - len(inamo_j) - 1  # -1 pour la nouvelle intention
        if places_libres < 0:
            # Ne devrait pas arriver (déjà bloqué ci-dessus), sécurité
            return JSONResponse(status_code=409, content={
                "code": "JOUR_BLOQUE",
                "message": f"Le {j.isoformat()} est saturé.",
                "occupants": [],
            })
        # Trier par date_start croissant, le plus récent part en premier (règle 3)
        sans_fixe_j_sorted = sorted(sans_fixe_j,
                                    key=lambda o: (o["date_start"], o["id"]),
                                    reverse=True)
        nb_a_deplacer_j = len(sans_fixe_j) - places_libres
        for o in sans_fixe_j_sorted[:nb_a_deplacer_j]:
            if o not in a_deplacer:
                a_deplacer.append(o)

    if len(a_deplacer) > 3 and not req.force_date:
        return JSONResponse(status_code=409, content={
            "code":      "TROP_DEPLACEMENTS",
            "message":   f"{len(a_deplacer)} intentions seraient déplacées. Confirmez-vous ?",
            "intentions": [{"nom": o["nom"], "demandeur": o["demandeur"],
                            "date": o["date_start"].isoformat()} for o in a_deplacer],
        })

    # ── 4. Déplacer un à un, ordre chronologique de date_start (le plus ancien en premier) ──
    # Règle 4 : ordre chronologique de date_start
    a_deplacer_sorted = sorted(a_deplacer, key=lambda o: (o["date_start"], o["id"]))

    deplacements = []
    for intention in a_deplacer_sorted:
        # Recharger avant chaque déplacement
        intentions_fresh = await fetch_all_intentions()
        map_jour_fresh   = build_map_jour(intentions_fresh)

        duree_int = 1
        if intention["date_end"]:
            duree_int = (intention["date_end"] - intention["date_start"]).days + 1

        # Point de départ : max(date_start_intention + 1, dernier_jour_bloc_cible + 1)
        # dernier_jour_bloc_cible = cible_end si période, cible si simple
        dernier_bloc = cible_end if cible_end else cible
        d_from = max(intention["date_start"] + timedelta(days=1),
                     dernier_bloc + timedelta(days=1))

        nouvelle_date = trouver_date_libre(d_from, map_jour_fresh, duree_int)
        if nouvelle_date is None:
            raise HTTPException(500,
                f"Impossible de trouver une date pour « {intention['nom']} » dans les 365 jours.")

        new_end = (nouvelle_date + timedelta(days=duree_int - 1)) if duree_int > 1 else None
        await notion_update_date(intention["id"], nouvelle_date, new_end)
        deplacements.append({
            "nom":           intention["nom"],
            "demandeur":     intention["demandeur"],
            "ancienne_date": intention["date_start"].isoformat(),
            "nouvelle_date": nouvelle_date.isoformat(),
        })

    # ── 5. Créer ──
    nom_final = nom
    if date_precise and not nom_final.rstrip().endswith("♦"):
        nom_final = f"{nom_final} ♦"

    await notion_create(
        nom_final,
        req.demandeur or "",   # notion_create omet si vide
        req.description or "",
        cible,
        cible_end,
    )

    # ── 6. Vérification finale ──
    intentions_final = await fetch_all_intentions()
    map_final        = build_map_jour(intentions_final)

    # Jours à vérifier : bloc cible + anciennes et nouvelles dates des déplacements
    jours_a_verifier: set[date] = set()
    for offset in range(duree_bloc):
        jours_a_verifier.add(cible + timedelta(days=offset))
    for dep in deplacements:
        jours_a_verifier.add(date.fromisoformat(dep["ancienne_date"]))
        jours_a_verifier.add(date.fromisoformat(dep["nouvelle_date"]))

    alertes = []
    for j in sorted(jours_a_verifier):
        occs_j = map_final.get(j, [])
        if len(occs_j) > capacite(j):
            alertes.append({
                "date":      j.isoformat(),
                "count":     len(occs_j),
                "capacite":  capacite(j),
                "intentions": [{"nom": o["nom"], "demandeur": o["demandeur"]} for o in occs_j],
            })

    return {
        "succes": True,
        "intention": {
            "nom":      nom_final,
            "demandeur": req.demandeur,
            "date":     cible.isoformat(),
            "date_fin": cible_end.isoformat() if cible_end else None,
        },
        "deplacements": deplacements,
        "alertes":      alertes,  # violations résiduelles détectées en étape 6
    }


@app.get("/api/calendrier")
async def api_calendrier(mois: int, annee: int):
    intentions = await fetch_all_intentions()
    map_jour   = build_map_jour(intentions)
    premier    = date(annee, mois, 1)
    dernier    = date(annee + 1, 1, 1) - timedelta(days=1) if mois == 12 \
                 else date(annee, mois + 1, 1) - timedelta(days=1)
    jours = []
    cur   = premier
    while cur <= dernier:
        occs = map_jour.get(cur, [])
        cap  = capacite(cur)
        jours.append({
            "date":      cur.isoformat(),
            "capacite":  cap,
            "count":     len(occs),
            "libre":     len(occs) < cap,
            "violation": len(occs) > cap,
            "intentions": [{
                "nom":      o["nom"],
                "demandeur": o["demandeur"],
                "fixe":     o["fixe"],
                "periode":  o["date_end"] is not None,
            } for o in occs],
        })
        cur += timedelta(days=1)
    return {"mois": mois, "annee": annee, "jours": jours}
