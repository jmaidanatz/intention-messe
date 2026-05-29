"""
Intentions de Messes — Web App
Backend FastAPI. Logique métier conforme au skill intention-messe.
Cache serveur centralisé pour minimiser les appels Notion.
"""

import os
import time
import json
import asyncio
import logging
from pathlib import Path
from datetime import date, timedelta
from functools import lru_cache
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("intentions")

app = FastAPI(title="Intentions de Messes")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Configuration ───────────────────────────────────────────────────────────
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DS_ID = "2d183ba0-7414-8018-ae4d-fee6db4c950d"
NOTION_API   = "https://api.notion.com/v1"
NOTION_VER   = "2022-06-28"
MAX_SEARCH   = 365
CACHE_TTL    = 300           # secondes : durée de vie du cache des intentions

VAPID_PUBLIC_KEY  = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_EMAIL       = os.environ.get("VAPID_EMAIL", "admin@example.com")


# ══════════════════════════════════════════════════════════════════════════════
# CACHE SERVEUR
# ══════════════════════════════════════════════════════════════════════════════
class IntentionsCache:
    """Cache en mémoire des intentions, avec TTL et invalidation manuelle.
    Évite de recharger Notion à chaque requête calendrier."""
    def __init__(self, ttl: int = CACHE_TTL):
        self._data: Optional[list[dict]] = None
        self._ts: float = 0.0
        self._ttl = ttl
        self._lock = asyncio.Lock()

    def invalider(self):
        self._data = None
        self._ts = 0.0

    def est_valide(self) -> bool:
        return self._data is not None and (time.time() - self._ts) < self._ttl

    async def get(self, forcer: bool = False) -> list[dict]:
        # Double-checked locking pour éviter les requêtes concurrentes multiples
        if not forcer and self.est_valide():
            return self._data
        async with self._lock:
            if not forcer and self.est_valide():
                return self._data
            data = await _fetch_all_intentions_notion()
            self._data = data
            self._ts = time.time()
            return data


cache_intentions = IntentionsCache()


# ── Helpers Notion ────────────────────────────────────────────────────────────
def notion_headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VER,
        "Content-Type": "application/json",
    }


async def _fetch_all_intentions_notion() -> list[dict]:
    """Charge TOUTES les intentions depuis Notion (paginé). Usage interne — passez par le cache."""
    if not NOTION_TOKEN:
        raise HTTPException(500, "NOTION_TOKEN absent. Vérifiez les variables d'environnement.")
    results: list[dict] = []
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
                headers=notion_headers(), json=body,
            )
            if not r.is_success:
                raise HTTPException(502, f"Notion API {r.status_code} : {r.text[:300]}")
            data = r.json()
            for page in data.get("results", []):
                props = page.get("properties", {})
                nom = "".join(t.get("plain_text", "") for t in props.get("Nom", {}).get("title", []))
                date_prop = (props.get("Date") or {}).get("date") or {}
                demandeur = "".join(t.get("plain_text", "") for t in props.get("Demandeur", {}).get("rich_text", []))
                description = "".join(t.get("plain_text", "") for t in props.get("Description", {}).get("rich_text", []))
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
    logger.info("Notion: %d intentions chargées", len(results))
    return results


async def fetch_all_intentions(forcer: bool = False) -> list[dict]:
    """Point d'accès unique : passe par le cache serveur."""
    return await cache_intentions.get(forcer=forcer)


