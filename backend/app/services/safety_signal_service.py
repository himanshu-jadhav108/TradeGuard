import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.domain.models import AuditEvent, SafetySignal, SafetySignalsReport


class SafetySignalService:
    @staticmethod
    def compute_signals(session_id: str, events: List[AuditEvent]) -> SafetySignalsReport:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        def parse_ts(ts_str: str) -> float:
            try:
                clean = ts_str.replace("Z", "+00:00")
                return datetime.fromisoformat(clean).timestamp()
            except Exception:
                return 0.0

        # Filter proposal creation events
        proposal_events = [e for e in events if e.event_type in ("RISK_EVALUATED", "PROPOSAL_CREATED")]
        sorted_proposals = sorted(proposal_events, key=lambda e: parse_ts(e.timestamp))

        # 1. Duplicate identical proposals in a short window (60s)
        duplicate_count = 0
        duplicate_details: List[Dict[str, Any]] = []

        for i in range(len(sorted_proposals)):
            cur = sorted_proposals[i]
            cur_ts = parse_ts(cur.timestamp)
            cur_meta = cur.metadata or {}
            cur_asset = cur_meta.get("asset")
            cur_side = cur_meta.get("side")
            cur_amt = cur_meta.get("amount")

            for j in range(i - 1, -1, -1):
                prev = sorted_proposals[j]
                prev_ts = parse_ts(prev.timestamp)
                if (cur_ts - prev_ts) > 60:
                    break
                prev_meta = prev.metadata or {}
                if (
                    cur_asset
                    and cur_side
                    and cur_amt is not None
                    and cur_asset == prev_meta.get("asset")
                    and cur_side == prev_meta.get("side")
                    and cur_amt == prev_meta.get("amount")
                ):
                    duplicate_count += 1
                    duplicate_details.append({
                        "proposal_id": cur.proposal_id,
                        "asset": cur_asset,
                        "side": cur_side,
                        "amount": cur_amt,
                        "interval_seconds": round(cur_ts - prev_ts, 2),
                    })
                    break

        signal_duplicates = SafetySignal(
            id="sig-duplicates",
            name="Duplicate Proposals in Short Window",
            description="Identical trade proposals (same asset, side, amount) staged within 60 seconds of each other.",
            count=duplicate_count,
            severity="WARN" if duplicate_count > 0 else "INFO",
            details={"duplicates": duplicate_details, "window_seconds": 60},
        )

        # 2. Proposals per minute per session
        recent_proposals = [
            e for e in proposal_events
            if (now.timestamp() - parse_ts(e.timestamp)) <= 60
        ]
        proposals_last_min = len(recent_proposals)

        if sorted_proposals:
            first_ts = parse_ts(sorted_proposals[0].timestamp)
            span_minutes = max((now.timestamp() - first_ts) / 60.0, 1.0)
            avg_ppm = round(len(sorted_proposals) / span_minutes, 2)
        else:
            avg_ppm = 0.0

        signal_rate = SafetySignal(
            id="sig-rate",
            name="Proposals Velocity (Per Minute)",
            description="Rate of trade proposals staged per minute in this active session.",
            count=proposals_last_min,
            severity="CRITICAL" if proposals_last_min > 10 else ("WARN" if proposals_last_min > 5 else "INFO"),
            details={
                "proposals_last_60s": proposals_last_min,
                "lifetime_proposals": len(proposal_events),
                "average_per_minute": avg_ppm,
            },
        )

        # 3. Repeated rejected confirmations
        reject_events = [e for e in events if e.event_type == "CONFIRM_REJECTED"]
        rejection_reasons: Dict[str, int] = {}
        for r in reject_events:
            reason = (r.metadata or {}).get("reason", "UNKNOWN")
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

        signal_rejections = SafetySignal(
            id="sig-rejected-confirms",
            name="Repeated Rejected Confirmations",
            description="Executions blocked by deterministic risk gates, unacknowledged warnings, or balance checks.",
            count=len(reject_events),
            severity="CRITICAL" if len(reject_events) >= 5 else ("WARN" if len(reject_events) >= 2 else "INFO"),
            details={"by_reason": rejection_reasons},
        )

        # 4. Expired-quote confirm attempts
        expired_events = [
            e for e in events
            if e.event_type == "PROPOSAL_EXPIRED"
            or (
                e.event_type == "CONFIRM_REJECTED"
                and (e.metadata or {}).get("reason") in ("EXPIRED_QUOTE", "PROPOSAL_ALREADY_EXPIRED")
            )
        ]
        signal_expired = SafetySignal(
            id="sig-expired-quotes",
            name="Expired Quote Confirmation Attempts",
            description="Attempts to confirm trades after the 30-second quote validity window has elapsed.",
            count=len(expired_events),
            severity="WARN" if len(expired_events) >= 1 else "INFO",
            details={"total_expired_events": len(expired_events)},
        )

        return SafetySignalsReport(
            session_id=session_id,
            signals=[signal_duplicates, signal_rate, signal_rejections, signal_expired],
            total_stored_events=len(events),
            computed_at=now_iso,
            label="rule-based safety signals",
        )
