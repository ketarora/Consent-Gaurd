# Merchant Integration Guide

Consent Guard is designed to run asynchronously alongside your existing LLM orchestration pipeline, providing deterministic intercept signals immediately before the final consumer socket push.

## Example Request (cURL)

When your autonomous agent generates a message intended for a buyer, pipe it entirely to the proxy endpoint:

```bash
curl -X POST "http://localhost:8000/api/intercept" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: rzp_test_consent_123" \
     -d '{
           "content": "Confirm your subscription below. You have exactly 4 minutes before the server crashes and deletes your discount.",
           "agent_id": "cart_recovery_bot_09"
         }'
```

## Expected Console Output

The firewall evaluates the payload synchronously (routing appropriately depending on prefilter triggering). If manipulative intent mapping to the taxonomy is found, a counterfactual `suggested_rewrite` is returned alongside the `held` action.

```json
{
  "message_id": "msg_f3a29b441c",
  "content": "Confirm your subscription below. You have exactly 4 minutes before the server crashes and deletes your discount.",
  "agent_id": "cart_recovery_bot_09",
  "timestamp": "2026-09-05T14:22:11.721Z",
  "decision": {
    "action": "held",
    "flags": [
      {
        "category": "CONFIRM_SHAMING",
        "confidence": 0.99,
        "quoted_span": "before the server crashes and deletes your discount",
        "suggested_rewrite": "Please confirm your subscription below when you are ready.",
        "cleared_by_allowlist": false
      }
    ],
    "reviewer_id": null,
    "review_notes": null
  }
}
```

## Handling Output in Merchant Services
Your backend should evaluate the `decision.action` key:
- `"passed"`: Broadcast to the user via WebSocket or push notification.
- `"held"`: Silently drop the outbound socket attempt. (Optional) inject `flags[0].suggested_rewrite` into the conversation history of the agent, forcing it to resample without hallucinated urgency.
