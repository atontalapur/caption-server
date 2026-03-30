# Caption Server

A local Python server that generates **5 photo captions written in your personal style** using Claude's vision API.

Drop your own writing samples in → the server learns your voice → every caption it writes sounds like you.

---

## Stack

| Layer | Tech |
|-------|------|
| Server | FastAPI + Uvicorn |
| AI | Anthropic Claude (vision) |
| Style priming | `.txt` / `.md` / `.mdx` files you provide |
| Port | `8472` |

---

## Quick start

```bash
# 1. Clone and enter
cd caption-server

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY

# 5. Add your writing (optional but recommended)
#    Drop .txt / .md files into data/writings/

# 6. Start
python -m app.main
```

Server starts at `http://localhost:8472`.

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check |
| `POST` | `/captions` | Upload image → get 5 captions |

**POST /captions** — `multipart/form-data`, field name `image`
Supported formats: JPEG, PNG, GIF, WebP (max 20 MB)

```bash
curl -X POST http://localhost:8472/captions \
  -F "image=@/path/to/photo.jpg"
```

Response:
```json
{
  "captions": [
    "Caption one.",
    "Caption two.",
    "Caption three.",
    "Caption four.",
    "Caption five."
  ],
  "style_samples_loaded": 3
}
```

---

## Style priming

Place any `.txt`, `.md`, or `.mdx` files in `data/writings/` before starting the server.
The contents are read once on startup and injected into every Claude prompt as a style reference.
Restart the server after adding new samples.

---

## Next.js integration

See [`docs/NEXTJS_INTEGRATION.md`](docs/NEXTJS_INTEGRATION.md) for a full guide including a proxy route handler, client hook, and TypeScript types.

---

## Project structure

```
caption-server/
├── app/
│   ├── main.py               # FastAPI app + lifespan
│   ├── routes/
│   │   ├── captions.py       # POST /captions
│   │   └── health.py         # GET /health
│   ├── services/
│   │   ├── claude_client.py  # Claude API integration
│   │   └── style_loader.py   # Reads writing samples
│   └── models/
│       └── schemas.py        # Pydantic response models
├── data/
│   └── writings/             # Your writing samples (git-ignored)
├── docs/
│   └── NEXTJS_INTEGRATION.md
├── .env.example
├── requirements.txt
└── README.md
```