async def notion_create(nom: str, demandeur: str, description: str,
                        d: date, d_end: Optional[date] = None) -> dict:
    date_val: dict = {"start": d.isoformat()}
    if d_end:
        date_val["end"] = d_end.isoformat()
    props: dict = {
        "Nom":  {"title": [{"text": {"content": nom}}]},
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
        if not r.is_success:
            raise HTTPException(502, f"Notion create {r.status_code} : {r.text[:300]}")
        cache_intentions.invalider()   # données modifiées → cache obsolète
        return r.json()


async def notion_update_date(page_id: str, new_start: date,
                             new_end: Optional[date] = None) -> None:
    date_val: dict = {"start": new_start.isoformat(), "end": new_end.isoformat() if new_end else None}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.patch(
            f"{NOTION_API}/pages/{page_id}",
            headers=notion_headers(),
            json={"properties": {"Date": {"date": date_val}}},
        )
        if not r.is_success:
            raise HTTPException(502, f"Notion update {r.status_code} : {r.text[:300]}")
        cache_intentions.invalider()


# ══════════════════════════════════════════════════════════════════════════════
# LOGIQUE MÉTIER
# ══════════════════════════════════════════════════════════════════════════════
@lru_cache(maxsize=64)
def paques(year: int) -> date:
    """Date de Pâques (Butcher). Mise en cache par année."""
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


@lru_cache(maxsize=64)
def ascension(year: int) -> date:
    return paques(year) + timedelta(days=39)


@lru_cache(maxsize=4096)
def capacite(jour: date) -> int:
    """Capacité d'un jour. Mise en cache (jour → capacité ne change jamais)."""
    if jour.month in (7, 8):               return 1   # juillet-août
    if (jour.month, jour.day) == (12, 25): return 3   # Noël
    if (jour.month, jour.day) == (11, 2):  return 3   # Commémoration des défunts
    if (jour.month, jour.day) == (11, 1):  return 2   # Toussaint
    if jour == ascension(jour.year):       return 2   # Ascension
    if jour.weekday() == 6:                return 2   # Dimanche
    return 1


def build_map_jour(intentions: list[dict]) -> dict[date, list[dict]]:
    m: dict[date, list[dict]] = {}
    for intention in intentions:
        cur = intention["date_start"]
        end = intention["date_end"] or cur
        while cur <= end:
            m.setdefault(cur, []).append(intention)
            cur += timedelta(days=1)
    return m


def est_inamovible(intention: dict, today: date) -> bool:
    d_end = intention["date_end"] or intention["date_start"]
    return intention["date_start"] <= today <= d_end


def est_libre(jour: date, map_jour: dict) -> bool:
    return len(map_jour.get(jour, [])) < capacite(jour)


def trouver_date_libre(depuis: date, map_jour: dict, duree: int = 1) -> Optional[date]:
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
                "date":       jour.isoformat(),
                "capacite":   capacite(jour),
                "count":      len(occs),
                "intentions": [{"nom": o["nom"], "demandeur": o["demandeur"]} for o in occs],
            })
    return sorted(viol, key=lambda v: v["date"])


def serialise_jour(cur: date, map_jour: dict) -> dict:
    occs = map_jour.get(cur, [])
    cap  = capacite(cur)
    return {
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
    }


# ── Modèles ─────────────────────────────────────────────────────────────────
class InsertionRequest(BaseModel):
    nom:            str
    demandeur:      Optional[str] = None
    description:    Optional[str] = None
    date_souhaitee: Optional[str] = None
    date_fin:       Optional[str] = None
    force_date:     bool = False


class DateLibreRequest(BaseModel):
    depuis: str
    duree:  int = 1


class PushSubscription(BaseModel):
    endpoint:       str
    keys:           dict
    expirationTime: Optional[float] = None


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES — PAGES
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
async def index():
    # Aucune variable Jinja dans le HTML : on sert le fichier directement.
    return FileResponse("templates/index.html", media_type="text/html")


@app.get("/sw.js")
async def service_worker():
    return FileResponse("static/sw.js", media_type="application/javascript")


@app.get("/manifest.json")
async def manifest():
    return FileResponse("static/manifest.json", media_type="application/manifest+json")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES — DIAGNOSTIC
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/diagnostic")
async def diagnostic():
    token_ok = bool(NOTION_TOKEN)
    result: dict = {
        "token_present":         token_ok,
        "token_prefix":          NOTION_TOKEN[:12] + "..." if token_ok else None,
        "database_id":           NOTION_DS_ID,
        "cache_valide":          cache_intentions.est_valide(),
        "vapid_public_present":  bool(VAPID_PUBLIC_KEY),
        "vapid_public_prefix":   VAPID_PUBLIC_KEY[:12] + "..." if VAPID_PUBLIC_KEY else None,
        "vapid_private_present": bool(VAPID_PRIVATE_KEY),
        "vapid_email":           VAPID_EMAIL,
        "env_vars_vapid":        {k: v[:8] + "..." for k, v in os.environ.items() if "VAPID" in k},
    }
    if not token_ok:
        result["erreur"] = "NOTION_TOKEN absent"
        return result
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{NOTION_API}/databases/{NOTION_DS_ID}", headers=notion_headers())
            result["status_http"] = r.status_code
            if r.status_code == 200:
                data = r.json()
                result["database_title"] = "".join(t.get("plain_text", "") for t in data.get("title", []))
                result["proprietes"] = {k: v.get("type") for k, v in data.get("properties", {}).items()}
            else:
                result["erreur_notion"] = r.text[:300]
    except Exception as e:
        result["exception"] = str(e)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES — DONNÉES
