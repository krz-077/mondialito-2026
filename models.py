from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

db = SQLAlchemy()

FASCE = {
    1: ["Francia", "Argentina", "Brasile", "Inghilterra", "Spagna", "Portogallo", "Germania", "Olanda"],
    2: ["Uruguay", "Colombia", "Croazia", "Belgio", "Marocco", "Stati Uniti", "Messico", "Svizzera"],
    3: ["Ecuador", "Senegal", "Giappone", "Austria", "Svezia", "Turchia", "Corea del Sud", "Repubblica Ceca"],
    4: ["Paraguay", "Canada", "Australia", "Norvegia", "Costa d'Avorio", "Egitto", "Algeria", "Tunisia"],
    5: ["Bosnia", "Scozia", "Ghana", "Arabia Saudita", "Iran", "Qatar", "Iraq", "Panama"],
    6: ["Sudafrica", "Uzbekistan", "RD del Congo", "Giordania", "Haiti", "Capo Verde", "Curacao", "Nuova Zelanda"],
}

PUNTEGGI = {
    1: {"win": 2, "draw": 1},
    2: {"win": 4, "draw": 2},
    3: {"win": 6, "draw": 3},
    4: {"win": 8, "draw": 4},
    5: {"win": 10, "draw": 5},
    6: {"win": 12, "draw": 6},
}

# Map PDF team names to names used in calc_teams.py
TEAM_ALIASES = {
    "Bosnia": "Bosnia Erzegovina",
    "RD del Congo": "Congo",
}

# Team -> Fascia lookup
TEAM_FASCIA = {}
for fascia, teams in FASCE.items():
    for team in teams:
        TEAM_FASCIA[team] = fascia

def normalize_team(name):
    if name in TEAM_ALIASES:
        return TEAM_ALIASES[name]
    if name in TEAM_FASCIA:
        return name
    for canonical, alias in TEAM_ALIASES.items():
        if name == alias:
            return canonical
    return name

def get_fascia(team_name):
    if team_name in TEAM_FASCIA:
        return TEAM_FASCIA[team_name]
    if team_name in TEAM_ALIASES:
        canonical = TEAM_ALIASES[team_name]
        return TEAM_FASCIA.get(canonical)
    return None

def get_fascia_name(team_name):
    f = get_fascia(team_name)
    if f:
        return f"{f}° Fascia"
    return None


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instance = db.Column(db.String(50), nullable=False, default="default")
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    locked = db.Column(db.Boolean, default=False)
    disabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("instance", "name"),)

    selections = db.relationship("Selection", backref="user", lazy=True)

    def team_by_fascia(self):
        result = {}
        for s in self.selections:
            result[s.fascia] = s.team_name
        return result

    def points(self, matchday=None):
        total = 0
        for s in self.selections:
            total += s.points(matchday)
        return total


class Selection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    fascia = db.Column(db.Integer, nullable=False)
    team_name = db.Column(db.String(100), nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "fascia"),)

    @property
    def _inst(self):
        return os.environ.get("INSTANCE", "default")

    def puntos(self, matchday=None):
        fascia_pts = PUNTEGGI[self.fascia]
        query = Match.query.filter(
            Match.instance == self._inst,
            ((Match.home_team == self.team_name) | (Match.away_team == self.team_name)),
            Match.home_score.isnot(None),
            Match.away_score.isnot(None),
        )
        if matchday:
            query = query.filter(Match.matchday == matchday)

        pts = 0
        matches = query.all()
        for m in matches:
            if m.home_team == self.team_name:
                if m.home_score > m.away_score:
                    pts += fascia_pts["win"]
                elif m.home_score == m.away_score:
                    pts += fascia_pts["draw"]
            elif m.away_team == self.team_name:
                if m.away_score > m.home_score:
                    pts += fascia_pts["win"]
                elif m.home_score == m.away_score:
                    pts += fascia_pts["draw"]
        return pts

    def points(self, matchday=None):
        pts = self.puntos(matchday)
        if matchday is None:
            winner_cfg = Config.query.filter_by(instance=self._inst, key="world_cup_winner").first()
            runner_cfg = Config.query.filter_by(instance=self._inst, key="world_cup_runner_up").first()
            if winner_cfg and self.team_name == winner_cfg.value:
                pts += 10
            if runner_cfg and self.team_name == runner_cfg.value:
                pts += 5
        return pts


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instance = db.Column(db.String(50), nullable=False, default="default")
    matchday = db.Column(db.Integer, nullable=False)
    home_team = db.Column(db.String(100), nullable=False)
    away_team = db.Column(db.String(100), nullable=False)
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    date = db.Column(db.DateTime, nullable=True)


class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instance = db.Column(db.String(50), nullable=False, default="default")
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(500), nullable=True)

    __table_args__ = (db.UniqueConstraint("instance", "key"),)
