# Integrating the Caption Server with Next.js

The server runs on **port `8472`** (non-standard, safe to keep open alongside your Next.js dev server on 3000).

---

## 1. Start the caption server

```bash
# From the caption-server root
python -m app.main
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8472 (Press CTRL+C to quit)
```

---

## 2. Verify it's alive

```bash
curl http://localhost:8472/health
# {"status":"ok","writings_loaded":3,"port":8472}
```

---

## 3. Environment variable in Next.js

Add this to your Next.js project's `.env.local`:

```env
CAPTION_SERVER_URL=http://localhost:8472
```

For production, point this at wherever you host the Python server (e.g. a Railway / Fly.io URL).

---

## 4. A) Server-side Route Handler (recommended)

Keeps the Python server private — your Next.js app proxies the request.

```ts
// app/api/captions/route.ts
import { NextRequest, NextResponse } from "next/server";

const CAPTION_SERVER = process.env.CAPTION_SERVER_URL ?? "http://localhost:8472";

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const image = formData.get("image");

  if (!image || !(image instanceof File)) {
    return NextResponse.json({ error: "No image provided" }, { status: 400 });
  }

  // Forward the file to the caption server
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

  const data = await res.json();
  // data = { captions: string[5], style_samples_loaded: number }
  return NextResponse.json(data);
}
```

---

## 5. B) Client-side (direct call — only if server is public)

If you expose the Python server publicly with CORS set to your domain:

```ts
async function getCaptions(file: File): Promise<string[]> {
  const form = new FormData();
  form.append("image", file);

  const res = await fetch("http://localhost:8472/captions", {
    method: "POST",
    body: form,
  });

  if (!res.ok) throw new Error(`Caption server error: ${res.status}`);
  const data = await res.json();
  return data.captions; // string[]
}
```

---

## 6. React component example

```tsx
"use client";

import { useState } from "react";

export default function CaptionUploader() {
  const [captions, setCaptions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setCaptions([]);

    const form = new FormData();
    form.append("image", file);

    const res = await fetch("/api/captions", { method: "POST", body: form });
    const data = await res.json();

    setCaptions(data.captions ?? []);
    setLoading(false);
  }

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleUpload} />
      {loading && <p>Generating captions…</p>}
      {captions.length > 0 && (
        <ol>
          {captions.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ol>
      )}
    </div>
  );
}
```

---

## 7. TypeScript types

```ts
// types/captions.ts
export interface CaptionResponse {
  captions: [string, string, string, string, string];
  style_samples_loaded: number;
}
```

---

## 8. Adding your writing style

Drop `.txt`, `.md`, or `.mdx` files into `caption-server/data/writings/` and restart the server. The more samples you add, the stronger the style priming. No redeployment of Next.js needed.

---

## 9. API reference

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/health` | — | `{ status, writings_loaded, port }` |
| `POST` | `/captions` | `multipart/form-data` with `image` field | `{ captions: string[5], style_samples_loaded: number }` |

**Supported image types:** JPEG, PNG, GIF, WebP (max 20 MB)
