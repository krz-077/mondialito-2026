# Mondialito 2026

Gioco tra amici per il Mondiale 2026.

## Regole

- Scegli 6 squadre (una per fascia)
- Punti base: vittoria/pareggio in base alla fascia (I=2/1, II=4/2, III=6/3, IV=8/4, V=10/5, VI=12/6)
- Sconfitta = 0 punti
- Bonus: vincente mondiale +10pt, secondo +5pt
- Quota iscrizione: €10

## Installazione locale

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py       # carica le partite
python app.py        # avvia il server su http://localhost:5000
```

## Deploy su Render (gratuito)

1. Crea un account su [render.com](https://render.com)
2. Collega il repo GitHub
3. Crea un **Web Service**:
   - **Build Command**: `pip install -r requirements.txt && python seed.py`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
   - **Environment**: `Python 3`
   - **Plan**: Free

In alternativa, crea un file `render.yaml` per deploy automatico:

```yaml
services:
  - type: web
    name: mondialito-2026
    runtime: python
    buildCommand: pip install -r requirements.txt && python seed.py
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
```

## Utilizzo

1. **Registrati** con il tuo nome
2. **Scegli le squadre** (una per fascia)
3. **Inserisci i risultati** delle partite (manualmente)
4. **Calcola** i punteggi con il bottone "Calcola"
5. **Classifica** mostra i punti totali di tutti i partecipanti
