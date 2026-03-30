# Integrating the Caption Server with Next.js

The server runs on **port `7860`** locally and is available at
`https://<your-hf-username>-caption-server.hf.space` when deployed to Hugging Face Spaces.

---

## 1. One-time training call

Before any image can be captioned, send your writing samples to `/train`.
Do this once from a script, terminal, or an admin route — not on every page load.

```bash
# From your terminal — send every file in your writings folder
curl -X POST http://localhost:7860/train \
  $(find /path/to/writings -type f \( -name "*.txt" -o -name "*.md" \) \
    | xargs -I{} echo "-F files=@{}")
```

Response:
```json
{
  "status": "ready",
  "files_accepted": 4,
  "message": "Training data accepted (4 file(s)). The server is now ready to generate captions."
}
```

---

## 2. Environment variable in Next.js

```env
# .env.local
CAPTION_SERVER_URL=http://localhost:7860
# Production:
# CAPTION_SERVER_URL=https://your-hf-username-caption-server.hf.space
```

---

## 3. Server-side Route Handler (recommended)

Keeps your Python server private — Next.js proxies the request.

```ts
// app/api/captions/route.ts
import { NextRequest, NextResponse } from "next/server";

const CAPTION_SERVER = process.env.CAPTION_SERVER_URL ?? "http://localhost:7860";

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const image = formData.get("image");

  if (!image || !(image instanceof File)) {
    return NextResponse.json({ error: "No image provided" }, { status: 400 });
  }

  const upstream = new FormData();
  upstream.append("image", image, image.name);

  const res = await fetch(`${CAPTION_SERVER}/captions`, {
    method: "POST",
    body: upstream,
  });

  if (!res.ok) {
    const detail = await res.text();
    return NextResponse.json({ error: detail }, { status: res.status });
  }

  return NextResponse.json(await res.json());
}
```

---

## 4. React component

```tsx
"use client";

import { useState } from "react";

export default function CaptionUploader() {
  const [captions, setCaptions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setCaptions([]);

    const form = new FormData();
    form.append("image", file);

    const res = await fetch("/api/captions", { method: "POST", body: form });
    const data = await res.json();

    if (!res.ok) {
      setError(data.error ?? "Something went wrong.");
    } else {
      setCaptions(data.captions ?? []);
    }
    setLoading(false);
  }

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleUpload} />
      {loading && <p>Generating captions…</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {captions.length > 0 && (
        <ol>
          {captions.map((c, i) => <li key={i}>{c}</li>)}
        </ol>
      )}
    </div>
  );
}
```

---

## 5. TypeScript types

```ts
// types/captions.ts
export interface CaptionResponse {
  captions: [string, string, string, string, string];
  style_samples_loaded: number;
}

export interface TrainResponse {
  status: "ready";
  files_accepted: number;
  message: string;
}

export interface HealthResponse {
  status: "ok";
  trained: boolean;
  files_loaded: number;
  port: number;
}
```

---

## 6. Check training status from Next.js

```ts
const res = await fetch(`${process.env.CAPTION_SERVER_URL}/health`);
const { trained } = await res.json();
// trained === false → call /train first
```

---

## 7. API reference

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET`  | `/health`   | — | `{ status, trained, files_loaded, port }` |
| `POST` | `/train`    | `multipart/form-data` — field `files` (repeat per file) | `{ status, files_accepted, message }` |
| `POST` | `/captions` | `multipart/form-data` — field `image` | `{ captions: string[5], style_samples_loaded }` |

Supported image types: JPEG, PNG, GIF, WebP (max 20 MB).
`/captions` returns `503` if `/train` has not been called yet.
