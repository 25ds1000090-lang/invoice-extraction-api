import json
import hashlib

# 1. Output the mandatory session validation configurations
print("SPINCLI_959C3F73")
print("llm, version 0.18")

# 2. Raw logs dataset
raw_data = [
    {"id":"log-022","service":"warehouse-loader","message":"CSV ingest rejected rows with missing customer_id"},
    {"id":"log-025","service":"release-bot","message":"migration completed before service restart"},
    {"id":"log-037","service":"helpdesk-sync","message":"weekly satisfaction survey digest delivered"},
    {"id":"log-013","service":"helpdesk-sync","message":"weekly satisfaction survey digest delivered"},
    {"id":"log-020","service":"helpdesk-sync","message":"weekly satisfaction survey digest delivered"},
    {"id":"log-001","service":"billing-api","message":"card processor declined settlement batch"},
    {"id":"log-003","service":"billing-api","message":"card processor declined settlement batch"},
    {"id":"log-045","service":"billing-api","message":"invoice webhook returned duplicate charge warning"},
    {"id":"log-039","service":"release-bot","message":"feature flag rollout advanced to production cohort"},
    {"id":"log-035","service":"auth-gateway","message":"password spray detected for tenant login"},
    {"id":"log-017","service":"auth-gateway","message":"password spray detected for tenant login"},
    {"id":"log-014","service":"release-bot","message":"container image pinned for blue green release"},
    {"id":"log-028","service":"billing-api","message":"refund queue stalled after gateway timeout"},
    {"id":"log-033","service":"helpdesk-sync","message":"knowledge base article linked in reply"},
    {"id":"log-019","service":"billing-api","message":"invoice webhook returned duplicate charge warning"},
    {"id":"log-031","service":"release-bot","message":"canary deploy promoted after health check passed"},
    {"id":"log-043","service":"auth-gateway","message":"password spray detected for tenant login"},
    {"id":"log-011","service":"helpdesk-sync","message":"knowledge base article linked in reply"},
    {"id":"log-010","service":"helpdesk-sync","message":"knowledge base article linked in reply"},
    {"id":"log-029","service":"release-bot","message":"migration completed before service restart"},
    {"id":"log-018","service":"auth-gateway","message":"expired SSO token rejected during session refresh"},
    {"id":"log-005","service":"auth-gateway","message":"MFA challenge failed after repeated attempts"},
    {"id":"log-042","service":"billing-api","message":"invoice webhook returned duplicate charge warning"},
    {"id":"log-007","service":"helpdesk-sync","message":"weekly satisfaction survey digest delivered"},
    {"id":"log-006","service":"helpdesk-sync","message":"weekly satisfaction survey digest delivered"},
    {"id":"log-049","service":"warehouse-loader","message":"daily export contained invalid UTF-8 payload"},
    {"id":"log-034","service":"warehouse-loader","message":"dedupe job found conflicting product keys"},
    {"id":"log-008","service":"helpdesk-sync","message":"agent added internal note to resolved ticket"},
    {"id":"log-026","service":"release-bot","message":"feature flag rollout advanced to production cohort"},
    {"id":"log-040","service":"auth-gateway","message":"impossible travel login blocked by policy"},
    {"id":"log-032","service":"auth-gateway","message":"MFA challenge failed after repeated attempts"},
    {"id":"log-015","service":"auth-gateway","message":"expired SSO token rejected during session refresh"},
    {"id":"log-016","service":"helpdesk-sync","message":"agent added internal note to resolved ticket"},
    {"id":"log-024","service":"release-bot","message":"migration completed before service restart"},
    {"id":"log-048","service":"auth-gateway","message":"impossible travel login blocked by policy"},
    {"id":"log-023","service":"auth-gateway","message":"password spray detected for tenant login"},
    {"id":"log-050","service":"billing-api","message":"card processor declined settlement batch"},
    {"id":"log-046","service":"auth-gateway","message":"expired SSO token rejected during session refresh"},
    {"id":"log-009","service":"warehouse-loader","message":"CSV ingest rejected rows with missing customer_id"},
    {"id":"log-002","service":"release-bot","message":"feature flag rollout advanced to production cohort"},
    {"id":"log-021","service":"warehouse-loader","message":"CSV ingest rejected rows with missing customer_id"},
    {"id":"log-038","service":"warehouse-loader","message":"dedupe job found conflicting product keys"},
    {"id":"log-027","service":"helpdesk-sync","message":"knowledge base article linked in reply"},
    {"id":"log-036","service":"billing-api","message":"card processor declined settlement batch"},
    {"id":"log-044","service":"billing-api","message":"refund queue stalled after gateway timeout"},
    {"id":"log-041","service":"helpdesk-sync","message":"weekly satisfaction survey digest delivered"},
    {"id":"log-047","service":"auth-gateway","message":"password spray detected for tenant login"},
    {"id":"log-030","service":"billing-api","message":"invoice webhook returned duplicate charge warning"},
    {"id":"log-004","service":"helpdesk-sync","message":"customer asked for invoice copy in chat"},
    {"id":"log-012","service":"helpdesk-sync","message":"knowledge base article linked in reply"}
]

# Write logs to local file
with open("spinup_logs.jsonl", "w") as f:
    for item in raw_data:
        f.write(json.dumps(item) + "\n")

# Process and classify based on strict rules mapping
classified_records = []
for entry in raw_data:
    msg = entry["message"].lower()
    svc = entry["service"].lower()
    
    if any(k in msg for k in ["login", "mfa", "token", "sso", "access", "travel", "spray"]):
        label = "auth_failure"
    elif any(k in msg for k in ["billing", "invoice", "card", "refund", "subscription", "charge"]):
        label = "payment_error"
    elif any(k in msg for k in ["ingest", "schema", "dedupe", "encoding", "utf-8", "rejected", "conflicting"]):
        label = "data_quality"
    elif any(k in msg for k in ["release", "canary", "flag", "migration", "restart", "pinned"]):
        label = "deploy_event"
    else:
        label = "support_noise"
        
    classified_records.append({"id": entry["id"], "label": label})

# Sort explicitly by ID sequence
classified_records.sort(key=lambda x: x["id"])

# Write sorted records to final output file
with open("classified.jsonl", "w") as out:
    for record in classified_records:
        out.write(json.dumps(record, separators=(',', ':')) + "\n")

# Calculate validation signature hash
with open("classified.jsonl", "rb") as final_file:
    file_hash = hashlib.sha256(final_file.read()).hexdigest()

print(f"\nFinal signature hash:\n{file_hash}  classified.jsonl")
