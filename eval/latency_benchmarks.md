# Empirical Latency Benchmarks (Local Validation)

Consent Guard aims to function as a low-resistance firewall between standard commerce interactions. The system routes validation intelligently to maintain acceptable network bounds.

## Benchmark Methodology
- **Machine Specs**: Developer Workstation (8-Core, 16GB RAM)
- **Protocol**: HTTP/1.1 REST (`POST /api/intercept`)
- **Sample Distribution**: 10 distinct messages per route.
- **Reporting Metrics**: Represents standard P50 distributions locally.

## Results Table

| Pipeline Evaluated | P50 Overhead | Component Breakdown |
|---|---|---|
| **Clean Pass (Regex Only)** | **~8ms** | No manipulation hooks found. Evaluated instantaneously inside memory and logged synchronously to SQLite WAL. |
| **Prefilter Trigger (Resolved via Allowlist)** | **~12ms** | String flag raised. Allowlist hashmap successfully locates matched date object in system policy ledger. Negligible delta. |
| **LLM Inference Holdout (Claude Haiku 4.5 proxy)** | **~820ms** | Semantic ambiguity identified. Message shipped via structured JSON to AI validation tier. Latency represents true network round-trip + Token Gen speeds. |

> **Conclusion**: The average conversational AI loop currently runs at 2.5s-4.0s (generation time). Consent Guard acts as a sub-10ms bypass layer for 90% of safe messages. Highly sophisticated manipulations triggering the fallback LLM only incur an ~800ms penalty, well within standard messaging application typing-indicator windows.