# ══════════════════════════════════════════════════════════════════════════════
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


@app.get("/api/calendrier")
async def api_calendrier(mois: int, annee: int, forcer: bool = False):
    """Un mois. Utilise le cache serveur (pas de rechargement Notion sauf si expiré)."""
    intentions = await fetch_all_intentions(forcer=forcer)
    map_jour   = build_map_jour(intentions)
    premier    = date(annee, mois, 1)
    dernier    = (date(annee + 1, 1, 1) if mois == 12 else date(annee, mois + 1, 1)) - timedelta(days=1)
    jours = []
    cur = premier
    while cur <= dernier:
        jours.append(serialise_jour(cur, map_jour))
        cur += timedelta(days=1)
    return {"mois": mois, "annee": annee, "jours": jours}


@app.get("/api/calendrier-plage")
async def api_calendrier_plage(forcer: bool = False):
    """Retourne TOUS les mois de -3 à +11 en UN SEUL appel.
    Le cache serveur fait qu'un seul chargement Notion est nécessaire."""
    intentions = await fetch_all_intentions(forcer=forcer)
    map_jour   = build_map_jour(intentions)
    today = date.today()
    mois_data = {}
    for dm in range(-3, 12):
        m = today.month + dm
        y = today.year
        while m > 12: m -= 12; y += 1
        while m < 1:  m += 12; y -= 1
        cle = f"{y}-{m:02d}"
        premier = date(y, m, 1)
        dernier = (date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)) - timedelta(days=1)
        jours = []
        cur = premier
        while cur <= dernier:
            jours.append(serialise_jour(cur, map_jour))
            cur += timedelta(days=1)
        mois_data[cle] = jours
    return {"mois": mois_data, "genere": today.isoformat()}


@app.post("/api/date-libre")
async def api_date_libre(req: DateLibreRequest):
    try:
        depuis = date.fromisoformat(req.depuis)
    except ValueError:
        raise HTTPException(400, "Format de date invalide (attendu YYYY-MM-DD).")
    if req.duree < 1 or req.duree > 31:
        raise HTTPException(400, "La durée doit être comprise entre 1 et 31 jours.")
    intentions = await fetch_all_intentions()
    map_jour   = build_map_jour(intentions)
    result     = trouver_date_libre(depuis, map_jour, req.duree)
    if result is None:
        raise HTTPException(404, "Aucune date libre dans les 365 prochains jours.")
    occupants = map_jour.get(result, [])
    return {
        "date":      result.isoformat(),
        "capacite":  capacite(result),
        "intentions_existantes": [{"nom": o["nom"], "demandeur": o["demandeur"]} for o in occupants],
    }


@app.get("/api/violations")
async def api_violations():
    return detect_violations(await fetch_all_intentions())


