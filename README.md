# Consent Guard Frontend (Compliance Dashboard)

This Next.js application serves as the real-time compliance oversight dashboard for the Consent Guard backend. Rather than traditional polling, it consumes a Server-Sent Event (SSE) stream from the backend to deliver sub-40ms telemetry updates to Compliance Officers tracking agentic drift.

## Key Features
- **Real-Time Log Ingestion**: Hooks into `/api/stream` for immediate ledger synchronization.
- **Glassmorphic Audit UI**: Minimalist, high-visibility workspace designed specifically for legal and compliance review.
- **POLICY DEVIATION Redlining**: Case-insensitive text mapping automatically highlights toxic phrases inside intercepted payloads.
- **Offline JSONL Export**: Direct one-click download of the complete compliance database trace.

## Getting Started

First, ensure the backend is running on `localhost:8000`.

Then, install dependencies and run the development server:
```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the live console.

## Architecture Guidelines
- Strict CSS scoping (`globals.css`) ensures FAANG-level FA/NextUI alignment.
- Zero client-side data mutation except for stateful manual "Approve" / "Reject" override dispatches (which persist to the backend's immutable ledger via REST).
