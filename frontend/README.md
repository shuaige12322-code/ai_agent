# Frontend

This frontend is scaffolded for:

- `Next.js`
- `assistant-ui`
- `shadcn/ui`-style local components

It is designed to talk to the existing FastAPI backend endpoints:

- `POST /chat`
- `GET /memory/{user_id}`
- `POST /memory/add`
- `GET /conversation/{user_id}`
- `POST /conversation/clear/{user_id}`
- `POST /knowledge/add`
- `GET /stats/{user_id}`

## Setup

Install Node.js 20+ first, because this machine did not have `node` or `npm` available when the scaffold was created.

Then run:

```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

Make sure the FastAPI backend is already running on:

```text
http://localhost:8000
```

## Environment

`.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_DEFAULT_USER_ID=demo-user
```

## Notes

- The current chat adapter is built against the existing non-streaming `/chat` REST API.
- The UI structure is intentionally ready for a future streaming transport upgrade.
- Once you add a streaming backend route, the `assistant-ui` runtime adapter is the main place to upgrade.

## Included UI

- Center chat workspace for the agent thread
- Left memory console for adding and viewing stored user memories
- Left conversation panel for reviewing or clearing session history
- Right knowledge intake panel for uploading RAG documents
- Right stats panel for memory totals and conversation length