@app.post("/api/inserer")
async def api_inserer(req: InsertionRequest):
    today = date.today()

    # Validation entrée
    nom = (req.nom or "").strip()
    if not nom:
        raise HTTPException(400, "Le nom de l'intention est requis.")

    # Normalisation RIP
    mots_rip = ["rip", "défunt", "défunte", "repos", "suffrage", "trentain", "décès"]
    if any(m in nom.lower() for m in mots_rip) and not nom.lower().startswith("rip"):
        nom = f"RIP - {nom}"

    # 1. État (cache)
    intentions = await fetch_all_intentions()
    map_jour   = build_map_jour(intentions)

    # Date cible
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

    # Date de fin (période)
    cible_end: Optional[date] = None
    if req.date_fin:
        try:
            cible_end = date.fromisoformat(req.date_fin)
        except ValueError:
            raise HTTPException(400, "Format de date_fin invalide.")
        if cible_end < cible:
            raise HTTPException(400, "La date de fin est antérieure à la date de début.")
    duree_bloc = (cible_end - cible).days + 1 if cible_end else 1

    # 2. Date passée
    if cible < today and not req.force_date:
        return JSONResponse(status_code=409, content={
            "code": "DATE_PASSEE",
            "message": f"La date {cible.isoformat()} est dans le passé. Confirmez-vous l'insertion ?",
            "date": cible.isoformat(),
        })

    # 3. Déplacements
    occupants_bloc: list[dict] = []
    for offset in range(duree_bloc):
        j = cible + timedelta(days=offset)
        for occ in map_jour.get(j, []):
            if occ not in occupants_bloc:
                occupants_bloc.append(occ)

    # Blocage si un jour est saturé d'inamovibles/♦
    for offset in range(duree_bloc):
        j = cible + timedelta(days=offset)
        inamo_j = [o for o in map_jour.get(j, []) if o["fixe"] or est_inamovible(o, today)]
        if len(inamo_j) >= capacite(j):
            return JSONResponse(status_code=409, content={
                "code": "JOUR_BLOQUE",
                "message": f"Le {j.isoformat()} est saturé par des intentions fixes ou inamovibles.",
                "occupants": [{"nom": o["nom"], "demandeur": o["demandeur"]} for o in inamo_j],
            })

    # Quels sans-♦ déplacer
    a_deplacer: list[dict] = []
    for offset in range(duree_bloc):
        j = cible + timedelta(days=offset)
        cap = capacite(j)
        occs_j      = map_jour.get(j, [])
        inamo_j     = [o for o in occs_j if o["fixe"] or est_inamovible(o, today)]
        sans_fixe_j = [o for o in occs_j if not o["fixe"] and not est_inamovible(o, today)]
        places_libres = cap - len(inamo_j) - 1
        if places_libres < 0:
            return JSONResponse(status_code=409, content={
                "code": "JOUR_BLOQUE",
                "message": f"Le {j.isoformat()} est saturé.",
                "occupants": [],
            })
        sans_fixe_sorted = sorted(sans_fixe_j, key=lambda o: (o["date_start"], o["id"]), reverse=True)
        nb = len(sans_fixe_j) - places_libres
        for o in sans_fixe_sorted[:nb]:
            if o not in a_deplacer:
                a_deplacer.append(o)

    if len(a_deplacer) > 3 and not req.force_date:
        return JSONResponse(status_code=409, content={
            "code": "TROP_DEPLACEMENTS",
            "message": f"{len(a_deplacer)} intentions seraient déplacées. Confirmez-vous ?",
            "intentions": [{"nom": o["nom"], "demandeur": o["demandeur"], "date": o["date_start"].isoformat()} for o in a_deplacer],
        })

    # 4. Déplacer (ordre chronologique de date_start)
    a_deplacer_sorted = sorted(a_deplacer, key=lambda o: (o["date_start"], o["id"]))
    deplacements = []
    dernier_bloc = cible_end if cible_end else cible
    for intention in a_deplacer_sorted:
        intentions_fresh = await fetch_all_intentions(forcer=True)
        map_fresh = build_map_jour(intentions_fresh)
        duree_int = (intention["date_end"] - intention["date_start"]).days + 1 if intention["date_end"] else 1
        d_from = max(intention["date_start"] + timedelta(days=1), dernier_bloc + timedelta(days=1))
        nouvelle_date = trouver_date_libre(d_from, map_fresh, duree_int)
        if nouvelle_date is None:
            raise HTTPException(500, f"Impossible de replacer « {intention['nom']} » dans les 365 jours.")
        new_end = (nouvelle_date + timedelta(days=duree_int - 1)) if duree_int > 1 else None
        await notion_update_date(intention["id"], nouvelle_date, new_end)
        deplacements.append({
            "nom": intention["nom"], "demandeur": intention["demandeur"],
            "ancienne_date": intention["date_start"].isoformat(),
            "nouvelle_date": nouvelle_date.isoformat(),
        })

    # 5. Créer
    nom_final = nom
    if duree_bloc == 9:
        nom_final = f"{nom_final} 9️⃣"
    elif duree_bloc == 30:
        nom_final = f"{nom_final} 🪦"
    if date_precise and not nom_final.rstrip("️⃣🪦 ").endswith("♦"):
        nom_final = f"{nom_final} ♦"
    await notion_create(nom_final, req.demandeur or "", req.description or "", cible, cible_end)

    # 6. Vérification finale
    intentions_final = await fetch_all_intentions(forcer=True)
    map_final = build_map_jour(intentions_final)
    jours_verif: set[date] = set()
    for offset in range(duree_bloc):
        jours_verif.add(cible + timedelta(days=offset))
    for dep in deplacements:
        jours_verif.add(date.fromisoformat(dep["ancienne_date"]))
        jours_verif.add(date.fromisoformat(dep["nouvelle_date"]))
    alertes = []
    for j in sorted(jours_verif):
        occs_j = map_final.get(j, [])
        if len(occs_j) > capacite(j):
            alertes.append({
                "date": j.isoformat(), "count": len(occs_j), "capacite": capacite(j),
                "intentions": [{"nom": o["nom"], "demandeur": o["demandeur"]} for o in occs_j],
            })

    return {
        "succes": True,
        "intention": {
            "nom": nom_final, "demandeur": req.demandeur,
            "date": cible.isoformat(),
            "date_fin": cible_end.isoformat() if cible_end else None,
        },
        "deplacements": deplacements,
        "alertes": alertes,
    }


