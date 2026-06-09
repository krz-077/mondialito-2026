import json

matches = [
    # Giornata 1
    ("Messico", "Sudafrica", 1.40, 4.50, 9.00),
    ("Corea del Sud", "Repubblica Ceca", 2.60, 3.10, 2.90),
    ("Canada", "Bosnia Erzegovina", 1.80, 3.50, 4.50),
    ("Stati Uniti", "Paraguay", 1.95, 3.25, 4.00),
    ("Qatar", "Svizzera", 14.00, 6.50, 1.20),
    ("Brasile", "Marocco", 1.67, 3.75, 5.25),
    ("Haiti", "Scozia", 6.00, 4.25, 1.50),
    ("Australia", "Turchia", 5.25, 3.60, 1.67),
    ("Germania", "Curacao", 1.04, 18.00, 36.00),
    ("Olanda", "Giappone", 2.05, 3.50, 3.60),
    ("Costa D'Avorio", "Ecuador", 3.40, 2.75, 2.45),
    ("Svezia", "Tunisia", 1.90, 3.25, 4.25),
    ("Spagna", "Capo Verde", 1.08, 12.00, 24.00),
    ("Belgio", "Egitto", 1.65, 3.75, 5.25),
    ("Arabia Saudita", "Uruguay", 8.00, 4.25, 1.42),
    ("Iran", "Nuova Zelanda", 1.85, 3.25, 4.25),
    ("Francia", "Senegal", 1.45, 4.25, 7.00),
    ("Iraq", "Norvegia", 14.00, 6.50, 1.20),
    ("Argentina", "Algeria", 1.40, 4.50, 8.50),
    ("Austria", "Giordania", 1.30, 5.50, 9.00),
    ("Portogallo", "Congo", 1.27, 5.75, 12.00),
    ("Inghilterra", "Croazia", 1.70, 3.75, 4.75),
    ("Ghana", "Panama", 2.05, 3.40, 3.60),
    ("Uzbekistan", "Colombia", 8.50, 4.50, 1.36),
    # Giornata 2
    ("Repubblica Ceca", "Sudafrica", 1.90, 3.40, 4.00),
    ("Svizzera", "Bosnia Erzegovina", 1.62, 3.75, 5.75),
    ("Canada", "Qatar", 1.30, 5.25, 10.00),
    ("Messico", "Corea del Sud", 1.80, 3.50, 4.50),
    ("Stati Uniti", "Australia", 1.70, 3.60, 4.75),
    ("Scozia", "Marocco", 4.00, 3.25, 1.90),
    ("Brasile", "Haiti", 1.07, 11.00, 25.00),
    ("Turchia", "Paraguay", 2.20, 3.10, 3.25),
    ("Olanda", "Svezia", 1.65, 3.75, 5.00),
    ("Germania", "Costa D'Avorio", 1.52, 4.00, 5.75),
    ("Ecuador", "Curacao", 1.20, 6.50, 13.00),
    ("Tunisia", "Giappone", 5.25, 3.40, 1.70),
    ("Spagna", "Arabia Saudita", 1.11, 8.50, 25.00),
    ("Belgio", "Iran", 1.40, 4.50, 8.00),
    ("Uruguay", "Capo Verde", 1.42, 4.25, 7.50),
    ("Nuova Zelanda", "Egitto", 5.00, 3.50, 1.72),
    ("Argentina", "Austria", 1.62, 3.75, 5.25),
    ("Francia", "Iraq", 1.13, 8.00, 22.00),
    ("Norvegia", "Senegal", 2.05, 3.50, 3.50),
    ("Giordania", "Algeria", 6.50, 4.00, 1.52),
    ("Portogallo", "Uzbekistan", 1.25, 5.75, 11.00),
    ("Inghilterra", "Ghana", 1.30, 5.25, 9.00),
    ("Panama", "Croazia", 6.50, 4.00, 1.52),
    ("Colombia", "Congo", 1.45, 4.00, 7.50),
]

teams = {}
for home, away, odd1, oddX, odd2 in matches:
    for team, odd_win in [(home, odd1), (away, odd2)]:
        exp_pts = 3.0/odd_win + 1.0/oddX
        if team not in teams:
            teams[team] = {"exp_pts": 0.0, "matches": 0}
        teams[team]["exp_pts"] += exp_pts
        teams[team]["matches"] += 1

# average exp_pts per match
for t in teams:
    teams[t]["avg"] = teams[t]["exp_pts"] / teams[t]["matches"]

sorted_teams = sorted(teams.items(), key=lambda x: x[1]["avg"], reverse=True)

for team, data in sorted_teams:
    print(f"{team}: {data['avg']:.3f} (tot {data['exp_pts']:.3f})")

print("\n---")
print(f"Max: {sorted_teams[0][1]['avg']:.3f} ({sorted_teams[0][0]})")
print(f"Min: {sorted_teams[-1][1]['avg']:.3f} ({sorted_teams[-1][0]})")
