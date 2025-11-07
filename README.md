
# FastAPI SQLite — Events & Members (POST for updates)

Features:
- SQLite via SQLModel
- Events (create/list/get/delete, **POST-as-update** on `/events/{id}`)
- Members with fields: cardId, name, wilayah, lingkungan, noHandphone, instagram, birthday, age
- Tap-in by `cardId`: `POST /events/{event_id}/tapin`
- List attendees of an event
- CORS + `/` redirects to `/docs`

## Setup (macOS)
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

## Notes
- If you previously created `app.db` with an older schema, delete it to recreate:
  ```bash
  rm app.db
  ```
- API uses camelCase where you asked; DB uses snake_case internally.