@app.post("/api/rafraichir")
async def api_rafraichir():
    """Force le rechargement du cache depuis Notion."""
    await fetch_all_intentions(forcer=True)
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS PUSH
# ══════════════════════════════════════════════════════════════════════════════
from pywebpush import webpush, WebPushException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

DATA_DIR = Path("data")
SUB_FILE = DATA_DIR / "subscription.json"
DATA_DIR.mkdir(exist_ok=True)
PARIS = pytz.timezone("Europe/Paris")
MOIS_ABBR = ['jan.','fév.','mar.','avr.','mai','juin','juil.','août','sep.','oct.','nov.','déc.']


def lire_subscription() -> Optional[dict]:
    if SUB_FILE.exists():
        try:
            return json.loads(SUB_FILE.read_text())
        except Exception:
            return None
    return None


def sauver_subscription(sub: dict) -> None:
    SUB_FILE.write_text(json.dumps(sub, ensure_ascii=False, indent=2))


def supprimer_subscription() -> None:
    if SUB_FILE.exists():
        SUB_FILE.unlink()


def envoyer_notification(subscription: dict, titre: str, corps: str) -> bool:
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        logger.warning("VAPID absentes — pas d'envoi")
        return False
    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps({"title": titre, "body": corps,
                             "icon": "/static/icon-192.png", "badge": "/static/icon-192.png"}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{VAPID_EMAIL}"},
        )
        return True
    except WebPushException as e:
        logger.error("Push error: %s", e)
        if e.response and e.response.status_code in (404, 410):
            supprimer_subscription()
        return False
    except Exception as e:
        logger.error("Push unexpected: %s", e)
        return False


def _texte_intentions_du_jour(occs: list[dict], jour: date) -> tuple[str, str]:
    date_str = f"{jour.day} {MOIS_ABBR[jour.month - 1]} {jour.year}"
    if not occs:
        return f"Intentions — {date_str}", "Aucune intention de Messe aujourd'hui."
    titre = f"{len(occs)} intention{'s' if len(occs) > 1 else ''} — {date_str}"
    corps = "\n".join(f"• {o['nom']}" + (f" ({o['demandeur']})" if o['demandeur'] else "") for o in occs)
    return titre, corps


