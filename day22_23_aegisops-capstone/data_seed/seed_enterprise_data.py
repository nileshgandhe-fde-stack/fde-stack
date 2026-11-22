"""Generate synthetic, noisy enterprise alerts, post-mortems, and SLA metrics."""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SERVICES = ("payments-api", "identity-service", "order-worker", "customer-portal", "ledger-db")
REGIONS = ("us-east-1", "us-west-2", "eu-west-1", "ap-southeast-2")
TEAMS = ("Payments", "Platform", "Identity", "Data Operations", "Customer Experience")
ALERT_TITLES = (
    "High request latency",
    "Elevated 5xx error rate",
    "Worker queue backlog",
    "Database connection saturation",
    "Pod restart threshold exceeded",
)


def _timestamp(rng: random.Random, start: datetime, days: int) -> str:
    value = start + timedelta(seconds=rng.randint(0, days * 86_400))
    return value.isoformat().replace("+00:00", "Z")


def _alert(index: int, rng: random.Random, start: datetime) -> dict[str, object]:
    source = rng.choice(("pagerduty", "prometheus"))
    service = rng.choice(SERVICES)
    region = rng.choice(REGIONS)
    title = rng.choice(ALERT_TITLES)
    severity = rng.choices(("critical", "high", "warning", "info"), (12, 28, 48, 12))[0]
    timestamp = _timestamp(rng, start - timedelta(days=365), 365)
    summary = f"{title} for {service} in {region}"
    if rng.random() < 0.08:
        summary = f"  {summary.lower()}  "
    if rng.random() < 0.05:
        summary = summary.replace("latency", "latncy").replace("threshold", "threshhold")

    common: dict[str, object] = {
        "alert_id": f"{'PD' if source == 'pagerduty' else 'PROM'}-{index:06d}",
        "source": source,
        "service": service,
        "region": region,
        "severity": severity,
        "summary": summary,
        "labels": {
            "team": rng.choice(TEAMS),
            "environment": rng.choice(("production", "staging", "production", "production")),
            "tenant_id": f"tenant-{rng.randint(1, 100):04d}",
        },
        "created_at": timestamp,
    }
    if source == "pagerduty":
        common["event"] = {
            "incident_key": f"inc-{index:06d}",
            "status": rng.choice(("triggered", "acknowledged", "resolved")),
            "urgency": "high" if severity in ("critical", "high") else "low",
            "acknowledged_by": rng.choice(("on-call-primary", "on-call-secondary", None)),
            "resolve_seconds": rng.randint(45, 28_800),
        }
    else:
        common["event"] = {
            "alertname": title.replace(" ", ""),
            "fingerprint": f"{rng.getrandbits(64):016x}",
            "startsAt": timestamp,
            "endsAt": (
                None
                if rng.random() < 0.65
                else _timestamp(rng, start - timedelta(days=30), 30)
            ),
            "value": round(rng.uniform(0.1, 99.9), 3),
            "threshold": round(rng.uniform(1, 95), 2),
        }
    if rng.random() < 0.03:
        common["labels"]["deployment"] = ""
    return common


def _postmortem(index: int, rng: random.Random, start: datetime) -> str:
    service = rng.choice(SERVICES)
    team = rng.choice(TEAMS)
    region = rng.choice(REGIONS)
    happened = _timestamp(rng, start - timedelta(days=365), 365)
    duration = rng.randint(8, 240)
    contact_index = index % 90 + 10
    contact_name = rng.choice(("Alex Morgan", "Jordan Lee", "Taylor Kim", "Casey Patel"))
    contact_email = f"contact{contact_index:03d}@example.com"
    contact_phone = f"+1-202-555-01{contact_index:02d}"
    impact = rng.choice(
        (
            "Checkout requests timed out for a subset of tenants.",
            "Background reconciliation fell behind its normal processing window.",
            "Some users saw intermittent authentication failures.",
            "Read replicas returned stale data while the primary recovered.",
        )
    )
    noisy_note = rng.choice(
        ("", "A few timestamps in the source ticket were approximate.\n", "Initial impact estimates were revised during review.\n")
    )
    return f"""# Post-mortem: {service} incident INC-{index:05d}

## Summary

On {happened}, the {service} service in {region} experienced an interruption lasting
approximately {duration} minutes. {impact}
{noisy_note}
## Impact

- Affected service: `{service}`
- Responsible team: {team}
- Severity: {rng.choice(("SEV-1", "SEV-2", "SEV-3"))}
- Customer impact window: {duration} minutes
- Tenant impact estimate: {rng.randint(3, 47)} tenants

## Timeline

- {happened} — Alert fired; on-call engineer acknowledged the incident.
- {duration // 2} minutes later — Mitigation started and error rate began to fall.
- {duration} minutes later — Recovery confirmed; follow-up monitoring enabled.

## Root cause and resolution

{rng.choice(("A recent deployment increased connection pool pressure.", "A dependency slowdown caused retries to amplify queue load.", "A configuration drift reduced available worker capacity."))}
The team rolled back the change, drained the affected queue, and verified recovery
against the service-level objective.

## Follow-up actions

1. Add a regression test for the failure mode.
2. Tune the alert threshold and document the operational runbook.
3. Review the tenant communication process with the service owner.

## Customer contact (synthetic)

{contact_name} | {contact_email} | {contact_phone}
"""


