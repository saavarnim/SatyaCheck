"""tools/seed_demo_reports.py – Seed rich realistic demo reports into satyacheck.db."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from app.db import SessionLocal
from app.models import Indicator, Report
from app.normalise import normalise

# Specific alert test seeds matching judging criteria:
# 1. 560102 (HSR Layout): 14 baseline reports over prior 7 days (~2/day) + 10 recent in last 20 hours -> SPIKE
# 2. 110016 (Hauz Khas): 4 baseline otp-call over prior 3-18 days + 1 recent job-offer in last 3 hours -> NEW_TYPE
# 3. 560064 (Yelahanka): 14 baseline reports + 2 recent -> Normal (NO alert)
# 4. 400050 (Bandra West): 8 recent reports + 10 month-old reports (excluded from 7-day map)
# 5. 500081 (Madhapur): 7 independent reports in last 5 days
SPECIFIC_ALERT_SEEDS = [
    # 560102: 14 baseline + 10 recent
    {
        "pincode": "560102",
        "baseline": [
            ("digital-arrest", "call", "phone", "+9198765432{:02d}", "CBI officer video call arrest threat", 30 + i * 11)
            for i in range(14)
        ],
        "recent": [
            ("digital-arrest", "call", "phone", "+9198765431{:02d}", "Fake arrest warrant over phone call", 1 + i * 1.8)
            for i in range(10)
        ],
    },
    # 110016: 4 baseline otp-call + 1 recent job-offer
    {
        "pincode": "110016",
        "baseline": [
            ("otp-call", "call", "phone", "+9198110016{:02d}", "Asking for bank OTP and card expiry", d * 24)
            for d in (3, 6, 10, 18)
        ],
        "recent": [
            ("job-offer", "telegram", "phone", "+919811009999", "Part-time hotel review job deposit requested", 3.0),
        ],
    },
    # 560064: 14 baseline + 2 recent
    {
        "pincode": "560064",
        "baseline": [
            ("digital-arrest" if i % 2 == 0 else "courier-customs", "call", "phone", "+9198765464{:02d}", "Normal baseline sighting", 30 + i * 11)
            for i in range(14)
        ],
        "recent": [
            ("courier-customs", "call", "phone", "+919876546498", "Courier parcel query", 5.0),
            ("digital-arrest", "call", "phone", "+919876546499", "Suspicious phone caller", 14.0),
        ],
    },
    # 400050: 8 recent + 10 month-old (32 days ago)
    {
        "pincode": "400050",
        "baseline": [
            ("investment-group", "whatsapp", "upi", "crypto-vip-{:02d}@icici", "Old trading group inquiry", 32 * 24 + i * 4)
            for i in range(10)
        ],
        "recent": [
            ("investment-group", "whatsapp", "upi", "stock-tips-{:02d}@icici", "Telegram stock trading VIP club", 2 + i * 2.5)
            for i in range(8)
        ],
    },
    # 500081: 7 recent in last 5 days
    {
        "pincode": "500081",
        "baseline": [],
        "recent": [
            ("fake-customer-care", "call", "phone", "+9195001122{:02d}", "Fake Google Pay helpline asking AnyDesk", 4 + i * 12)
            for i in range(7)
        ],
    },
    # 560038: 7 reports
    {
        "pincode": "560038",
        "baseline": [
            ("upi-refund-qr", "whatsapp", "upi", "refund-support-{:02d}@okaxis", "Sent QR code claiming refund", 40 + i * 15)
            for i in range(4)
        ],
        "recent": [
            ("digital-arrest", "call", "phone", "+9198112233{:02d}", "Customs police drug parcel call", 2 + i * 3)
            for i in range(6)
        ],
    },
]

def seed_demo_reports(db=None):
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        now = datetime.now(timezone.utc)
        created_count = 0

        for block in SPECIFIC_ALERT_SEEDS:
            pincode = block["pincode"]
            all_entries = block["baseline"] + block["recent"]

            for idx, entry in enumerate(all_entries):
                scam_type, channel, id_type, id_base, note_tmpl, hours_ago = entry
                raw_val = id_base.format(idx) if "{:02d}" in id_base else id_base
                try:
                    canon = normalise(id_type, raw_val)
                except Exception:
                    canon = raw_val

                indicator = db.query(Indicator).filter_by(type=id_type, canonical_value=canon).first()
                if not indicator:
                    indicator = Indicator(type=id_type, canonical_value=canon)
                    db.add(indicator)
                    db.flush()

                case_id = f"CASE-{hashlib.sha256(f'{id_type}:{canon}'.encode()).hexdigest()[:8].upper()}"
                dt = now - timedelta(hours=hours_ago)

                # Distinct reporter and IP tokens so each forms a genuine trusted voice
                rep_token = hashlib.sha256(f"voice_{pincode}_{scam_type}_{idx}_{raw_val}".encode()).hexdigest()[:16]
                ip_token = hashlib.sha256(f"ip_{pincode}_{scam_type}_{idx}_{hours_ago}".encode()).hexdigest()[:16]

                report = Report(
                    report_id=f"REP-{uuid.uuid4().hex[:12].upper()}",
                    case_id=case_id,
                    indicator_id=indicator.id,
                    occurred_at=dt,
                    reported_at=dt + timedelta(minutes=5),
                    reporter_token=rep_token,
                    ip_token=ip_token,
                    channel=channel,
                    scam_type=scam_type,
                    pincode=pincode,
                    note_redacted=f"{note_tmpl} incident number {idx + 1} with details",
                    has_screenshot=(idx % 2 == 0),
                    amount_lost_inr=float(idx * 2500) if idx % 3 == 0 else 0.0,
                )
                db.add(report)
                created_count += 1

        db.commit()
        print(f"Successfully seeded {created_count} rich demo reports into database.")
        return created_count
    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    db = SessionLocal()
    db.query(Report).delete()
    db.commit()
    seed_demo_reports(db)
    db.close()

