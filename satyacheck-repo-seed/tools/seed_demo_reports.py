"""tools/seed_demo_reports.py – Seed rich realistic demo reports into satyacheck.db."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from app.db import SessionLocal
from app.models import Indicator, Report
from app.normalise import normalise

# Generate diverse distinct reports per area to give CRIT (>=10), HIGH (5-9), MED (1-4)
AREA_SEEDS = [
    # (pincode, count, [(scam_type, channel, id_type, id_base, note_template)])
    ("560102", 12, [
        ("digital-arrest", "call", "phone", "+9198765432{:02d}", "CBI officer video call arrest threat"),
        ("fake-kyc-link", "sms", "url", "https://sbi-alert-verify-{:02d}.in", "SMS saying KYC will expire today"),
    ]),
    ("560038", 7, [
        ("upi-refund-qr", "whatsapp", "upi", "refund-support-{:02d}@okaxis", "Sent QR code claiming refund"),
        ("digital-arrest", "call", "phone", "+9198112233{:02d}", "Customs police drug parcel call"),
    ]),
    ("560103", 6, [
        ("courier-customs", "call", "phone", "+9197112233{:02d}", "Courier customs seized parcel fee"),
    ]),
    ("400050", 8, [
        ("investment-group", "whatsapp", "upi", "crypto-vip-{:02d}@icici", "Telegram stock trading VIP club"),
        ("fake-kyc-link", "sms", "url", "https://bank-kyc-pan-{:02d}.com", "Urgent PAN card verification SMS"),
    ]),
    ("560034", 4, [
        ("job-offer", "telegram", "phone", "+9198223344{:02d}", "Part-time hotel review job fee"),
    ]),
    ("560066", 3, [
        ("investment-group", "whatsapp", "url", "https://trade-signals-{:02d}.org", "WhatsApp crypto investment scheme"),
    ]),
    ("110016", 4, [
        ("fake-kyc-link", "sms", "sender_id", "VK-SB{:02d}", "Electricity disconnection KYC warning"),
    ]),
    ("560076", 2, [
        ("electricity-disconnection", "sms", "phone", "+9196554433{:02d}", "Power supply disconnection threat"),
    ]),
    ("500081", 2, [
        ("fake-customer-care", "call", "phone", "+9195001122{:02d}", "Fake Google Pay helpline asking AnyDesk"),
    ]),
    ("411014", 3, [
        ("digital-arrest", "call", "phone", "+9193332211{:02d}", "Supreme court video notice digital arrest"),
    ]),
    ("600020", 1, [
        ("otp-call", "call", "phone", "+9194443322{:02d}", "Card division asking for CVV and OTP"),
    ]),
]

def seed_demo_reports():
    db = SessionLocal()
    try:
        # Clear existing non-seed reports
        db.query(Report).delete()
        now = datetime.now(timezone.utc)
        created_count = 0

        for pincode, target_count, configs in AREA_SEEDS:
            for idx in range(target_count):
                scam_type, channel, id_type, id_base, note_tmpl = configs[idx % len(configs)]
                raw_val = id_base.format(idx)
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
                hours = 1 + (idx * 5) % 70
                dt = now - timedelta(hours=hours)

                # Distinct reporter and IP tokens so each forms a genuine trusted voice
                rep_token = hashlib.sha256(f"unique_voice_{pincode}_{idx}_{raw_val}".encode()).hexdigest()[:16]
                ip_token = hashlib.sha256(f"unique_ip_{pincode}_{idx}_{idx * 3}".encode()).hexdigest()[:16]

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
        print(f"Successfully seeded {created_count} rich demo reports into satyacheck.db.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_reports()
