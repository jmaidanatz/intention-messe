<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Intentions de Messes</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --fond:       #faf8f4;
    --fond2:      #f2ede4;
    --blanc:      #ffffff;
    --bordeaux:   #6b1a2a;
    --bordeaux2:  #8c2236;
    --or:         #b8903a;
    --texte:      #1a1410;
    --texte2:     #6b5f52;
    --texte3:     #a39787;
    --bordure:    #ddd5c8;
    --vert:       #2d6a4f;
    --rouge:      #9b2335;
    --radius:     4px;
    --shadow:     0 1px 3px rgba(0,0,0,.08), 0 4px 16px rgba(0,0,0,.04);
    --trans:      .18s ease;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--fond);
    color: var(--texte);
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }

  /* ── Header ── */
  header {
    background: var(--blanc);
    border-bottom: 1px solid var(--bordure);
    padding: 0 2.5rem;
    height: 56px;
    display: flex;
    align-items: center;
    gap: 1.4rem;
    position: sticky;
    top: 0;
    z-index: 50;
  }
  .header-croix {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.1rem;
    color: var(--bordeaux);
    font-weight: 300;
  }
  .header-sep {
    width: 1px;
    height: 22px;
    background: var(--bordure);
  }
  header h1 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.25rem;
    font-weight: 500;
    color: var(--texte);
    letter-spacing: .02em;
  }
  .header-badge {
    margin-left: auto;
    font-size: .72rem;
    font-weight: 500;
    color: var(--texte3);
    letter-spacing: .06em;
    text-transform: uppercase;
  }

  /* ── Layout ── */
  .wrap {
    max-width: 1020px;
    margin: 0 auto;
    padding: 2.4rem 2rem;
  }

  /* ── Navigation ── */
  nav {
    display: flex;
    gap: 0;
    margin-bottom: 2.4rem;
    border-bottom: 1.5px solid var(--bordure);
  }
  .nav-btn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    margin-bottom: -1.5px;
    color: var(--texte2);
    font-family: 'DM Sans', sans-serif;
    font-size: .8rem;
    font-weight: 400;
    letter-spacing: .06em;
    text-transform: uppercase;
    padding: .65rem 1.4rem;
    cursor: pointer;
    transition: var(--trans);
  }
  .nav-btn:hover { color: var(--texte); }
  .nav-btn.actif {
    color: var(--bordeaux);
    border-bottom-color: var(--bordeaux);
    font-weight: 500;
  }

  /* ── Sections ── */
  .section { display: none; }
  .section.active { display: block; animation: fadeIn .2s ease; }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }

  /* ── Titre de section ── */
  .titre-section {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.6rem;
    font-weight: 400;
    color: var(--texte);
    margin-bottom: .3rem;
    letter-spacing: .01em;
  }
  .sous-titre {
    font-size: .82rem;
    color: var(--texte3);
    margin-bottom: 1.8rem;
    font-weight: 300;
  }

  /* ── Carte ── */
  .carte {
    background: var(--blanc);
    border: 1px solid var(--bordure);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    padding: 1.8rem;
    margin-bottom: 1.2rem;
  }

  /* ── Formulaire ── */
  .grille { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  @media (max-width: 580px) { .grille { grid-template-columns: 1fr; } }

  .champ { display: flex; flex-direction: column; gap: .4rem; }
  .champ label {
    font-size: .72rem;
    font-weight: 500;
    color: var(--texte2);
    letter-spacing: .07em;
    text-transform: uppercase;
  }
  .champ input, .champ textarea {
    background: var(--fond);
    border: 1px solid var(--bordure);
    border-radius: var(--radius);
    color: var(--texte);
    font-family: 'DM Sans', sans-serif;
    font-size: .92rem;
    padding: .6rem .85rem;
    transition: var(--trans);
    outline: none;
  }
  .champ input:focus, .champ textarea:focus {
    border-color: var(--bordeaux);
    background: var(--blanc);
    box-shadow: 0 0 0 3px rgba(107,26,42,.07);
  }
  .champ textarea { resize: vertical; min-height: 72px; }

  /* ── Boutons ── */
  .btn {
    font-family: 'DM Sans', sans-serif;
    font-size: .78rem;
    font-weight: 500;
    letter-spacing: .07em;
    text-transform: uppercase;
    padding: .6rem 1.6rem;
    border-radius: var(--radius);
    border: none;
    cursor: pointer;
    transition: var(--trans);
    display: inline-flex;
    align-items: center;
    gap: .5rem;
  }
  .btn-bordeaux { background: var(--bordeaux); color: #fff; }
  .btn-bordeaux:hover { background: var(--bordeaux2); }
  .btn-ghost { background: transparent; border: 1px solid var(--bordure); color: var(--texte2); }
  .btn-ghost:hover { border-color: var(--texte2); color: var(--texte); }
  .btn-row { display: flex; gap: .7rem; margin-top: 1.4rem; align-items: center; }

  /* ── Messages ── */
  .message {
    border-radius: var(--radius);
    padding: .85rem 1.1rem;
    margin: 1rem 0;
    font-size: .88rem;
    line-height: 1.55;
    display: none;
  }
  .message.visible { display: block; }
  .message.succes  { background: #edf7f1; border: 1px solid #a8d5bb; color: #1a5c35; }
  .message.erreur  { background: #fdf0f0; border: 1px solid #e8b4b4; color: #7a1c1c; }
  .message.info    { background: #fdf7ee; border: 1px solid #e8d5a8; color: #6b4c1a; }

  /* ── Calendrier ── */
  .nav-mois {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.4rem;
  }
  .nav-mois h2 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.3rem;
    font-weight: 400;
    color: var(--texte);
    min-width: 200px;
    text-align: center;
    letter-spacing: .02em;
  }

  .grille-cal { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; }

  .entete-cal {
    text-align: center;
    font-size: .68rem;
    font-weight: 500;
    color: var(--texte3);
    letter-spacing: .08em;
    text-transform: uppercase;
    padding: .4rem 0;
  }

  .jour-cal {
    background: var(--blanc);
    border: 1px solid var(--bordure);
    border-radius: var(--radius);
    min-height: 78px;
    padding: .4rem .5rem;
    cursor: pointer;
    transition: var(--trans);
    position: relative;
    overflow: hidden;
  }
  .jour-cal:hover { border-color: var(--bordeaux); z-index: 1; }
  .jour-cal.vide { background: transparent; border: none; cursor: default; }
  .jour-cal.aujourd-hui { border-color: var(--bordeaux); }
  .jour-cal.aujourd-hui .num-jour { color: var(--bordeaux); font-weight: 500; }
  .jour-cal.violation { background: #fdf0f0; border-color: #e8b4b4; }

  .num-jour {
    font-family: 'Cormorant Garamond', serif;
    font-size: .95rem;
    font-weight: 400;
    display: block;
    margin-bottom: .15rem;
    color: var(--texte);
  }
  .dot-libre {
    position: absolute;
    top: .4rem;
    right: .45rem;
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--vert);
  }
  .dot-viol {
    position: absolute;
    top: .4rem;
    right: .45rem;
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--rouge);
  }
  .cap-ind {
    position: absolute;
    bottom: .3rem;
    right: .45rem;
    font-size: .6rem;
    color: var(--texte3);
    font-weight: 300;
  }
  .intention-mini {
    font-size: .66rem;
    color: var(--texte2);
    line-height: 1.25;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 1px;
  }
  .intention-mini.fixe { color: var(--or); }

  /* ── Popup ── */
  .popup-overlay {
    position: fixed; inset: 0;
    background: rgba(26,20,16,.45);
    z-index: 200;
    display: none;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(2px);
  }
  .popup-overlay.visible { display: flex; }
  .popup {
    background: var(--blanc);
    border: 1px solid var(--bordure);
    border-radius: 6px;
    padding: 2rem 2.2rem;
    max-width: 460px;
    width: 95%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 8px 40px rgba(0,0,0,.14);
    animation: popIn .18s ease;
  }
  @keyframes popIn { from { opacity:0; transform:scale(.97) translateY(6px); } to { opacity:1; transform:none; } }
  .popup h3 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--texte);
    margin-bottom: 1.2rem;
    padding-bottom: .8rem;
    border-bottom: 1px solid var(--bordure);
  }
  .liste-intentions { list-style: none; }
  .liste-intentions li {
    padding: .6rem 0;
    border-bottom: 1px solid var(--fond2);
    font-size: .88rem;
  }
  .liste-intentions li:last-child { border: none; }
  .nom-int { color: var(--texte); font-weight: 400; }
  .dem-int { color: var(--texte3); font-size: .78rem; display: block; margin-top: .1rem; }
  .badge {
    display: inline-block;
    border-radius: 3px;
    padding: .1rem .35rem;
    font-size: .64rem;
    font-weight: 500;
    letter-spacing: .05em;
    text-transform: uppercase;
    margin-left: .4rem;
    vertical-align: middle;
  }
  .badge-fixe   { background: #fdf7ee; color: var(--or); border: 1px solid #e8d5a8; }
  .badge-periode { background: #edf7f1; color: var(--vert); border: 1px solid #a8d5bb; }

  /* ── Violations ── */
  .violation-item {
    background: #fdf5f5;
    border: 1px solid #e8c4c4;
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    margin-bottom: .8rem;
  }
  .violation-date {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1rem;
    color: var(--rouge);
    margin-bottom: .5rem;
    font-weight: 500;
  }

  /* ── Date libre ── */
  .result-libre {
    background: var(--blanc);
    border: 1px solid var(--bordure);
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    margin-top: 1rem;
    display: none;
    box-shadow: var(--shadow);
  }
  .result-libre.visible { display: block; }
  .date-libre-val {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2rem;
    font-weight: 300;
    color: var(--texte);
    margin-bottom: .4rem;
    letter-spacing: .01em;
  }

  /* ── Spinner ── */
  .spinner {
    display: inline-block;
    width: 14px; height: 14px;
    border: 1.5px solid var(--bordure);
    border-top-color: var(--bordeaux);
    border-radius: 50%;
    animation: spin .65s linear infinite;
  }
  .spinner.cache { display: none; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Légende calendrier ── */
  .legende {
    display: flex;
    gap: 1.4rem;
    margin-bottom: 1rem;
    font-size: .74rem;
    color: var(--texte3);
    align-items: center;
    flex-wrap: wrap;
  }
  .leg-item { display: flex; align-items: center; gap: .35rem; }
  .leg-dot { width: 7px; height: 7px; border-radius: 50%; }
</style>
</head>
<body>

<header>
  <span class="header-croix">✠</span>
  <div class="header-sep"></div>
  <h1>Intentions de Messes</h1>
  <span class="header-badge">ICRSP · Rennes</span>
</header>

<div class="wrap">

  <nav>
    <button class="nav-btn actif" data-section="inserer">Insérer</button>
    <button class="nav-btn" data-section="calendrier">Calendrier</button>
    <button class="nav-btn" data-section="date-libre">Date libre</button>
    <button class="nav-btn" data-section="violations">Violations</button>
  </nav>

  <!-- ── INSÉRER ── -->
  <div class="section active" id="inserer">
    <div class="titre-section">Nouvelle intention</div>
    <p class="sous-titre">Le ♦ est ajouté automatiquement si une date précise est fournie. Le déplacement des intentions sans ♦ est géré automatiquement.</p>
    <div class="carte">
      <form id="form-insertion">
        <div class="grille">
          <div class="champ" style="grid-column:1/-1">
            <label>Nom de l'intention *</label>
            <input type="text" id="nom" placeholder="ex. RIP — Jean Dupont  ou  Guérison de Marie" required>
          </div>
          <div class="champ">
            <label>Demandeur</label>
            <input type="text" id="demandeur" placeholder="ex. Mme Martin">
          </div>
          <div class="champ">
            <label>Date souhaitée <span style="font-weight:300;text-transform:none;letter-spacing:0">(vide = prochaine date libre)</span></label>
            <input type="date" id="date_souhaitee">
          </div>
          <div class="champ" style="grid-column:1/-1">
            <label>Note</label>
            <textarea id="description" placeholder="Précision contextuelle…"></textarea>
          </div>
        </div>
        <div class="btn-row">
          <button type="submit" class="btn btn-bordeaux">Insérer l'intention</button>
          <span class="spinner cache" id="spin-inserer"></span>
        </div>
      </form>
    </div>
    <div class="message" id="msg-inserer"></div>
  </div>

  <!-- ── CALENDRIER ── -->
  <div class="section" id="calendrier">
    <div class="nav-mois">
      <button class="btn btn-ghost" id="mois-prev">←</button>
      <h2 id="titre-mois">…</h2>
      <button class="btn btn-ghost" id="mois-next">→</button>
      <span class="spinner cache" id="spin-cal"></span>
    </div>
    <div class="legende">
      <span class="leg-item"><span class="leg-dot" style="background:var(--vert)"></span>Libre</span>
      <span class="leg-item"><span class="leg-dot" style="background:var(--rouge)"></span>Violation</span>
      <span class="leg-item"><span style="font-size:.8rem;color:var(--bordeaux)">✠</span>Aujourd'hui</span>
    </div>
    <div class="grille-cal" id="grille-cal"></div>
  </div>

  <!-- ── DATE LIBRE ── -->
  <div class="section" id="date-libre">
    <div class="titre-section">Prochaine date libre</div>
    <p class="sous-titre">Cherche la première date disponible après la date indiquée, en tenant compte des périodes et des ♦.</p>
    <div class="carte">
      <div class="grille">
        <div class="champ">
          <label>À partir de</label>
          <input type="date" id="dl-depuis">
        </div>
        <div class="champ">
          <label>Durée en jours <span style="font-weight:300;text-transform:none;letter-spacing:0">(1, 9, 30…)</span></label>
          <input type="number" id="dl-duree" value="1" min="1" max="30">
        </div>
      </div>
      <div class="btn-row">
        <button class="btn btn-bordeaux" id="btn-dl">Chercher</button>
        <span class="spinner cache" id="spin-dl"></span>
      </div>
    </div>
    <div class="result-libre" id="result-libre"></div>
  </div>

  <!-- ── VIOLATIONS ── -->
  <div class="section" id="violations">
    <div class="titre-section">Violations de capacité</div>
    <p class="sous-titre">Détecte tous les jours où le nombre d'intentions dépasse la capacité autorisée.</p>
    <div class="btn-row" style="margin-bottom:1.4rem">
      <button class="btn btn-bordeaux" id="btn-violations">Analyser la base</button>
      <span class="spinner cache" id="spin-viol"></span>
    </div>
    <div id="liste-violations"></div>
  </div>

</div>

<!-- ── POPUP JOUR ── -->
<div class="popup-overlay" id="popup-overlay">
  <div class="popup">
    <h3 id="popup-titre">—</h3>
    <ul class="liste-intentions" id="popup-intentions"></ul>
    <div class="btn-row" style="margin-top:1.2rem">
      <button class="btn btn-ghost" onclick="fermerPopup()">Fermer</button>
    </div>
  </div>
</div>

<!-- ── POPUP CONFIRMATION ── -->
<div class="popup-overlay" id="popup-confirm">
  <div class="popup">
    <h3 id="confirm-titre">Confirmation requise</h3>
    <div id="confirm-body" style="font-size:.9rem;color:var(--texte2);line-height:1.65;margin-bottom:.8rem"></div>
    <div class="btn-row">
      <button class="btn btn-bordeaux" id="confirm-ok">Confirmer</button>
      <button class="btn btn-ghost" onclick="fermerConfirm()">Annuler</button>
    </div>
  </div>
</div>

<script>
const MOIS_FR = ['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre'];
let calMois = new Date().getMonth() + 1;
let calAnnee = new Date().getFullYear();

// ── Onglets ────────────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('actif'));
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    btn.classList.add('actif');
    document.getElementById(btn.dataset.section).classList.add('active');
    if (btn.dataset.section === 'calendrier') chargerCal();
  });
});

