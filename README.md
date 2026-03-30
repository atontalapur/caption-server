---
title: Caption Server
emoji: 📸
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
---

# Caption Server

Generates **5 photo captions written in your personal style** using Claude's vision API.

Upload your writing once → the server learns your voice → every caption it generates sounds like you.

Deployable on **Hugging Face Spaces** (Docker SDK) or run locally.

---

## Workflow

```
1.  POST /train    ← send your writing samples once
        ↓
    200 OK — "ready to accept images"
        ↓
2.  POST /captions ← send any photo from any app
        ↓
    5 captions in your style
```

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health`   | Liveness + training status |
| `POST` | `/train`    | Upload writing samples (one-time setup) |
| `POST` | `/captions` | Upload a photo → 5 captions |

---

### `POST /train`

Send all files from your writings directory as a `multipart/form-data` request.
Accepted extensions: `.txt`, `.md`, `.mdx`. Other files are ignored.

```bash
curl -X POST https://your-space.hf.space/train \
  -F "files=@journal_entry.txt" \
  -F "files=@blog_post.md" \
  -F "files=@notes.txt"
```

**Response `200 OK`**
```json
{
  "status": "ready",
  "files_accepted": 3,
  "message": "Training data accepted (3 file(s)). The server is now ready to generate captions."
}
```

---

### `POST /captions`

Send one image file. Supported: JPEG, PNG, GIF, WebP (max 20 MB).

```bash
curl -X POST https://your-space.hf.space/captions \
  -F "image=@photo.jpg"
```

**Response `200 OK`**
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

Returns `503` if `/train` has not been called yet.

---

### `GET /health`

```json
{
  "status": "ok",
  "trained": true,
  "files_loaded": 3,
  "port": 7860
}
```

---

## Deploy to Hugging Face Spaces

1. **Create a new Space** at huggingface.co → SDK: **Docker**
2. Push this repo as the Space source (or fork it)
3. Add your secret in **Settings → Variables and Secrets**:
   - `ANTHROPIC_API_KEY` → your Anthropic key
4. Optionally enable **Persistent Storage** so training data survives restarts
5. The Space builds and starts — your API is live at `https://your-username-caption-server.hf.space`

---

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add ANTHROPIC_API_KEY
python -m app.main            # → http://localhost:7860
```

---

## Project structure

```
caption-server/
├── app/
│   ├── main.py                  # FastAPI app + lifespan
│   ├── routes/
│   │   ├── train.py             # POST /train
│   │   ├── captions.py          # POST /captions
│   │   └── health.py            # GET  /health
│   ├── services/
│   │   ├── claude_client.py     # Claude vision API
│   │   └── style_loader.py      # File parsing + persistence
│   └── models/
│       └── schemas.py           # Pydantic types
├── data/                        # Runtime cache (git-ignored)
├── docs/
│   └── NEXTJS_INTEGRATION.md   # Next.js-specific guide
├── Dockerfile                   # HF Spaces Docker build
├── requirements.txt
└── .env.example
```

---

## Integration docs

- **Any HTTP client** — use the curl examples above directly.
- **Next.js** — see [`docs/NEXTJS_INTEGRATION.md`](docs/NEXTJS_INTEGRATION.md).
