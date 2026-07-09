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

def dt(day, hour, minute=0, month=6):
    return datetime(2026, month, day, hour, minute)

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

    # --- Sedicesimi di finale (MD4) - orari italiani da Wikipedia ---
    (4, "Sudafrica", "Canada", dt(28, 21)),               # 28/06 12:00 UTC-7
    (4, "Brasile", "Giappone", dt(29, 19)),               # 29/06 12:00 UTC-5
    (4, "Germania", "Paraguay", dt(29, 22, 30)),          # 29/06 16:30 UTC-4
    (4, "Olanda", "Marocco", dt(30, 3)),                  # 29/06 19:00 UTC-6 → 30/06 03:00 IT
    (4, "Costa d'Avorio", "Norvegia", dt(30, 19)),        # 30/06 12:00 UTC-5
    (4, "Francia", "Svezia", dt(30, 23)),                 # 30/06 17:00 UTC-4
    (4, "Messico", "Ecuador", dt(1, 3, month=7)),                  # 30/06 19:00 UTC-6 → 01/07 03:00 IT
    (4, "Inghilterra", norm("Repubblica Democratica del Congo"), dt(1, 18, month=7)),  # 01/07 12:00 UTC-4
    (4, "Belgio", "Senegal", dt(1, 22, month=7)),                  # 01/07 13:00 UTC-7
    (4, norm("Usa"), norm("Bosnia-Erzegovina"), dt(2, 2, month=7)), # 01/07 17:00 UTC-7 → 02/07 02:00 IT
    (4, "Spagna", "Austria", dt(2, 21, month=7)),                  # 02/07 12:00 UTC-7
    (4, "Portogallo", "Croazia", dt(3, 1, month=7)),               # 02/07 19:00 UTC-4 → 03/07 01:00 IT
    (4, "Svizzera", "Algeria", dt(3, 5, month=7)),                 # 02/07 20:00 UTC-7 → 03/07 05:00 IT
    (4, "Australia", "Egitto", dt(3, 20, month=7)),                # 03/07 13:00 UTC-5
    (4, "Argentina", "Capo Verde", dt(4, 0, month=7)),             # 03/07 18:00 UTC-4 → 04/07 00:00 IT
    (4, "Colombia", "Ghana", dt(4, 3, 30, month=7)),               # 03/07 20:30 UTC-5 → 04/07 03:30 IT

    # --- Ottavi di finale (MD5) - orari italiani da Wikipedia ---
    (5, "Canada", "Marocco", dt(4, 19, month=7)),                  # 04/07 12:00 UTC-5
    (5, "Paraguay", "Francia", dt(4, 23, month=7)),                # 04/07 17:00 UTC-4
    (5, "Brasile", "Norvegia", dt(5, 22, month=7)),                # 05/07 16:00 UTC-4
    (5, "Messico", "Inghilterra", dt(6, 2, month=7)),              # 05/07 18:00 UTC-6 → 06/07 02:00 IT
    (5, "Portogallo", "Spagna", dt(6, 21, month=7)),               # 06/07 14:00 UTC-5
    (5, norm("Usa"), "Belgio", dt(7, 2, month=7)),                  # 06/07 17:00 UTC-7 → 07/07 02:00 IT
    (5, "Argentina", "Egitto", dt(7, 18, month=7)),                # 07/07 12:00 UTC-4
    (5, "Svizzera", "Colombia", dt(7, 22, month=7)),               # 07/07 13:00 UTC-7

    # --- Quarti di finale (MD6) ---
    (6, "Francia", "Marocco", dt(9, 22, month=7)),                # 09/07 16:00 UTC-4
    (6, "Spagna", "Belgio", dt(10, 21, month=7)),                 # 10/07 12:00 UTC-7
    (6, "Norvegia", "Inghilterra", dt(11, 23, month=7)),          # 11/07 17:00 UTC-4
    (6, "Argentina", "Svizzera", dt(12, 3, month=7)),             # 11/07 20:00 UTC-5 → 12/07 03:00 IT

    # --- Semifinali (MD7) - nomi da aggiornare dopo i quarti ---
    (7, "Vincente 97", "Vincente 98", dt(14, 21, month=7)),       # 14/07 14:00 UTC-5
    (7, "Vincente 99", "Vincente 100", dt(15, 21, month=7)),      # 15/07 15:00 UTC-4

    # --- Finale terzo posto (MD8) ---
    (8, "Perdente 101", "Perdente 102", dt(18, 23, month=7)),     # 18/07 17:00 UTC-4

    # --- Finale (MD9) ---
    (9, "Vincente 101", "Vincente 102", dt(19, 21, month=7)),     # 19/07 15:00 UTC-4
]

def seed():
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"DB non ancora pronto: {e}. Riproverà al primo avvio.")
            return

        from app import INSTANCE
        added = 0
        for md, home, away, date in MATCHES:
            existing = Match.query.filter_by(instance=INSTANCE, matchday=md, home_team=home, away_team=away).first()
            if not existing:
                match = Match(instance=INSTANCE, matchday=md, home_team=home, away_team=away, date=date)
                db.session.add(match)
                added += 1

        if added:
            db.session.commit()
            print(f"Inserite {added} nuove partite per istanza '{INSTANCE}'")
        else:
            print(f"Nessuna nuova partita per istanza '{INSTANCE}'")

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