// ── Formulaire insertion ───────────────────────────────────────────────────────
document.getElementById('form-insertion').addEventListener('submit', async e => {
  e.preventDefault();
  await soumettreForme(false);
});

async function soumettreForme(force = false) {
  const spin = document.getElementById('spin-inserer');
  const msg  = document.getElementById('msg-inserer');
  spin.classList.remove('cache');
  msg.className = 'message';

  const body = {
    nom: document.getElementById('nom').value.trim(),
    demandeur: document.getElementById('demandeur').value.trim(),
    description: document.getElementById('description').value.trim(),
    date_souhaitee: document.getElementById('date_souhaitee').value || null,
    force_date: force,
  };

  try {
    const r = await fetch('/api/inserer', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    const data = await r.json();

    if (r.status === 409) {
      if (data.code === 'DATE_PASSEE') {
        demanderConfirmation(
          'Date dans le passé',
          `La date <strong>${fmtDate(data.date)}</strong> est dans le passé. Confirmer l'insertion ?`,
          () => soumettreForme(true)
        );
      } else if (data.code === 'TROP_DEPLACEMENTS') {
        const liste = data.intentions.map(i => `<br>• ${i.nom} <span style="color:var(--texte3)">(${fmtDate(i.date)})</span>`).join('');
        demanderConfirmation(
          'Déplacements multiples',
          `${data.intentions.length} intentions seront déplacées :${liste}<br><br>Confirmer ?`,
          () => soumettreForme(true)
        );
      } else {
        afficherMsg('erreur', data.message || 'Erreur inconnue', 'msg-inserer');
      }
      return;
    }
    if (!r.ok) { afficherMsg('erreur', data.detail || 'Erreur serveur', 'msg-inserer'); return; }

    let html = `Intention insérée : <strong>${data.intention.nom}</strong> — ${fmtDate(data.intention.date)}`;
    if (data.deplacements.length) {
      html += '<br><br><span style="font-weight:500">Déplacements effectués :</span>';
      data.deplacements.forEach(d => {
        html += `<br>· <em>${d.nom}</em> : ${fmtDate(d.ancienne_date)} → ${fmtDate(d.nouvelle_date)}`;
      });
    }
    afficherMsg('succes', html, 'msg-inserer');
    document.getElementById('form-insertion').reset();
  } catch(err) {
    afficherMsg('erreur', 'Erreur réseau : ' + err.message, 'msg-inserer');
  } finally {
    spin.classList.add('cache');
  }
}

// ── Calendrier ─────────────────────────────────────────────────────────────────
async function chargerCal() {
  const spin = document.getElementById('spin-cal');
  spin.classList.remove('cache');
  document.getElementById('titre-mois').textContent = `${MOIS_FR[calMois-1]} ${calAnnee}`;
  try {
    const r = await fetch(`/api/calendrier?mois=${calMois}&annee=${calAnnee}`);
    const data = await r.json();
    renderCal(data.jours);
  } catch(e) { console.error(e); }
  finally { spin.classList.add('cache'); }
}

function renderCal(jours) {
  const grille = document.getElementById('grille-cal');
  grille.innerHTML = '';
  ['Lu','Ma','Me','Je','Ve','Sa','Di'].forEach(j => {
    const el = document.createElement('div');
    el.className = 'entete-cal';
    el.textContent = j;
    grille.appendChild(el);
  });

  const aujourd = new Date().toISOString().split('T')[0];
  let decalage = (new Date(jours[0].date + 'T00:00:00').getDay() + 6) % 7;
  for (let i = 0; i < decalage; i++) {
    const v = document.createElement('div');
    v.className = 'jour-cal vide';
    grille.appendChild(v);
  }

  jours.forEach(j => {
    const el = document.createElement('div');
    el.className = 'jour-cal';
    if (j.violation) el.classList.add('violation');
    if (j.date === aujourd) el.classList.add('aujourd-hui');

    const num = document.createElement('span');
    num.className = 'num-jour';
    num.textContent = new Date(j.date + 'T00:00:00').getDate();
    el.appendChild(num);

    if (j.libre && !j.violation) {
      const dot = document.createElement('span');
      dot.className = 'dot-libre';
      el.appendChild(dot);
    }
    if (j.violation) {
      const dot = document.createElement('span');
      dot.className = 'dot-viol';
      el.appendChild(dot);
    }

    j.intentions.slice(0, 2).forEach(int => {
      const d = document.createElement('div');
      d.className = 'intention-mini' + (int.fixe ? ' fixe' : '');
      d.textContent = int.nom.replace(/^RIP - /, '✝ ');
      el.appendChild(d);
    });
    if (j.intentions.length > 2) {
      const plus = document.createElement('div');
      plus.className = 'intention-mini';
      plus.textContent = `+${j.intentions.length - 2} autres`;
      el.appendChild(plus);
    }

    const cap = document.createElement('span');
    cap.className = 'cap-ind';
    cap.textContent = `${j.count}/${j.capacite}`;
    el.appendChild(cap);

    el.addEventListener('click', () => ouvrirPopupJour(j));
    grille.appendChild(el);
  });
}

document.getElementById('mois-prev').addEventListener('click', () => {
  calMois--; if (calMois < 1) { calMois = 12; calAnnee--; } chargerCal();
});
document.getElementById('mois-next').addEventListener('click', () => {
  calMois++; if (calMois > 12) { calMois = 1; calAnnee++; } chargerCal();
});

// ── Popup jour ─────────────────────────────────────────────────────────────────
function ouvrirPopupJour(j) {
  document.getElementById('popup-titre').textContent =
    `${fmtDate(j.date)} — ${j.count} / ${j.capacite}`;
  const ul = document.getElementById('popup-intentions');
  ul.innerHTML = '';
  if (!j.intentions.length) {
    ul.innerHTML = '<li style="color:var(--texte3);font-style:italic;padding:.5rem 0">Aucune intention</li>';
  } else {
    j.intentions.forEach(i => {
      const li = document.createElement('li');
      const fixeBadge   = i.fixe    ? '<span class="badge badge-fixe">♦ fixe</span>'      : '';
      const perioBadge  = i.periode ? '<span class="badge badge-periode">Période</span>'  : '';
      li.innerHTML = `<span class="nom-int">${i.nom}${fixeBadge}${perioBadge}</span><span class="dem-int">${i.demandeur || '—'}</span>`;
      ul.appendChild(li);
    });
  }
  document.getElementById('popup-overlay').classList.add('visible');
}
function fermerPopup() { document.getElementById('popup-overlay').classList.remove('visible'); }
document.getElementById('popup-overlay').addEventListener('click', e => {
  if (e.target === document.getElementById('popup-overlay')) fermerPopup();
});

// ── Date libre ─────────────────────────────────────────────────────────────────
document.getElementById('dl-depuis').value = new Date().toISOString().split('T')[0];

document.getElementById('btn-dl').addEventListener('click', async () => {
  const spin = document.getElementById('spin-dl');
  const result = document.getElementById('result-libre');
  spin.classList.remove('cache');
  result.classList.remove('visible');
  try {
    const r = await fetch('/api/date-libre', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        depuis: document.getElementById('dl-depuis').value,
        duree:  parseInt(document.getElementById('dl-duree').value) || 1,
      }),
    });
    const data = await r.json();
    if (!r.ok) {
      result.innerHTML = `<span style="color:var(--rouge)">${data.detail}</span>`;
    } else {
      let html = `<div class="date-libre-val">${fmtDate(data.date)}</div>`;
      html += `<div style="font-size:.8rem;color:var(--texte3);margin-bottom:.6rem">Capacité : ${data.capacite} — ${data.intentions_existantes.length} intention(s) déjà présente(s)</div>`;
      if (data.intentions_existantes.length) {
        html += '<ul style="list-style:none">';
        data.intentions_existantes.forEach(i => {
          html += `<li style="font-size:.83rem;color:var(--texte2);padding:.2rem 0;border-bottom:1px solid var(--fond2)">· ${i.nom}${i.demandeur ? ' <span style="color:var(--texte3)">(' + i.demandeur + ')</span>' : ''}</li>`;
        });
        html += '</ul>';
      }
      result.innerHTML = html;
    }
    result.classList.add('visible');
  } catch(e) {
    result.innerHTML = `<span style="color:var(--rouge)">Erreur : ${e.message}</span>`;
    result.classList.add('visible');
  } finally { spin.classList.add('cache'); }
});

