"""Seed the database with matches from calc_teams.py and initial data."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, Match, User, Selection
from werkzeug.security import generate_password_hash

# Team name normalization (Sky schedule → FASCE)
N = {
    "Cechia": "Repubblica Ceca",
    "Bosnia-Erzegovina": "Bosnia",
    "Repubblica Democratica del Congo": "RD del Congo",
    "RD Congo": "RD del Congo",
    "Curaçao": "Curacao",
    "Usa": "Stati Uniti",
}

def norm(name):
    return N.get(name, name)

# Helper: datetime for Italian date/time in June 2026
from datetime import datetime

def dt(day, hour, minute=0):
    return datetime(2026, 6, day, hour, minute)

# (matchday, home, away, datetime) — 72 partite, date/ora italiane da Wikipedia
MATCHES = [
    # Gruppo A (UTC-6 → Italia +8h, tranne Rep.Ceca-Sudafrica UTC-4 → +6h)
    (1, "Messico", "Sudafrica", dt(11, 21)),
    (1, "Corea del Sud", "Repubblica Ceca", dt(12, 4)),
    (2, "Repubblica Ceca", "Sudafrica", dt(18, 18)),
    (2, "Messico", "Corea del Sud", dt(19, 3)),
    (3, "Repubblica Ceca", "Messico", dt(25, 3)),
    (3, "Sudafrica", "Corea del Sud", dt(25, 3)),

    # Gruppo B (Canada-Bosnia UTC-4 → +6h, resto UTC-7 → +9h)
    (1, "Canada", norm("Bosnia-Erzegovina"), dt(12, 21)),
    (1, "Qatar", "Svizzera", dt(13, 21)),
    (2, "Svizzera", norm("Bosnia-Erzegovina"), dt(18, 21)),
    (2, "Canada", "Qatar", dt(19, 0)),
    (3, "Svizzera", "Canada", dt(24, 21)),
    (3, norm("Bosnia-Erzegovina"), "Qatar", dt(24, 21)),

    # Gruppo C (UTC-4 → +6h)
    (1, "Brasile", "Marocco", dt(14, 0)),
    (1, norm("Haiti"), "Scozia", dt(14, 3)),
    (2, "Scozia", "Marocco", dt(20, 0)),
    (2, "Brasile", norm("Haiti"), dt(20, 2, 30)),
    (3, "Scozia", "Brasile", dt(25, 0)),
    (3, "Marocco", norm("Haiti"), dt(25, 0)),

    # Gruppo D (UTC-7 → +9h)
    (1, norm("Usa"), "Paraguay", dt(13, 3)),
    (1, "Australia", "Turchia", dt(14, 6)),
    (2, norm("Usa"), "Australia", dt(19, 21)),
    (2, "Turchia", "Paraguay", dt(20, 5)),
    (3, "Turchia", norm("Usa"), dt(26, 4)),
    (3, "Paraguay", "Australia", dt(26, 4)),

    # Gruppo E (Germania-Curaçao UTC-5 → +7h, resto UTC-4 → +6h)
    (1, "Germania", norm("Curaçao"), dt(14, 19)),
    (1, "Costa d'Avorio", "Ecuador", dt(15, 1)),
    (2, "Germania", "Costa d'Avorio", dt(20, 22)),
    (2, "Ecuador", norm("Curaçao"), dt(21, 2)),
    (3, norm("Curaçao"), "Costa d'Avorio", dt(25, 22)),
    (3, "Ecuador", "Germania", dt(25, 22)),

    # Gruppo F (Svezia-Tunisia UTC-6 → +8h, resto UTC-5 → +7h)
    (1, "Olanda", "Giappone", dt(14, 22)),
    (1, "Svezia", "Tunisia", dt(15, 4)),
    (2, "Olanda", "Svezia", dt(20, 19)),
    (2, "Tunisia", "Giappone", dt(21, 6)),
    (3, "Giappone", "Svezia", dt(26, 1)),
    (3, "Tunisia", "Olanda", dt(26, 1)),

    # Gruppo G (UTC-7 → +9h)
    (1, "Belgio", "Egitto", dt(15, 21)),
    (1, "Iran", "Nuova Zelanda", dt(16, 3)),
    (2, "Belgio", "Iran", dt(21, 21)),
    (2, "Nuova Zelanda", "Egitto", dt(22, 3)),
    (3, "Egitto", "Iran", dt(27, 5)),
    (3, "Nuova Zelanda", "Belgio", dt(27, 5)),

    # Gruppo H (UTC-4 → +6h, tranne Capo Verde-Arabia UTC-5 → +7h e Uruguay-Spagna UTC-6 → +8h)
    (1, "Spagna", "Capo Verde", dt(15, 18)),
    (1, "Arabia Saudita", "Uruguay", dt(16, 0)),
    (2, "Spagna", "Arabia Saudita", dt(21, 18)),
    (2, "Uruguay", "Capo Verde", dt(22, 0)),
    (3, "Capo Verde", "Arabia Saudita", dt(27, 2)),
    (3, "Uruguay", "Spagna", dt(27, 2)),

    # Gruppo I (UTC-4 → +6h)
    (1, "Francia", "Senegal", dt(16, 21)),
    (1, "Iraq", "Norvegia", dt(17, 0)),
    (2, "Francia", "Iraq", dt(22, 23)),
    (2, "Norvegia", "Senegal", dt(23, 2)),
    (3, "Norvegia", "Francia", dt(26, 21)),
    (3, "Senegal", "Iraq", dt(26, 21)),

    # Gruppo J (Argentina-Algeria UTC-5 → +7h, Austria-Giordania UTC-7 → +9h, resto UTC-5 → +7h)
    (1, "Argentina", "Algeria", dt(17, 3)),
    (1, "Austria", "Giordania", dt(17, 6)),
    (2, "Argentina", "Austria", dt(22, 19)),
    (2, "Giordania", "Algeria", dt(23, 5)),
    (3, "Algeria", "Austria", dt(28, 4)),
    (3, "Giordania", "Argentina", dt(28, 4)),

    # Gruppo K (Portogallo-RD Congo UTC-5 → +7h, Uzbekistan-Colombia UTC-6 → +8h, MD3 UTC-4 → +6h)
    (1, "Portogallo", norm("Repubblica Democratica del Congo"), dt(17, 19)),
    (1, "Uzbekistan", "Colombia", dt(18, 4)),
    (2, "Portogallo", "Uzbekistan", dt(23, 19)),
    (2, "Colombia", norm("Repubblica Democratica del Congo"), dt(24, 4)),
    (3, "Colombia", "Portogallo", dt(28, 1, 30)),
    (3, norm("Repubblica Democratica del Congo"), "Uzbekistan", dt(28, 1, 30)),

    # Gruppo L (Inghilterra-Croazia UTC-5 → +7h, Ghana-Panama UTC-4 → +6h, MD2/3 UTC-4 → +6h)
    (1, "Inghilterra", "Croazia", dt(17, 22)),
    (1, "Ghana", "Panama", dt(18, 1)),
    (2, "Inghilterra", "Ghana", dt(23, 22)),
    (2, "Panama", "Croazia", dt(24, 1)),
    (3, "Panama", "Inghilterra", dt(27, 23)),
    (3, "Croazia", "Ghana", dt(27, 23)),
]

def seed():
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"DB non ancora pronto: {e}. Riproverà al primo avvio.")
            return

        from app import INSTANCE
        if Match.query.filter_by(instance=INSTANCE).first():
            print(f"Database già popolato per istanza '{INSTANCE}'. Salto seed.")
            return

        for md, home, away, date in MATCHES:
            match = Match(instance=INSTANCE, matchday=md, home_team=home, away_team=away, date=date)
            db.session.add(match)

        # Admin user
        if not User.query.filter_by(instance=INSTANCE, name="admin").first():
            admin = User(
                instance=INSTANCE,
                name="admin",
                password_hash=generate_password_hash("nicolamerola29"),
                is_admin=True,
                locked=True,
            )
            db.session.add(admin)

        db.session.commit()
        print(f"Inserite {len(MATCHES)} partite per istanza '{INSTANCE}'")

if __name__ == "__main__":
    seed()
