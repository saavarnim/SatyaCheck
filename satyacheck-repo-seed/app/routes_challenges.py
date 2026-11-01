import html
import os
from datetime import timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app import clock, config
from app.clock import to_ist_iso
from app.db import get_db
from app.models import Challenge, Indicator, Report, VerifiedIndicator
from app.normalise import normalise, InvalidIdentifier

router = APIRouter()


class ChallengeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    identifier_type: Optional[str] = None
    identifier_value: Optional[str] = None
    claimant_name: Optional[str] = None
    contact_email: Optional[str] = None
    proof_note: Optional[str] = None


class ChallengeResolveRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision: Optional[str] = None  # "upheld" | "rejected"


def _is_demo_mode() -> bool:
    """Return True if DEMO_MODE is enabled via config or env."""
    return getattr(config, "DEMO_MODE", False) or os.getenv("DEMO_MODE", "false").lower() == "true"


def _ensure_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.post("/challenges", status_code=201)
def post_challenge(
    payload: ChallengeCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Submit a dispute with business proof.
    (docs/01-api.md)
    """
    # 1. Validate required fields
    if not payload.identifier_type or not payload.identifier_value:
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})
    if not payload.claimant_name or not payload.claimant_name.strip():
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})
    if not payload.contact_email or not payload.contact_email.strip():
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    # 2. Normalise identifier
    try:
        norm_type = payload.identifier_type.strip().lower()
        if norm_type not in config.IDENTIFIER_TYPES:
            return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})
        canon_val = normalise(norm_type, payload.identifier_value)
    except (InvalidIdentifier, Exception):
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    now = _ensure_utc(clock.now())

    # 3. Find or create indicator
    indicator = (
        db.query(Indicator)
        .filter_by(type=norm_type, canonical_value=canon_val)
        .first()
    )

    if indicator is not None:
        # Check 7-day cooldown on recent rejection
        cutoff_7d = now - timedelta(days=7)
        recent_rejected = (
            db.query(Challenge)
            .filter(
                Challenge.indicator_id == indicator.id,
                Challenge.status == "rejected",
                Challenge.resolved_at > cutoff_7d,
            )
            .first()
        )
        if recent_rejected is not None:
            return JSONResponse(status_code=409, content={"error": "CHALLENGE_BLOCKED"})

        # Check existing under_review challenge -> return 201 with existing id
        existing = (
            db.query(Challenge)
            .filter_by(indicator_id=indicator.id, status="under_review")
            .first()
        )
        if existing is not None:
            return JSONResponse(
                status_code=201,
                content={
                    "challenge_id": f"CH-{existing.id:06d}",
                    "status": "under_review",
                },
            )
    else:
        # Create indicator row
        indicator = Indicator(type=norm_type, canonical_value=canon_val)
        db.add(indicator)
        db.commit()
        db.refresh(indicator)

    # 4. Insert new challenge
    new_challenge = Challenge(
        indicator_id=indicator.id,
        claimant_name=payload.claimant_name.strip(),
        contact_email=payload.contact_email.strip(),
        proof_note=(payload.proof_note or "").strip(),
        status="under_review",
        created_at=now,
    )
    db.add(new_challenge)
    db.commit()
    db.refresh(new_challenge)

    return JSONResponse(
        status_code=201,
        content={
            "challenge_id": f"CH-{new_challenge.id:06d}",
            "status": "under_review",
        },
    )


@router.get("/admin/challenges")
def admin_list_challenges(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    db: Session = Depends(get_db),
):
    """
    List under-review challenges. Protected by X-Admin-Token.
    (docs/01-api.md)
    """
    if not x_admin_token or x_admin_token != config.ADMIN_TOKEN:
        return JSONResponse(status_code=403, content={"error": "FORBIDDEN"})

    challenges = (
        db.query(Challenge)
        .filter_by(status="under_review")
        .order_by(Challenge.created_at.asc())
        .all()
    )

    items = []
    for c in challenges:
        ind = db.query(Indicator).filter_by(id=c.indicator_id).first()
        items.append({
            "challenge_id": f"CH-{c.id:06d}",
            "indicator_type": ind.type if ind else None,
            "indicator_value": ind.canonical_value if ind else None,
            "claimant_name": c.claimant_name,
            "contact_email": c.contact_email,
            "proof_note": c.proof_note,
            "status": c.status,
            "created_at": to_ist_iso(c.created_at),
        })

    return {"challenges": items}


def _render_auth_form_html(error: Optional[str] = None) -> str:
    err_html = f'<div style="background:#fef2f2; border:1px solid #fecaca; color:#991b1b; padding:10px 14px; border-radius:6px; margin-bottom:16px; font-size:0.85rem;">{html.escape(error)}</div>' if error else ''
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Admin Review Access • SatyaCheck</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #0f172a; display: flex; justify-content: center; align-items: center; min-height: 85vh; padding: 20px; }}
    .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; width: 100%; max-width: 400px; padding: 28px; box-shadow: 0 4px 14px rgba(0,0,0,0.06); }}
    h2 {{ font-size: 1.25rem; font-weight: 800; margin-bottom: 6px; color: #0f172a; }}
    p {{ font-size: 0.88rem; color: #64748b; margin-bottom: 20px; line-height: 1.5; }}
    label {{ display: block; font-size: 0.82rem; font-weight: 700; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.03em; color: #475569; }}
    input {{ width: 100%; box-sizing: border-box; padding: 11px 13px; font-size: 0.95rem; border: 1px solid #cbd5e1; border-radius: 6px; margin-bottom: 16px; }}
    button {{ width: 100%; background: #0284c7; color: white; border: none; padding: 11px; font-size: 0.95rem; font-weight: 700; border-radius: 6px; cursor: pointer; transition: background 0.15s ease; }}
    button:hover {{ background: #0369a1; }}
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size: 2rem; margin-bottom: 10px;">🔐</div>
    <h2>Admin Review Portal</h2>
    <p>Please enter your administrative access token to inspect challenged business reports.</p>
    {err_html}
    <form method="GET" action="/admin/reviews">
      <label for="token">Admin Access Token</label>
      <input type="password" id="token" name="token" placeholder="Enter ADMIN_TOKEN" required autofocus />
      <button type="submit">Access Reviews Portal</button>
    </form>
    <div style="margin-top: 16px; text-align: center;">
      <a href="/#/" style="font-size: 0.82rem; color: #64748b; text-decoration: none;">← Return to Main App</a>
    </div>
  </div>
</body>
</html>
"""


def _render_reviews_html(reviews: list[dict], token: str, current_filter: str, total_counts: dict) -> str:
    rows_html = ""
    for r in reviews:
        status = r["status"]
        status_badge_class = (
            "status-pending" if status == "under_review" else
            "status-upheld" if status == "upheld" else "status-rejected"
        )
        status_label = (
            "Under Review" if status == "under_review" else
            "Upheld (Verified)" if status == "upheld" else "Rejected (Cooldown)"
        )
        actions_html = ""
        if status == "under_review":
            actions_html = f"""
            <div class="actions-group">
              <button class="btn btn-uphold" onclick="resolveReview('{r['challenge_id']}', 'upheld')">✔️ Uphold</button>
              <button class="btn btn-reject" onclick="resolveReview('{r['challenge_id']}', 'rejected')">❌ Reject</button>
            </div>
            """
        else:
            actions_html = f"""<span class="resolved-note">Resolved at {html.escape(r.get('resolved_at') or 'N/A')}</span>"""

        email_link = f"""<a href="mailto:{html.escape(r['contact_email'])}?subject=SatyaCheck%20Dispute%20Review%20{html.escape(r['challenge_id'])}&body=Hello%20{html.escape(r['claimant_name'])},%0D%0A%0D%0ARegarding%20your%20dispute%20for%20{html.escape(r['indicator_value'])}:%0D%0A" class="email-link">📧 {html.escape(r['contact_email'])}</a>"""
        proof_display = html.escape(r['proof_note']) if r['proof_note'] else '<em style="color:#94a3b8">No proof note submitted</em>'

        rows_html += f"""
        <tr id="row-{r['challenge_id']}">
          <td><strong class="ch-id">{html.escape(r['challenge_id'])}</strong><br><small class="text-muted">{html.escape(r['created_at'])}</small></td>
          <td>
            <span class="badge-type">{html.escape(r['indicator_type'].upper())}</span>
            <code class="val-code">{html.escape(r['indicator_value'])}</code>
            <div class="sightings-badge">📊 {r['report_count']} community sighting{'s' if r['report_count'] != 1 else ''}</div>
          </td>
          <td>
            <div class="claimant-name">{html.escape(r['claimant_name'])}</div>
            <div>{email_link}</div>
          </td>
          <td class="proof-cell">{proof_display}</td>
          <td><span class="status-badge {status_badge_class}" id="badge-{r['challenge_id']}">{status_label}</span></td>
          <td id="actions-{r['challenge_id']}">{actions_html}</td>
        </tr>
        """

    if not reviews:
        rows_html = """<tr><td colspan="6" style="text-align:center; padding: 40px 20px; color: #64748b;">No challenged reviews found matching this filter.</td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SatyaCheck Admin • Challenged Reviews</title>
  <style>
    :root {{
      --primary: #0284c7;
      --primary-dark: #0369a1;
      --bg: #f8fafc;
      --surface: #ffffff;
      --border: #e2e8f0;
      --text: #0f172a;
      --text-muted: #64748b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 16px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .brand-icon {{
      background: #0284c7;
      color: white;
      font-weight: 900;
      width: 38px;
      height: 38px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.2rem;
    }}
    h1 {{ font-size: 1.4rem; font-weight: 800; color: #0f172a; }}
    .subtitle {{ font-size: 0.85rem; color: var(--text-muted); }}
    .nav-actions {{ display: flex; align-items: center; gap: 10px; }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 12px;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      text-decoration: none;
      border: 1px solid transparent;
      transition: all 0.15s ease;
    }}
    .btn-secondary {{
      background: #fff;
      border-color: var(--border);
      color: #334155;
    }}
    .btn-secondary:hover {{ background: #f1f5f9; }}
    .btn-uphold {{
      background: #10b981;
      color: #fff;
    }}
    .btn-uphold:hover {{ background: #059669; }}
    .btn-reject {{
      background: #ef4444;
      color: #fff;
    }}
    .btn-reject:hover {{ background: #dc2626; }}
    
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }}
    .stat-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 18px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }}
    .stat-val {{ font-size: 1.6rem; font-weight: 800; color: #0f172a; }}
    .stat-label {{ font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }}

    .tabs-bar {{
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .tab-link {{
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 0.88rem;
      font-weight: 600;
      text-decoration: none;
      color: #64748b;
      background: #e2e8f0;
      transition: all 0.15s ease;
    }}
    .tab-link:hover {{ background: #cbd5e1; }}
    .tab-link.active {{
      background: var(--primary);
      color: #fff;
    }}

    .table-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow-x: auto;
      box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.88rem;
    }}
    th {{
      background: #f1f5f9;
      color: #475569;
      font-weight: 700;
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    td {{
      padding: 14px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #fafafa; }}
    
    .ch-id {{ font-family: monospace; font-size: 0.95rem; color: #1e293b; }}
    .val-code {{ font-family: monospace; font-size: 0.95rem; font-weight: 600; color: #0f172a; display: inline-block; margin-top: 4px; }}
    .badge-type {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      background: #e0f2fe;
      color: #0369a1;
      display: inline-block;
    }}
    .sightings-badge {{
      font-size: 0.75rem;
      color: #64748b;
      margin-top: 4px;
    }}
    .claimant-name {{ font-weight: 700; color: #1e293b; }}
    .email-link {{ color: #0284c7; text-decoration: none; font-size: 0.82rem; word-break: break-all; }}
    .email-link:hover {{ text-decoration: underline; }}
    .proof-cell {{ max-width: 280px; font-size: 0.84rem; color: #334155; line-height: 1.4; }}
    
    .status-badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .status-pending {{ background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }}
    .status-upheld {{ background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }}
    .status-rejected {{ background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }}

    .actions-group {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .resolved-note {{ font-size: 0.75rem; color: var(--text-muted); }}
    .text-muted {{ color: var(--text-muted); font-size: 0.75rem; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="brand-icon">✓</div>
        <div>
          <h1>SatyaCheck • Trust & Safety Review</h1>
          <p class="subtitle">Dispute review desk for business verification and identifier claims</p>
        </div>
      </div>
      <div class="nav-actions">
        <a href="/#/" class="btn btn-secondary">← Back to App</a>
        <a href="/admin/reviews?token={html.escape(token)}" class="btn btn-secondary">🔄 Refresh</a>
      </div>
    </header>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-val">{total_counts['total']}</div>
        <div class="stat-label">Total Challenges</div>
      </div>
      <div class="stat-card" style="border-left: 4px solid #f59e0b;">
        <div class="stat-val" style="color: #b45309;">{total_counts['under_review']}</div>
        <div class="stat-label">Pending Review</div>
      </div>
      <div class="stat-card" style="border-left: 4px solid #10b981;">
        <div class="stat-val" style="color: #047857;">{total_counts['upheld']}</div>
        <div class="stat-label">Upheld (Verified)</div>
      </div>
      <div class="stat-card" style="border-left: 4px solid #ef4444;">
        <div class="stat-val" style="color: #b91c1c;">{total_counts['rejected']}</div>
        <div class="stat-label">Rejected (Cooldown)</div>
      </div>
    </div>

    <div class="tabs-bar">
      <a href="/admin/reviews?token={html.escape(token)}" class="tab-link {'active' if not current_filter else ''}">All ({total_counts['total']})</a>
      <a href="/admin/reviews?token={html.escape(token)}&status=under_review" class="tab-link {'active' if current_filter == 'under_review' else ''}">Under Review ({total_counts['under_review']})</a>
      <a href="/admin/reviews?token={html.escape(token)}&status=upheld" class="tab-link {'active' if current_filter == 'upheld' else ''}">Upheld ({total_counts['upheld']})</a>
      <a href="/admin/reviews?token={html.escape(token)}&status=rejected" class="tab-link {'active' if current_filter == 'rejected' else ''}">Rejected ({total_counts['rejected']})</a>
    </div>

    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>ID / Date</th>
            <th>Target Identifier</th>
            <th>Claimant & Contact</th>
            <th>Proof / Justification</th>
            <th>Review Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
  </div>

  <script>
    const adminToken = "{html.escape(token)}";

    async function resolveReview(challengeId, decision) {{
      const verb = decision === 'upheld' ? 'UPHOLD and VERIFY' : 'REJECT';
      if (!confirm(`Are you sure you want to ${{verb}} challenge ${{challengeId}}?`)) return;

      const actCell = document.getElementById(`actions-${{challengeId}}`);
      if (actCell) actCell.innerHTML = '<span class="text-muted">Processing...</span>';

      try {{
        const res = await fetch(`/admin/challenges/${{challengeId}}/resolve?token=${{encodeURIComponent(adminToken)}}`, {{
          method: 'POST',
          headers: {{
            'Content-Type': 'application/json',
            'X-Admin-Token': adminToken
          }},
          body: JSON.stringify({{ decision: decision }})
        }});

        if (res.ok) {{
          const data = await res.json();
          const badge = document.getElementById(`badge-${{challengeId}}`);
          if (badge) {{
            badge.className = decision === 'upheld' ? 'status-badge status-upheld' : 'status-badge status-rejected';
            badge.textContent = decision === 'upheld' ? 'Upheld (Verified)' : 'Rejected (Cooldown)';
          }}
          if (actCell) {{
            actCell.innerHTML = `<span class="resolved-note">Marked as ${{decision}} just now</span>`;
          }}
          alert(`Success: ${{challengeId}} resolved as ${{decision}}.`);
        }} else {{
          const err = await res.json();
          alert(`Resolution failed: ${{err.error || 'Server error'}}`);
          window.location.reload();
        }}
      }} catch (e) {{
        alert('Network error while resolving review.');
        window.location.reload();
      }}
    }}
  </script>
</body>
</html>
"""


@router.get("/admin/reviews")
def admin_reviews_portal(
    request: Request,
    token: Optional[str] = Query(None),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    status: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Admin portal to access and resolve challenged reviews.
    Accepts token via X-Admin-Token header or ?token= query parameter.
    Outputs HTML dashboard by default, or JSON if requested.
    """
    effective_token = x_admin_token or token
    wants_json = format == "json" or request.headers.get("accept", "").startswith("application/json")

    if not effective_token:
        if wants_json:
            return JSONResponse(status_code=403, content={"error": "FORBIDDEN"})
        return HTMLResponse(content=_render_auth_form_html())

    if effective_token != config.ADMIN_TOKEN:
        if wants_json:
            return JSONResponse(status_code=403, content={"error": "FORBIDDEN"})
        return HTMLResponse(content=_render_auth_form_html(error="Invalid administrative token. Access denied."), status_code=403)

    q = db.query(Challenge)
    if status and status in ("under_review", "upheld", "rejected"):
        q = q.filter_by(status=status)
    challenges = q.order_by(Challenge.created_at.desc()).all()

    items = []
    for c in challenges:
        ind = db.query(Indicator).filter_by(id=c.indicator_id).first()
        rep_count = db.query(Report).filter_by(indicator_id=c.indicator_id).count() if ind else 0
        items.append({
            "challenge_id": f"CH-{c.id:06d}",
            "id": c.id,
            "indicator_type": ind.type if ind else "unknown",
            "indicator_value": ind.canonical_value if ind else "",
            "claimant_name": c.claimant_name,
            "contact_email": c.contact_email,
            "proof_note": c.proof_note or "",
            "status": c.status,
            "created_at": to_ist_iso(c.created_at),
            "resolved_at": to_ist_iso(c.resolved_at) if c.resolved_at else None,
            "report_count": rep_count,
        })

    if wants_json:
        return {"reviews": items}

    total_counts = {
        "total": db.query(Challenge).count(),
        "under_review": db.query(Challenge).filter_by(status="under_review").count(),
        "upheld": db.query(Challenge).filter_by(status="upheld").count(),
        "rejected": db.query(Challenge).filter_by(status="rejected").count(),
    }

    return HTMLResponse(content=_render_reviews_html(items, effective_token, status or "", total_counts))


@router.post("/admin/challenges/{challenge_id}/resolve")
def admin_resolve_challenge(
    challenge_id: str,
    payload: ChallengeResolveRequest,
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Resolve a challenge as upheld or rejected. Protected by X-Admin-Token or ?token=.
    (docs/01-api.md)
    """
    effective_token = x_admin_token or token
    if not effective_token or effective_token != config.ADMIN_TOKEN:
        return JSONResponse(status_code=403, content={"error": "FORBIDDEN"})

    if payload.decision not in ("upheld", "rejected"):
        return JSONResponse(status_code=400, content={"error": "INVALID_REQUEST"})

    # Parse integer ID from "CH-000001" or "1"
    raw = challenge_id.strip()
    if raw.upper().startswith("CH-"):
        raw = raw[3:]
    try:
        cid = int(raw)
    except ValueError:
        return JSONResponse(status_code=404, content={"error": "NOT_FOUND"})

    challenge = db.query(Challenge).filter_by(id=cid).first()
    if not challenge:
        return JSONResponse(status_code=404, content={"error": "NOT_FOUND"})

    now = _ensure_utc(clock.now())
    challenge.status = payload.decision
    challenge.resolved_at = now
    db.commit()

    if payload.decision == "upheld":
        # Add to verified_indicators(source='review')
        indicator = db.query(Indicator).filter_by(id=challenge.indicator_id).first()
        if indicator:
            existing_v = (
                db.query(VerifiedIndicator)
                .filter_by(type=indicator.type, canonical_value=indicator.canonical_value)
                .first()
            )
            if existing_v:
                existing_v.org = challenge.claimant_name
                existing_v.source = "review"
            else:
                new_v = VerifiedIndicator(
                    type=indicator.type,
                    canonical_value=indicator.canonical_value,
                    org=challenge.claimant_name,
                    source="review",
                )
                db.add(new_v)
            db.commit()

    return {
        "challenge_id": f"CH-{challenge.id:06d}",
        "status": challenge.status,
    }


@router.post("/admin/reset")
def admin_reset(
    db: Session = Depends(get_db),
):
    """
    Reset state when DEMO_MODE=true. Deletes reports, indicators, challenges,
    and review-added verified rows. Keeps areas, seed verified, and licence.
    (docs/01-api.md)
    """
    if not _is_demo_mode():
        return JSONResponse(status_code=403, content={"error": "DEMO_MODE_REQUIRED"})

    db.query(Report).delete()
    db.query(Challenge).delete()
    db.query(Indicator).delete()
    db.query(VerifiedIndicator).filter(VerifiedIndicator.source == "review").delete()
    db.commit()

    # Reset in-memory rate limits as well
    from app.identity import reset_rate_limits
    reset_rate_limits()

    return {"ok": True}