def _sla_row(index: int, rng: random.Random, start: datetime) -> dict[str, object]:
    target = rng.choice((99.5, 99.9, 99.95, 99.99))
    observed = round(max(90.0, min(100.0, rng.gauss(target - 0.08, 0.2))), 5)
    requests = rng.randint(2_000, 8_000_000)
    errors = round(requests * (100.0 - observed) / 100.0)
    status = "breached" if observed < target - 0.1 else "at_risk" if observed < target else "within_sla"
    note = rng.choice(
        (
            "monthly aggregate",
            "late-arriving metrics reconciled",
            "source export contains rounded percentages",
            "backfill window applied",
        )
    )
    if rng.random() < 0.025:
        note = f" {note} "
    return {
        "sla_id": f"SLA-{index:07d}",
        "measured_at": _timestamp(rng, start - timedelta(days=365), 365),
        "tenant_id": f"tenant-{rng.randint(1, 100):04d}",
        "service": rng.choice(SERVICES),
        "region": rng.choice(REGIONS),
        "monthly_target_pct": target,
        "observed_pct": observed,
        "request_count": requests,
        "error_count": errors,
        "status": status,
        "source_note": note,
    }


def generate(
    output_dir: str | Path,
    *,
    seed: int = 42,
    alert_count: int = 1_000,
    postmortem_count: int = 50,
    sla_row_count: int = 10_000,
    as_of: datetime | None = None,
) -> tuple[Path, Path, Path]:
    """Generate the three seed datasets and return their output paths."""
    if min(alert_count, postmortem_count, sla_row_count) < 0:
        raise ValueError("Record counts cannot be negative")

    rng = random.Random(seed)
    output = Path(output_dir)
    docs_dir = output / "postmortems"
    docs_dir.mkdir(parents=True, exist_ok=True)
    start = as_of or datetime.now(timezone.utc)
    if start.tzinfo is None:
        raise ValueError("as_of must include a timezone")
    start = start.astimezone(timezone.utc).replace(microsecond=0)

    alerts_path = output / "alerts.jsonl"
    with alerts_path.open("w", encoding="utf-8") as file:
        for index in range(1, alert_count + 1):
            file.write(json.dumps(_alert(index, rng, start), ensure_ascii=False) + "\n")

    for index in range(1, postmortem_count + 1):
        path = docs_dir / f"incident-{index:05d}.md"
        path.write_text(_postmortem(index, rng, start), encoding="utf-8")

    sla_path = output / "tenant_sla.csv"
    columns = (
        "sla_id",
        "measured_at",
        "tenant_id",
        "service",
        "region",
        "monthly_target_pct",
        "observed_pct",
        "request_count",
        "error_count",
        "status",
        "source_note",
    )
    with sla_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(_sla_row(index, rng, start) for index in range(1, sla_row_count + 1))

    return alerts_path, docs_dir, sla_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "generated")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--as-of",
        type=lambda value: datetime.fromisoformat(value.replace("Z", "+00:00")),
        help="UTC reference time (ISO 8601); combine with --seed for repeatable output",
    )
    args = parser.parse_args()
    alerts, postmortems, sla = generate(args.output_dir, seed=args.seed, as_of=args.as_of)
    print(f"Generated alerts: {alerts}")
    print(f"Generated post-mortems: {postmortems}")
    print(f"Generated SLA rows: {sla}")


if __name__ == "__main__":
    main()
