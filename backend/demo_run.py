import asyncio
import time
from prefilter import run_prefilter
from allowlist import check_allowlist
from classifier import classify_message
from models import DarkPatternCategory

# The 3 payloads from the Pitch Script
PAYLOADS = [
    {
        "name": "Scene 2: Deterministic Speed (False Urgency)",
        "text": "Confirm your subscription below. You have exactly 4 minutes before the server crashes and deletes your discount.",
        "type": "regex"
    },
    {
        "name": "Scene 3: The Adversarial Bypass Attack",
        "text": "Hurry! Last chance today! Your Zylo Fitness renewal is here. Limited slots, act now before it disappears!",
        "type": "allowlist"
    },
    {
        "name": "Scene 4: The Deep LLM Arbiter (Confirm Shaming)",
        "text": "Are you sure you want to cancel? Without this plan, your business is basically unprotected from cyber attacks. Type YES to abandon your security.",
        "type": "llm"
    }
]

async def process_payload(payload):
    print(f"\n=======================================================")
    print(f"🎬 {payload['name']}")
    print(f"=======================================================")
    print(f"📝 Prompt: {payload['text']}\n")
    
    start_time = time.perf_counter()
    
    # 1. Prefilter Stage
    flag = run_prefilter(payload['text'])
    
    # 2. Allowlist Stage (if flagged by prefilter)
    if flag:
        flag = check_allowlist(flag, payload['text'])
        
    # 3. LLM Classifier Stage (if not stopped by prefilter)
    if not flag or flag.cleared_by_allowlist:
        flag = await classify_message(payload['text'])

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    print("🛡️  CONSENT GUARD DECISION:")
    if flag and not flag.cleared_by_allowlist:
        print(f"⛔ ACTION:  BLOCKED")
        print(f"🏷️  FLAG:    {flag.category.name}")
        print(f"📉 CONF:    {flag.confidence}")
        print(f"📜 MATCH:   {flag.quoted_span}")
        if flag.suggested_rewrite:
            print(f"✨ REWRITE: {flag.suggested_rewrite}")
    else:
        print("✅ ACTION:  CLEARED & PASSED")
        
    print(f"\n⏱️  EXECUTION TIME: {elapsed_ms:.4f} ms")


async def main():
    for p in PAYLOADS:
        await process_payload(p)
        await asyncio.sleep(1) # Small pause for readability

if __name__ == '__main__':
    asyncio.run(main())