async def tache_notification_matin():
    sub = lire_subscription()
    if not sub:
        return
    aujourd = date.today()
    try:
        intentions = await fetch_all_intentions(forcer=True)
    except Exception as e:
        logger.error("Notif: Notion KO: %s", e)
        return
    occs = build_map_jour(intentions).get(aujourd, [])
    titre, corps = _texte_intentions_du_jour(occs, aujourd)
    envoyer_notification(sub, titre, corps)


scheduler = AsyncIOScheduler(timezone=PARIS)
scheduler.add_job(tache_notification_matin, trigger="cron", hour=6, minute=45,
                  id="notif_matin", replace_existing=True)


@app.on_event("startup")
async def _startup():
    try:
        scheduler.start()
        logger.info("Scheduler démarré (6h45 Europe/Paris)")
    except Exception as e:
        logger.error("Scheduler KO: %s", e)


@app.on_event("shutdown")
async def _shutdown():
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        pass


@app.get("/api/push/vapid-public-key")
async def get_vapid_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(503, "VAPID_PUBLIC_KEY absente. Voir /api/push/generer-vapid.")
    return {"publicKey": VAPID_PUBLIC_KEY}


@app.get("/api/push/generer-vapid")
async def generer_vapid():
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    import base64
    key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    pub = key.public_key()
    def b64url(data): return base64.urlsafe_b64encode(data).rstrip(b"=").decode()
    public_key  = b64url(pub.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint))
    private_key = b64url(key.private_numbers().private_value.to_bytes(32, "big"))
    html = """<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><title>Cles VAPID</title>
<style>body{font-family:monospace;max-width:700px;margin:3rem auto;padding:1rem;background:#faf8f4;color:#1a1410}
h1{font-family:serif;font-size:1.4rem;margin-bottom:1.5rem}
.card{background:#fff;border:1px solid #ddd5c8;border-radius:4px;padding:1.2rem 1.4rem;margin-bottom:1rem}
.label{font-size:.75rem;font-weight:600;color:#6b5f52;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.4rem}
.key{word-break:break-all;font-size:.82rem;background:#f2ede4;padding:.6rem .8rem;border-radius:3px;cursor:pointer;border:1px solid #ddd5c8}
.key:hover{background:#e8e0d0}.note{font-size:.82rem;color:#a39787;margin-top:1.5rem;line-height:1.6}.warn{color:#9b2335;font-weight:600}
</style></head><body><h1>Cles VAPID generees</h1>
<p style="font-size:.85rem;color:#6b5f52;margin-bottom:1.5rem">Cliquez pour copier, collez dans Railway Variables.</p>
<div class="card"><div class="label">VAPID_PUBLIC_KEY</div>
<div class="key" onclick="navigator.clipboard.writeText(this.innerText);this.style.background=\'#d4edda\'">""" + public_key + """</div></div>
<div class="card"><div class="label">VAPID_PRIVATE_KEY</div>
<div class="key" onclick="navigator.clipboard.writeText(this.innerText);this.style.background=\'#d4edda\'">""" + private_key + """</div></div>
<div class="note"><span class="warn">Valables uniquement pour cette generation.</span><br>
Apres ajout dans Railway, cliquez sur Redeploy.</div></body></html>"""
    return HTMLResponse(html)


@app.post("/api/push/subscribe")
async def push_subscribe(sub: PushSubscription):
    sauver_subscription({"endpoint": sub.endpoint, "keys": sub.keys, "expirationTime": sub.expirationTime})
    return {"ok": True}


@app.delete("/api/push/subscribe")
async def push_unsubscribe():
    supprimer_subscription()
    return {"ok": True}


@app.get("/api/push/status")
async def push_status():
    sub = lire_subscription()
    return {"actif": sub is not None}


@app.post("/api/push/test")
async def push_test():
    sub = lire_subscription()
    if not sub:
        raise HTTPException(400, "Aucun abonnement enregistré.")
    aujourd = date.today()
    try:
        occs = build_map_jour(await fetch_all_intentions()).get(aujourd, [])
    except Exception:
        occs = []
    titre, corps = _texte_intentions_du_jour(occs, aujourd)
    if not envoyer_notification(sub, titre, corps):
        raise HTTPException(500, "Échec de l'envoi. Vérifiez les clés VAPID.")
    return {"ok": True}