// ── Violations ─────────────────────────────────────────────────────────────────
document.getElementById('btn-violations').addEventListener('click', async () => {
  const spin = document.getElementById('spin-viol');
  const liste = document.getElementById('liste-violations');
  spin.classList.remove('cache');
  liste.innerHTML = '';
  try {
    const r = await fetch('/api/violations');
    const data = await r.json();
    if (!data.length) {
      liste.innerHTML = '<div class="message info visible">Aucune violation détectée dans la base.</div>';
    } else {
      data.forEach(v => {
        const div = document.createElement('div');
        div.className = 'violation-item';
        let html = `<div class="violation-date">${fmtDate(v.date)} — ${v.count} intention(s) · capacité ${v.capacite}</div><ul style="list-style:none">`;
        v.intentions.forEach(i => {
          html += `<li style="font-size:.85rem;color:var(--texte2);padding:.2rem 0">· ${i.nom}${i.demandeur ? ' <span style="color:var(--texte3)">(' + i.demandeur + ')</span>' : ''}</li>`;
        });
        html += '</ul>';
        div.innerHTML = html;
        liste.appendChild(div);
      });
    }
  } catch(e) {
    liste.innerHTML = `<div class="message erreur visible">Erreur : ${e.message}</div>`;
  } finally { spin.classList.add('cache'); }
});

// ── Confirmation ────────────────────────────────────────────────────────────────
let confirmCallback = null;
function demanderConfirmation(titre, body, callback) {
  document.getElementById('confirm-titre').textContent = titre;
  document.getElementById('confirm-body').innerHTML = body;
  confirmCallback = callback;
  document.getElementById('popup-confirm').classList.add('visible');
}
document.getElementById('confirm-ok').addEventListener('click', () => {
  fermerConfirm();
  if (confirmCallback) confirmCallback();
});
function fermerConfirm() {
  document.getElementById('popup-confirm').classList.remove('visible');
  confirmCallback = null;
}

// ── Utilitaires ─────────────────────────────────────────────────────────────────
function fmtDate(iso) {
  const [y, m, d] = iso.split('-');
  return `${parseInt(d)} ${MOIS_FR[parseInt(m)-1]} ${y}`;
}
function afficherMsg(type, html, id) {
  const el = document.getElementById(id);
  el.className = `message ${type} visible`;
  el.innerHTML = html;
}
</script>
</body>
</html>
