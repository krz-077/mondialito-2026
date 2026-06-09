import os
import sys
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for, session
)
from models import db, User, Selection, Match, Config, FASCE, PUNTEGGI, TEAM_FASCIA, get_fascia
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-mondialito")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(os.path.dirname(__file__), "data", "mondialito.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Ensure data directory exists for SQLite
os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)

INSTANCE = os.environ.get("INSTANCE", "default")

with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html", fasce=FASCE, punteggi=PUNTEGGI)


@app.route("/api/users", methods=["GET"])
def get_users():
    users = User.query.filter_by(instance=INSTANCE).all()
    return jsonify([{"id": u.id, "name": u.name} for u in users])


@app.route("/api/users/check", methods=["GET"])
def check_user():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"exists": False}), 400
    user = User.query.filter_by(instance=INSTANCE, name=name).first()
    return jsonify({"exists": user is not None})


@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json()
    name = data.get("name", "").strip()
    password = data.get("password", "").strip()
    if not name:
        return jsonify({"error": "Nome obbligatorio"}), 400
    if not password:
        return jsonify({"error": "Password obbligatoria"}), 400
    if User.query.filter_by(instance=INSTANCE, name=name).first():
        return jsonify({"error": "Utente già esistente"}), 400
    user = User(instance=INSTANCE, name=name, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["is_admin"] = user.is_admin
    return jsonify({"id": user.id, "name": user.name, "is_admin": user.is_admin})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    name = data.get("name", "").strip()
    password = data.get("password", "").strip()
    user = User.query.filter_by(instance=INSTANCE, name=name).first()
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404
    if user.disabled:
        return jsonify({"error": "Utente disabilitato. Contatta l'amministratore."}), 403
    if not user.password_hash or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Password errata"}), 401
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["is_admin"] = user.is_admin
    return jsonify({"id": user.id, "name": user.name, "is_admin": user.is_admin})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/session")
def get_session():
    if "user_id" in session:
        return jsonify({
            "id": session["user_id"],
            "name": session["user_name"],
            "is_admin": session.get("is_admin", False),
        })
    return jsonify(None)


@app.route("/api/selections", methods=["GET", "POST"])
def selections():
    if request.method == "GET":
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Non autenticato"}), 401
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "Utente non trovato"}), 404
        return jsonify({"teams": user.team_by_fascia(), "locked": user.locked})

    data = request.get_json()
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Non autenticato"}), 401

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404
    if user.locked:
        return jsonify({"error": "Bloccata! Non puoi più modificare le squadre."}), 403

    selections = data.get("selections", {})
    for fascia_str, team in selections.items():
        fascia = int(fascia_str)
        existing = Selection.query.filter_by(user_id=user_id, fascia=fascia).first()
        if existing:
            existing.team_name = team
        else:
            db.session.add(Selection(user_id=user_id, fascia=fascia, team_name=team))

    if len(selections) == 6:
        user.locked = True

    db.session.commit()
    return jsonify({"ok": True, "locked": user.locked})


@app.route("/api/matches", methods=["GET"])
def get_matches():
    matchday = request.args.get("matchday", type=int)
    query = Match.query.filter_by(instance=INSTANCE)
    if matchday:
        query = query.filter(Match.matchday == matchday)
    matches = query.order_by(Match.matchday, Match.date, Match.id).all()
    return jsonify([
        {
            "id": m.id,
            "matchday": m.matchday,
            "home_team": m.home_team,
            "away_team": m.away_team,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "date": m.date.isoformat() if m.date else None,
        }
        for m in matches
    ])


