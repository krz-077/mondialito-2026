# Mondialito 2026

Gioco di pronostici tra amici per il Mondiale FIFA 2026.

## Indice

- [Architettura](#architettura)
- [Business Logic](#business-logic)
- [API Endpoints](#api-endpoints)
- [Modello Dati](#modello-dati)
- [Setup Locale](#setup-locale)
- [Deploy](#deploy)
- [Multi-istanza](#multi-istanza)

---

## Architettura

```
┌─────────────────────────────────────────────────────┐
│                    Frontend                          │
│         HTML/CSS/JS (Jinja2 template)                │
│         templates/index.html                         │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP/JSON
┌─────────────────────▼───────────────────────────────┐
│                   Backend (Flask)                    │
│                   app.py                             │
│                   models.py                          │
└─────────────────────┬───────────────────────────────┘
                      │ SQLAlchemy
┌─────────────────────▼───────────────────────────────┐
│                      DB                              │
│         SQLite (dev) / PostgreSQL (prod)              │
│         seed.py → Match + User + Config              │
└─────────────────────────────────────────────────────┘
```

### Stack

| Componente | Tecnologia |
|------------|-----------|
| Backend | Python 3, Flask (Jinja2, SQLAlchemy, Werkzeug) |
| Frontend | HTML5, CSS3, JavaScript vanilla (nessun framework) |
| Database | SQLite (dev), PostgreSQL (produzione) |
| Deploy | Render (Web Service + PostgreSQL) |
| API esterna | football-data.org (risultati live) |

### Struttura file

```
mondialito-2026/
├── app.py              # Flask app + routes + business logic
├── models.py           # Modelli SQLAlchemy + regole punteggi
├── seed.py             # Popola database (partite + admin)
├── requirements.txt    # Dipendenze Python
├── Procfile            # Comando start per Render
├── render.yaml         # Blueprint Render (web + database)
├── templates/
│   └── index.html      # SPA frontend (tutto in un file)
├── data/               # Database SQLite (dev, gitignorato)
├── venv/               # Virtual environment (gitignorato)
└── README.md
```

---

## Business Logic

### Fasce e Punteggi

48 squadre divise in 6 fasce da 8 squadre ciascuna, in base al ranking FIFA. Il punteggio è inversamente proporzionale alla forza: più la fascia è alta, più punti vale.

| Fascia | Esempio squadre | Vittoria | Pareggio |
|--------|----------------|----------|----------|
| I° | Francia, Argentina, Brasile | 2 pt | 1 pt |
| II° | Uruguay, Colombia, Croazia | 4 pt | 2 pt |
| III° | Ecuador, Senegal, Giappone | 6 pt | 3 pt |
| IV° | Paraguay, Canada, Australia | 8 pt | 4 pt |
| V° | Bosnia, Scozia, Ghana | 10 pt | 5 pt |
| VI° | Sudafrica, Uzbekistan, RD del Congo | 12 pt | 6 pt |

**Sconfitta = 0 pt** per tutte le fasce.

### Regole

1. Ogni giocatore sceglie **6 squadre** (una per fascia)
2. La scelta viene **bloccata** al salvataggio: non si può più modificare
3. Il punteggio si calcola sui risultati dei **90 minuti regolamentari** (supplementari e rigori esclusi)
4. **Bonus finale**: squadra vincente il Mondiale +10pt, seconda +5pt
5. **Iscrizioni chiuse** automaticamente alla prima partita (11 giugno, ore 21:00 italiane)

### Calcolo Punteggi

```
Per ogni partita:
  Se squadra_scelta vince  → punti_fascia["win"]
  Se squadra_scelta pareggia → punti_fascia["draw"]
  Se squadra_scelta perde  → 0
```

I punteggi vengono calcolati:
- **In automatico** ogni 30 secondi se la classifica live è attiva
- **Manualmente** con il pulsante "Calcola" (admin)

### Multi-istanza

La variabile d'ambiente `INSTANCE` separa i dati di gruppi diversi sullo stesso database. Ogni web service su Render con `INSTANCE` diversa vede solo i propri utenti, partite e configurazioni.

### Live Refresh

Il sistema fetcha risultati live da football-data.org:
1. Ogni 30 secondi il frontend chiama `/api/standings?live=1`
2. Il backend controlla se ci sono partite **iniziate ma senza punteggio**
3. Se sì → chiama l'API esterna e aggiorna i punteggi
4. Se no → risponde subito senza chiamare nulla
5. Quando una partita ha `fullTime` (90' finiti), non viene più fetchata
6. Quando tutte le 72 partite hanno punteggio → **stop definitivo**

---

## Modello Dati

### User
| Campo | Tipo | Note |
|-------|------|------|
| id | Integer | PK |
| instance | String(50) | Multi-istanza |
| name | String(100) | Nome utente (unique per istanza) |
| alias | String(100) | Etichetta visibile in classifica (opzionale) |
| password_hash | String(256) | Hash Werkzeug |
| is_admin | Boolean | Admin flag |
| locked | Boolean | Squadra bloccata |
| disabled | Boolean | Disabilitato (login negato) |

### Selection
| Campo | Tipo | Note |
|-------|------|------|
| id | Integer | PK |
| user_id | Integer | FK → User |
| fascia | Integer | 1-6 |
| team_name | String(100) | Squadra scelta |
| *(instance)* | derivata | Da User |

Unique: (user_id, fascia)

### Match
| Campo | Tipo | Note |
|-------|------|------|
| id | Integer | PK |
| instance | String(50) | Multi-istanza |
| matchday | Integer | 1, 2, 3 |
| home_team | String(100) | Casa |
| away_team | String(100) | Trasferta |
| home_score | Integer/null | Goal casa (null = non giocata) |
| away_score | Integer/null | Goal trasferta |
| date | DateTime | Data/ora italiana |

### Config
| Campo | Tipo | Note |
|-------|------|------|
| id | Integer | PK |
| instance | String(50) | Multi-istanza |
| key | String(100) | Chiave |
| value | String(500) | Valore |

Config note:
- `football_api_key` → API key per risultati live
- `world_cup_winner` → Squadra vincente Mondiale (+10pt)
- `world_cup_runner_up` → Secondo posto (+5pt)

---

## API Endpoints

### Pubblici (no auth)

| Metodo | Path | Descrizione |
|--------|------|-------------|
| GET | `/` | Pagina principale |
| GET | `/api/teams` | Lista fasce e squadre |
| GET | `/api/matchdays` | Giornate disponibili (1, 2, 3) |
| GET | `/api/matches` | Partite (filtro: `?matchday=1`) |
| GET | `/api/standings` | Classifica (filtro: `?matchday=1`, `?live=1`) |
| GET | `/api/standings?live=1` | Classifica + auto-fetch risultati live |
| GET | `/api/registration-status` | Stato iscrizioni (aperte/chiuse) |
| GET | `/api/users/check?name=X` | Verifica esistenza utente |
| POST | `/api/users` | Registrazione (`{name, password}`) |
| POST | `/api/login` | Login (`{name, password}`) |
| GET | `/api/session` | Sessione corrente |

### Autenticati (utente loggato)

| Metodo | Path | Descrizione |
|--------|------|-------------|
| GET | `/api/selections` | Squadre scelte + stato lock |
| POST | `/api/selections` | Salva scelte (`{selections: {1:"Francia", ...}}`) |
| POST | `/api/logout` | Logout |

### Admin only

| Metodo | Path | Descrizione |
|--------|------|-------------|
| GET | `/api/admin/users` | Lista utenti con stato |
| POST | `/api/admin/users/:id/reset-password` | Reset password |
| POST | `/api/admin/users/:id/toggle-disable` | Disabilita/riabilita |
| POST | `/api/admin/users/:id/reset-selections` | Reset squadra |
| POST | `/api/admin/users/:id/set-alias` | Imposta alias (`{alias}`) |
| POST | `/api/matches/update-scores` | Aggiorna punteggio |
| POST | `/api/calculate-matchday` | Calcola punteggi |
| POST | `/api/fetch-results` | Fetch manuale risultati |
| POST | `/api/simulate-results` | Genera risultati casuali (test) |
| GET | `/api/config` | Leggi configurazione |
| POST | `/api/config` | Scrivi configurazione |

---

## Setup Locale

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
# Apri http://localhost:5000
```

### Test live refresh (senza API esterna)

```bash
LIVE_TEST_MODE=1 python app.py
```

Simula 2 partite che terminano ogni 30 secondi con punteggi casuali.

### Accesso admin

| User | Password |
|------|----------|
| `admin` | `nicolamerola29` |

---

## Deploy

### Render (consigliato)

1. Push su GitHub
2. Render → **New +** → **Web Service** (o **Blueprint**)
3. **Build Command**: `pip install -r requirements.txt && python seed.py`
4. **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
5. Aggiungi **Environment Variables**:
   - `DATABASE_URL` → PostgreSQL connection string (da Render Database)
   - `INSTANCE` → `default` (o nome gruppo)

### Render Blueprint (automatico)

Il file `render.yaml` definisce web service + database PostgreSQL. Crea un Blueprint su Render e tutto viene configurato automaticamente.

---

## Multi-istanza

Per creare più gruppi di amici sullo stesso database:

1. Crea un secondo **Web Service** su Render
2. Usa lo **stesso database** PostgreSQL (stessa `DATABASE_URL`)
3. Imposta `INSTANCE` diversa per ogni web service (es. `amici1`, `amici2`)
4. Ogni istanza ha i propri utenti, partite e punteggi

Per usare database separati, crea un PostgreSQL dedicato per ogni web service.