@app.route("/api/matches", methods=["POST"])
def save_matches():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Non autenticato"}), 401
    user = db.session.get(User, user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Solo l'admin può modificare le partite"}), 403

    data = request.get_json()
    matchday = data.get("matchday", 1)
    matches = data.get("matches", [])

    Match.query.filter_by(instance=INSTANCE, matchday=matchday).delete()
    for m in matches:
        match = Match(
            instance=INSTANCE,
            matchday=matchday,
            home_team=m["home_team"],
            away_team=m["away_team"],
            home_score=m.get("home_score"),
            away_score=m.get("away_score"),
        )
        db.session.add(match)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/matches/update-scores", methods=["POST"])
def update_scores():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Non autenticato"}), 401
    user = db.session.get(User, user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Solo l'admin può modificare i risultati"}), 403

    data = request.get_json()
    match_id = data.get("match_id")
    home_score = data.get("home_score")
    away_score = data.get("away_score")
    match = db.session.get(Match, match_id)
    if not match:
        return jsonify({"error": "Partita non trovata"}), 404
    match.home_score = home_score
    match.away_score = away_score
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/standings")
def get_standings():
    users = User.query.filter_by(instance=INSTANCE).all()
    matchday = request.args.get("matchday", type=int)
    result = []
    for user in users:
        total = 0
        details = {}
        for s in user.selections:
            pts = s.points(matchday)
            total += pts
            details[str(s.fascia)] = {"team": s.team_name, "points": pts}
        result.append({
            "user_id": user.id,
            "name": user.name,
            "total_points": total,
            "details": details,
        })
    result.sort(key=lambda x: x["total_points"], reverse=True)
    return jsonify(result)


@app.route("/api/calculate-matchday", methods=["POST"])
def calculate_matchday():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Non autenticato"}), 401
    user = db.session.get(User, user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Solo l'admin può calcolare i punteggi"}), 403

    data = request.get_json()
    matchday = data.get("matchday")

    standings = []
    users = User.query.filter_by(instance=INSTANCE).all()
    for user in users:
        total = 0
        for s in user.selections:
            total += s.points(matchday)
        standings.append({"user_id": user.id, "name": user.name, "points": total})

    standings.sort(key=lambda x: x["points"], reverse=True)
    return jsonify({"matchday": matchday, "standings": standings})


@app.route("/api/leaderboard")
def full_leaderboard():
    users = User.query.filter_by(instance=INSTANCE).all()
    result = []
    for user in users:
        total = user.points()
        details = {}
        for s in user.selections:
            pts = s.points()
            details[str(s.fascia)] = {"team": s.team_name, "points": pts}
        result.append({
            "user_id": user.id,
            "name": user.name,
            "total_points": total,
            "details": details,
        })
    result.sort(key=lambda x: x["total_points"], reverse=True)
    return jsonify(result)


EN2IT = {
    "Mexico": "Messico", "South Africa": "Sudafrica", "South Korea": "Corea del Sud",
    "Czech Republic": "Repubblica Ceca", "Czechia": "Repubblica Ceca",
    "Canada": "Canada", "Bosnia and Herzegovina": "Bosnia", "Bosnia-Herzegovina": "Bosnia",
    "United States": "Stati Uniti", "USA": "Stati Uniti", "Paraguay": "Paraguay",
    "Haiti": "Haiti", "Scotland": "Scozia", "Australia": "Australia", "Turkey": "Turchia",
    "Brazil": "Brasile", "Morocco": "Marocco", "Qatar": "Qatar", "Switzerland": "Svizzera",
    "Germany": "Germania", "Curaçao": "Curacao", "Ivory Coast": "Costa d'Avorio",
    "Ecuador": "Ecuador", "Netherlands": "Olanda", "Japan": "Giappone", "Sweden": "Svezia",
    "Tunisia": "Tunisia", "Spain": "Spagna", "Cape Verde": "Capo Verde",
    "Cape Verde Islands": "Capo Verde",
    "Saudi Arabia": "Arabia Saudita", "Uruguay": "Uruguay", "Iran": "Iran",
    "New Zealand": "Nuova Zelanda", "Belgium": "Belgio", "Egypt": "Egitto",
    "France": "Francia", "Senegal": "Senegal", "Iraq": "Iraq", "Norway": "Norvegia",
    "Argentina": "Argentina", "Algeria": "Algeria", "Austria": "Austria",
    "Jordan": "Giordania", "Ghana": "Ghana", "Panama": "Panama",
    "England": "Inghilterra", "Croatia": "Croazia", "Portugal": "Portogallo",
    "DR Congo": "RD del Congo", "Congo DR": "RD del Congo",
    "Uzbekistan": "Uzbekistan", "Colombia": "Colombia",
    "Korea Republic": "Corea del Sud", "Korea, Republic of": "Corea del Sud",
}

def norm_api(n):
    if not n:
        return None
    n = n.strip()
    return EN2IT.get(n, n)


@app.route("/api/fetch-results", methods=["POST"])
def fetch_results():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Non autenticato"}), 401
    user = db.session.get(User, user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Solo l'admin"}), 403

    api_key_cfg = Config.query.filter_by(instance=INSTANCE, key="football_api_key").first()
    api_key = api_key_cfg.value if api_key_cfg else None
    if not api_key:
        return jsonify({
            "error": "Nessuna API configurata",
            "instructions": "Vai su https://www.football-data.org/client/register, "
                           "registrati gratis, copia il tuo API key e incollalo nelle impostazioni."
        }), 400

    import requests
    headers = {"X-Auth-Token": api_key}

    # Try competition IDs: 2000 (World Cup generic), then try to search
    comp_ids_cfg = Config.query.filter_by(instance=INSTANCE, key="football_competition_id").first()
    comp_ids = [comp_ids_cfg.value] if comp_ids_cfg and comp_ids_cfg.value else ["2000", "2018", "2001", "2002", "2003"]

    last_error = ""
    updated = 0

    for comp_id in comp_ids:
        try:
            r = requests.get(
                f"https://api.football-data.org/v4/competitions/{comp_id}/matches",
                headers=headers, timeout=10
            )
            if r.status_code == 403:
                return jsonify({"error": "API key non valida. Riguadagnatene una su football-data.org"}), 400
            if r.status_code == 429:
                return jsonify({"error": "Troppe richieste, riprova tra un minuto"}), 400
            if r.status_code == 404:
                last_error = f"Competizione {comp_id} non trovata"
                continue
            if r.status_code != 200:
                last_error = f"Competizione {comp_id}: errore {r.status_code}"
                continue

            data = r.json()
            matches = data.get("matches", [])
            if not matches:
                last_error = f"Competizione {comp_id}: nessuna partita trovata"
                continue

            updated = 0
            for m in matches:
                home_name = m.get("homeTeam", {}).get("name")
                away_name = m.get("awayTeam", {}).get("name")
                if not home_name or not away_name:
                    continue
                home_api = norm_api(home_name)
                away_api = norm_api(away_name)
                score = m.get("score")
                if not score or score.get("fullTime", {}).get("home") is None:
                    continue
                home_goal = score["fullTime"]["home"]
                away_goal = score["fullTime"]["away"]

                match = Match.query.filter_by(instance=INSTANCE, home_team=home_api, away_team=away_api).first()
                if not match:
                    match = Match.query.filter_by(instance=INSTANCE, home_team=away_api, away_team=home_api).first()
                if match:
                    match.home_score = home_goal
                    match.away_score = away_goal
                    updated += 1

            db.session.commit()
            return jsonify({"ok": True, "updated": updated, "total": len(matches), "competition_id": comp_id})

        except requests.exceptions.Timeout:
            last_error = f"Competizione {comp_id}: richiesta scaduta"
            continue
        except requests.exceptions.ConnectionError:
            return jsonify({"error": "Impossibile connettersi a football-data.org. Controlla connessione."}), 400
        except Exception as e:
            last_error = f"Competizione {comp_id}: {str(e)[:80]}"
            continue

    return jsonify({
        "error": f"Nessuna competizione World Cup 2026 trovata. {last_error}",
        "hint": "Prova a impostare un competition ID diverso via API (es. 2000, 2018, 2021, 2022). "
                "Vai su Impostazioni → Imposta ID competizione."
    }), 400


@app.route("/api/config", methods=["GET", "POST"])
def config():
    if request.method == "GET":
        configs = Config.query.filter_by(instance=INSTANCE).all()
        return jsonify({c.key: c.value for c in configs})
    data = request.get_json()
    for key, value in data.items():
        existing = Config.query.filter_by(instance=INSTANCE, key=key).first()
        if existing:
            existing.value = str(value) if value is not None else None
        else:
            db.session.add(Config(instance=INSTANCE, key=key, value=str(value) if value is not None else None))
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/matchdays")
def get_matchdays():
    matchdays = db.session.query(Match.matchday).filter(Match.instance == INSTANCE).distinct().order_by(Match.matchday).all()
    return jsonify([m[0] for m in matchdays])


@app.route("/api/teams")
def get_teams():
    return jsonify(FASCE)


# --- Admin: user management ---

def admin_required():
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if not user or not user.is_admin:
        return None
    return user


@app.route("/api/admin/users", methods=["GET"])
def admin_get_users():
    if not admin_required():
        return jsonify({"error": "Solo admin"}), 403
    users = User.query.filter_by(instance=INSTANCE).order_by(User.name).all()
    return jsonify([{
        "id": u.id,
        "name": u.name,
        "disabled": u.disabled,
        "locked": u.locked,
        "has_selections": len(u.selections) > 0,
    } for u in users])


@app.route("/api/admin/users/<int:user_id>/reset-password", methods=["POST"])
def admin_reset_password(user_id):
    if not admin_required():
        return jsonify({"error": "Solo admin"}), 403
    data = request.get_json()
    new_password = data.get("password", "").strip()
    if not new_password:
        return jsonify({"error": "Inserisci una password"}), 400
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/admin/users/<int:user_id>/toggle-disable", methods=["POST"])
def admin_toggle_disable(user_id):
    if not admin_required():
        return jsonify({"error": "Solo admin"}), 403
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404
    if user.is_admin:
        return jsonify({"error": "Non puoi disabilitare l'admin"}), 400
    user.disabled = not user.disabled
    db.session.commit()
    return jsonify({"ok": True, "disabled": user.disabled})


@app.route("/api/admin/users/<int:user_id>/reset-selections", methods=["POST"])
def admin_reset_selections(user_id):
    if not admin_required():
        return jsonify({"error": "Solo admin"}), 403
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Utente non trovato"}), 404
    Selection.query.filter_by(user_id=user_id).delete()
    user.locked = False
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/simulate-results", methods=["POST"])
def simulate_results():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Non autenticato"}), 401
    user = db.session.get(User, user_id)
    if not user or not user.is_admin:
        return jsonify({"error": "Solo l'admin"}), 403

    import random
    matches = Match.query.filter(Match.instance == INSTANCE, Match.home_score.is_(None)).all()
    count = len(matches)
    for m in matches:
        m.home_score = random.randint(0, 4)
        m.away_score = random.randint(0, 4)
    db.session.commit()
    return jsonify({"ok": True, "simulated": count})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
