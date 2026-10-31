#!/usr/bin/env python3
"""
judge_sim.py: simulates the hackathon judges' test tool against YOUR server.

Standalone: pip install httpx, then
  python judge_sim.py --base https://yourteam.onrender.com \
      --licence-long licences/long.json \
      --sign-cmd 'python tools/sign_licence.py --licensee "Demo Bank" --minutes 1 --out {out}'

* Uses FRESH RANDOM numbers on every run (use --seed to repeat a run), so rules
  that only work for specific numbers will fail here, like they will on judging day.
* It calls POST /admin/reset between sections. Never point it at data you care about.
* Scores mirror the brief's rows 1-5 (75 pts) and the 7 bonus pts. Rows 6-7
  (easy to report, demo/code, 25 pts) are judged by humans and not simulated.
* These are MY guesses at the judges' variants. Passing here is necessary, not sufficient.
"""
import argparse, json, random, re, subprocess, sys, tempfile, time, uuid, os
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import httpx

IST = timezone(timedelta(hours=5, minutes=30))
R = namedtuple("R", "status data text ms")

AREAS = {  # pincode: (locality, city, lat, lng)  (Appendix B)
    "560102": ("HSR Layout", "Bengaluru", 12.9116, 77.6473), "560038": ("Indiranagar", "Bengaluru", 12.9784, 77.6408),
    "560034": ("Koramangala", "Bengaluru", 12.9352, 77.6245), "560066": ("Whitefield", "Bengaluru", 12.9698, 77.7500),
    "560076": ("BTM Layout", "Bengaluru", 12.9166, 77.6101), "560011": ("Jayanagar", "Bengaluru", 12.9299, 77.5826),
    "560037": ("Marathahalli", "Bengaluru", 12.9591, 77.6974), "560103": ("Bellandur", "Bengaluru", 12.9260, 77.6762),
    "560100": ("Electronic City", "Bengaluru", 12.8452, 77.6602), "560078": ("JP Nagar", "Bengaluru", 12.9077, 77.5851),
    "560003": ("Malleshwaram", "Bengaluru", 13.0035, 77.5709), "560010": ("Rajajinagar", "Bengaluru", 12.9915, 77.5520),
    "560024": ("Hebbal", "Bengaluru", 13.0358, 77.5970), "560064": ("Yelahanka", "Bengaluru", 13.1007, 77.5963),
    "560070": ("Banashankari", "Bengaluru", 12.9250, 77.5468), "400050": ("Bandra West", "Mumbai", 19.0596, 72.8295),
    "110016": ("Hauz Khas", "Delhi", 28.5494, 77.2001), "500081": ("Madhapur", "Hyderabad", 17.4486, 78.3908),
    "600020": ("Adyar", "Chennai", 13.0012, 80.2565), "411014": ("Viman Nagar", "Pune", 18.5679, 73.9143),
    "700091": ("Salt Lake Sector V", "Kolkata", 22.5790, 88.4290), "380015": ("Satellite", "Ahmedabad", 23.0260, 72.5085),
    "302017": ("Malviya Nagar", "Jaipur", 26.8570, 75.8080), "226010": ("Gomti Nagar", "Lucknow", 26.8540, 80.9990),
    "682030": ("Kakkanad", "Kochi", 10.0159, 76.3419),
}
VERIFIED = [  # Appendix C
    ("phone", "1930"), ("phone", "1909"), ("phone", "1800 1600"), ("phone", "1800 2600"), ("phone", "1800 1080"),
    ("phone", "1800 1234"), ("phone", "1800 2100"), ("phone", "1860 419 5555"), ("phone", "1860 266 2666"),
    ("sender_id", "HDFCBK"), ("sender_id", "ICICIB"), ("sender_id", "SBIINB"), ("sender_id", "AXISBK"),
    ("sender_id", "KOTAKB"), ("url", "https://cybercrime.gov.in"), ("url", "https://sancharsaathi.gov.in"),
    ("phone", "+91 80 4100 2233"), ("phone", "+91 80 2553 0190"), ("upi", "freshbakes@okaxis"),
]
VERIFIED_SENDERS = {v for t, v in VERIFIED if t == "sender_id"}
SCAM_TYPES = ["digital-arrest", "fake-kyc-link", "upi-refund-qr", "investment-group", "courier-customs", "job-offer",
              "lottery-prize", "loan-app-harassment", "electricity-disconnection", "fake-customer-care", "otp-call", "sextortion"]
NOTES = [  # 24 clearly different notes: English, Hindi, Hinglish (no banned words)
    "Got a video call from someone in a police uniform saying a parcel with drugs was booked in my name.",
    "Caller said my Aadhaar was linked to money laundering and made me stay on video for hours.",
    "They asked for a refundable deposit of 25000 to clear my case, so I hung up immediately.",
    "Same number called my mother twice this week pretending to be a CBI officer.",
    "Received a link to update KYC that opened a page copying my bank's login screen.",
    "He kept saying do not tell anyone and do not disconnect the call, felt really scary.",
    "Number rang during office hours, a recorded voice said press 1 to avoid arrest.",
    "My neighbour lost money after the same caller threatened her with a fake warrant.",
    "मुझे वीडियो कॉल आया, पुलिस की वर्दी में एक आदमी बोला कि मेरे नाम पर पार्सल पकड़ा गया है।",
    "फोन करने वाले ने कहा कि मेरा आधार गलत कामों में इस्तेमाल हुआ है और तुरंत पैसे भेजो।",
    "इस नंबर से मेरे पिताजी को कल रात तीन बार फोन आया, उन्हें बहुत डराया गया।",
    "उन्होंने कहा किसी को मत बताना और कॉल मत काटना, मैंने तुरंत फोन रख दिया।",
    "बैंक के नाम पर लिंक भेजा गया जो बिल्कुल असली वेबसाइट जैसा दिख रहा था।",
    "मेरी मौसी से जुर्माने के नाम पर दस हज़ार रुपये मांगे गए।",
    "Bhai mujhe aaj subah is number se call aaya, bola CBI se hoon aur arrest ho jaoge.",
    "Unhone kaha parcel me drugs mile hain, turant paise bhejo warna police aa jayegi.",
    "Mere dost ko bhi isi number se call aaya tha, usne block kar diya.",
    "Link pe click karte hi bank jaisa page khula, OTP maang rahe the, maine band kar diya.",
    "Number se WhatsApp pe fake notice bheja gaya, upar Supreme Court ka logo laga tha.",
    "Caller ne apna naam inspector bataya par background me koi office ki awaaz nahi thi.",
    "Rs 2 lakh ki demand ki gayi, bola abhi transfer karo to case band ho jayega.",
    "Message aaya ki bijli kat jayegi aaj raat, bill update karne ke liye is link par click karo.",
    "Sent me a QR code saying scan it to receive a refund, but it asked for my UPI PIN.",
    "Dadi ko bhi call aaya, bahut daraya, family ne samjhaya ki ye jhootha call hai.",
]
BANNED = re.compile(r"\b(scammers?|fraudsters?|criminals?|culprits?|crooks?|thieves|thief)\b|\bis a fraud\b|\bare frauds?\b", re.I)
MAP_KEYS = {"pincode", "locality", "city", "count", "top_scam_type", "severity", "lat", "lng"}
EVID_KEYS = {"occurred_at", "channel", "scam_type", "pincode"}
LOOKUP_KEYS = ["verdict", "report_count", "distinct_reporters", "first_seen", "last_seen", "scam_type",
               "display_value", "evidence", "challenged"]
VERDICTS = {"KNOWN_SCAM", "SUSPICIOUS", "NO_REPORTS", "VERIFIED_BUSINESS"}


class Sim:
    def __init__(self, base, seed, verbose):
        self.base, self.verbose = base.rstrip("/"), verbose
        self.rng = random.Random(seed)
        self.http = httpx.Client(base_url=self.base, timeout=30, follow_redirects=True)
        self.run = f"{self.rng.getrandbits(24):06x}"
        self.n = 0
        self.rows, self.bodies, self.lookup_ms = [], [], []
        self.used_ips, self.fake_alert_ok = set(), None

    # ---------- plumbing ----------
    def call(self, method, path, **kw):
        t = time.perf_counter()
        try:
            r = self.http.request(method, path, **kw)
            status, text = r.status_code, r.text
        except Exception as e:  # network error, DNS, timeout
            status, text = 0, f"{type(e).__name__}"
        ms = (time.perf_counter() - t) * 1000
        try:
            data = json.loads(text)
        except Exception:
            data = {}
        self.bodies.append(text)
        return R(status, data if isinstance(data, dict) else {}, text, ms)

    def score(self, section, name, earned, pts, detail=""):
        earned = max(0.0, min(pts, earned))
        self.rows.append((section, name, earned, pts))
        ok = earned >= pts - 1e-9
        tag = "PASS" if ok else ("PART" if earned > 0 else "FAIL")
        line = f"  {tag} [{earned:.2f}/{pts:g}] {name}"
        if detail and (not ok or self.verbose):
            line += f"   -> {detail}"
        print(line)
        return ok

    def check(self, section, name, ok, pts, detail=""):
        return self.score(section, name, pts if ok else 0, pts, detail)

    def info(self, msg):
        print(f"  INFO {msg}")

    def reset(self):
        r = self.call("POST", "/admin/reset")
        if r.status != 200:
            print(f"\n!! POST /admin/reset returned {r.status}. Judges rely on it. Fix this first. ({r.text[:120]})")
            sys.exit(2)

    # ---------- generators ----------
    def phone10(self):
        while True:
            d = self.rng.choice("6789") + "".join(self.rng.choice("0123456789") for _ in range(9))
            if len(set(d)) >= 5:
                return d

    def phone_variants(self, d):
        return [f"+91 {d[:5]} {d[5:]}", f"0{d}", f"{d[:5]}-{d[5:]}", f"91{d}", f"+91{d}"]

    def word(self, n=6):
        return "".join(self.rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n))

    def upi(self):
        local = self.word(5) + str(self.rng.randint(10, 99))
        handle = self.rng.choice(["okaxis", "oksbi", "ybl", "paytm", "okhdfcbank"])
        return local, handle

    def host(self):
        return f"{self.word(6)}-kyc.{self.rng.choice(['in', 'com', 'xyz'])}"

    def sender(self):
        while True:
            s = "".join(self.rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(6))
            if s not in VERIFIED_SENDERS:
                return s

    def reporter(self):
        return f"r_{self.rng.getrandbits(32):08x}"

    def prefix(self):
        while True:
            p = f"{self.rng.randint(100, 223)}.{self.rng.randint(0, 255)}.{self.rng.randint(0, 255)}"
            if p not in self.used_ips:
                self.used_ips.add(p)
                return p

    def indicator(self, itype):
        """returns (canonical_expected, [variants], extra) for a fresh random indicator"""
        if itype == "phone":
            d = self.phone10()
            return "+91" + d, self.phone_variants(d), {"raw": [d]}
        if itype == "upi":
            l, h = self.upi()
            return f"{l}@{h}", [f"{l}@{h}", f"{l.capitalize()}@{h.upper()}", f" {l}@{h} "], {"raw": [f"{l}@{h}", l]}
        if itype == "url":
            h = self.host()
            return f"https://{h}/verify", [f"https://{h}/verify", f"http://www.{h}/verify?utm=sms", f"https://{h}/verify/"], {"raw": [h]}
        s = self.sender()
        return s, [s, "VM" + s, "AD-" + s], {"raw": [s]}

    def when(self, hours_ago):
        return datetime.now(IST) - timedelta(hours=hours_ago)

    def report(self, itype, value, pincode, reporter=None, ip=None, note="", hours_ago=0.5, scam="digital-arrest",
               channel="Phone call", **over):
        self.n += 1
        occ = self.when(hours_ago)
        rep = min(datetime.now(IST), occ + timedelta(minutes=self.rng.randint(5, 30)))
        loc, city = AREAS.get(pincode, ("", ""))[:2]
        body = {"report_id": f"rep_{self.run}_{self.n:05d}", "occurred_at": occ.replace(microsecond=0).isoformat(),
                "reported_at": rep.replace(microsecond=0).isoformat(), "reporter_id": reporter or self.reporter(),
                "ip_prefix": ip or self.prefix(), "channel": channel, "scam_type": scam, "identifier_type": itype,
                "identifier_value": value, "pincode": pincode, "locality": loc, "city": city, "note": note,
                "has_screenshot": False, "amount_lost_inr": 0}
        body.update(over)
        return self.call("POST", "/reports", json=body)

    def lookup(self, itype, value):
        r = self.call("GET", "/lookup", params={"type": itype, "value": value})
        if r.status == 200:
            self.lookup_ms.append(r.ms)
        return r

    def campaign(self, itype, variants, n, pincode, notes=True, hours=(1, 40), scam="digital-arrest", ips=None):
        """n genuine, unrelated reporters: own id, own network, own words. Returns count of 201s."""
        picks = self.rng.sample(NOTES, min(n, len(NOTES)))
        ok = 0
        for i in range(n):
            note = picks[i % len(picks)] if notes else ""
            r = self.report(itype, variants[i % len(variants)], pincode, note=note, scam=scam,
                            hours_ago=self.rng.uniform(*hours), ip=(ips[i] if ips else None))
            ok += r.status == 201
        return ok

    def bulk(self, pincode, n, hours_list, scams, tag=None):
        """n reports, each its own number/reporter/network/words, so each is an independent unit."""
        ok = 0
        for i in range(n):
            r = self.report("phone", "+91" + self.phone10(), pincode, note=self.rng.choice(NOTES),
                            hours_ago=hours_list[i], scam=scams[i % len(scams)])
            ok += r.status == 201
        return ok

    def alerts(self, pincode):
        r = self.call("GET", "/alerts", params={"pincode": pincode})
        return r, r.data.get("alerts", []) if r.status == 200 else []

    # ---------- SECTION 1: stops fake reports (20) ----------
    def sec1(self):
        S = "1 Stops fake reports"
        print("\n=== 1. Stops fake reports (20 pts) ===")
        self.reset()
        pins = {"bomb": "560024", "bomb2": "560003", "wifi": "560010", "spam": "560064"}

        # A1: 40 friends, 3 networks, copy-pasted note
        v = "+91" + self.phone10()
        ips = [self.prefix() for _ in range(3)]
        for i in range(40):
            self.report("phone", v, pins["bomb"], note="This shop number is a scam please block it, do not pick up the call",
                        ip=ips[i % 3], hours_ago=self.rng.uniform(0.2, 2))
        r = self.lookup("phone", v)
        self.check(S, "A1 report-bombing: 40 friends, copy-pasted note, 3 networks -> not KNOWN_SCAM",
                   r.data.get("verdict") != "KNOWN_SCAM", 3, f"verdict={r.data.get('verdict')} distinct={r.data.get('distinct_reporters')}")
        # A2: 40 friends on 40 networks, lightly edited copies
        v2 = "+91" + self.phone10()
        for i in range(40):
            self.report("phone", v2, pins["bomb2"], note=f"This shop number is a scam please block it, do not pick up the call {i * 7}",
                        hours_ago=self.rng.uniform(0.2, 2))
        r = self.lookup("phone", v2)
        self.check(S, "A2 report-bombing: 40 friends, lightly edited copies, 40 networks -> not KNOWN_SCAM",
                   r.data.get("verdict") != "KNOWN_SCAM", 2, f"verdict={r.data.get('verdict')} distinct={r.data.get('distinct_reporters')}")
        # B: 22 fake accounts, one Wi-Fi, different words
        v3 = "+91" + self.phone10()
        wifi = self.prefix()
        for i, note in enumerate(self.rng.sample(NOTES, 22)):
            self.report("phone", v3, pins["wifi"], ip=wifi, note=note, hours_ago=self.rng.uniform(0.2, 3))
        r = self.lookup("phone", v3)
        self.check(S, "B 22 fake accounts on one Wi-Fi -> not KNOWN_SCAM", r.data.get("verdict") != "KNOWN_SCAM", 5,
                   f"verdict={r.data.get('verdict')} distinct={r.data.get('distinct_reporters')}")
        # C: one person, six reports in an hour (429 is allowed and not penalised)
        v4 = "+91" + self.phone10()
        me, my_ip = self.reporter(), self.prefix()
        codes = [self.report("phone", v4, pins["spam"], reporter=me, ip=my_ip, note=self.rng.choice(NOTES),
                             hours_ago=self.rng.uniform(0.1, 0.9)).status for _ in range(6)]
        r = self.lookup("phone", v4)
        self.check(S, "C one person reports 6 times in an hour -> distinct_reporters 1, not KNOWN_SCAM",
                   r.data.get("verdict") != "KNOWN_SCAM" and r.data.get("distinct_reporters", 9) <= 1 and all(c in (201, 429) for c in codes),
                   5, f"codes={codes} verdict={r.data.get('verdict')} distinct={r.data.get('distinct_reporters')}")
        # D: junk
        junk = [("phone", x) for x in ["12345", "test", "0000000000", "1234567890", "abc", "", "9999999999"]]
        junk += [("upi", "nope"), ("url", "not a url"), ("sender_id", "AB")]
        passed = 0
        for t, x in junk:
            a = self.report(t, x, "560102")
            b = self.call("GET", "/lookup", params={"type": t, "value": x})
            passed += (a.status == 400 and "error" in a.data) and (b.status == 400)
        bad_pin = self.report("phone", "+91" + self.phone10(), "999999").status == 400
        bad_time = self.report("phone", "+91" + self.phone10(), "560102", occurred_at="not-a-date").status == 400
        self.score(S, f"D junk rejected with 400 ({passed}/{len(junk)} identifiers, bad pincode={bad_pin}, bad time={bad_time})",
                   5 * (passed + bad_pin + bad_time) / (len(junk) + 2), 5)
        # After tricks: fake reports must not alert (bonus)
        bad = []
        for p in pins.values():
            r, al = self.alerts(p)
            if r.status != 200 or al:
                bad.append((p, [a.get("type") for a in al]))
        self.fake_alert_ok = not bad
        self.info(f"alerts after fake reports: {'none (good)' if not bad else bad}")
        # Hard cases (information only)
        print("  -- hard cases (not scored, shows your engine's limits) --")
        v5 = "+91" + self.phone10()
        for note in self.rng.sample(NOTES, 24):
            self.report("phone", v5, "560011", note=note, hours_ago=self.rng.uniform(0.2, 3))
        r = self.lookup("phone", v5)
        self.info(f"24 unrelated-looking reporters, unique notes, 24 networks -> {r.data.get('verdict')} (KNOWN_SCAM is expected: indistinguishable from a real wave)")
        v6 = "+91" + self.phone10()
        two = [self.prefix(), self.prefix()]
        for i, note in enumerate(self.rng.sample(NOTES, 8)):
            self.report("phone", v6, "560037", ip=two[i % 2], note=note, hours_ago=self.rng.uniform(0.2, 3))
        r = self.lookup("phone", v6)
        self.info(f"8 genuine reporters on only 2 shared networks -> {r.data.get('verdict')} distinct={r.data.get('distinct_reporters')} (record this in your README)")

    # ---------- SECTION 2: lookup (15) ----------
    def sec2(self):
        S = "2 Lookup gives the right answer"
        print("\n=== 2. Lookup gives the right answer (15 pts) ===")
        self.reset()
        self.lookup_ms.clear()
        self.call("GET", "/health")
        self.lookup("phone", "+91" + self.phone10())  # warm-up, not timed
        self.lookup_ms.clear()
        plan = [("phone", 7, True), ("upi", 5, True), ("url", 4, True), ("sender_id", 3, False)]
        pin = ["560102", "560038", "560034", "560066"]
        known_ok, fmt_ok, fmt_detail = 0, 0, []
        for (t, n, notes), p in zip(plan, pin):
            canon, variants, _ = self.indicator(t)
            posted = self.campaign(t, variants, n, p, notes=notes)
            results = [self.lookup(t, v) for v in variants]
            first = results[0].data
            schema = all(k in first for k in LOOKUP_KEYS) and first.get("verdict") in VERDICTS
            k = results[0].status == 200 and first.get("verdict") == "KNOWN_SCAM" and schema
            known_ok += k
            same = len({(x.data.get("verdict"), x.data.get("distinct_reporters"), x.data.get("display_value")) for x in results}) == 1
            merged = first.get("distinct_reporters") == n
            fmt_ok += (same and merged)
            self.check(S, f"real {t} scam, {n} reporters{'' if notes else ', no notes'} -> KNOWN_SCAM with full schema",
                       k, 1.5, f"posted={posted}/{n} verdict={first.get('verdict')} distinct={first.get('distinct_reporters')} schema={schema}")
            self.check(S, f"all {len(variants)} typing styles of the {t} give the same answer and merge into {n} reporters",
                       same and merged, 0.75, f"same={same} distinct={first.get('distinct_reporters')} expected={n}")
        # NO_REPORTS
        good, total = 0, 0
        for t in ["phone", "upi", "url", "sender_id"]:
            for _ in range(3):
                canon, variants, _ = self.indicator(t)
                r = self.lookup(t, variants[0])
                total += 1
                good += (r.status == 200 and r.data.get("verdict") == "NO_REPORTS" and r.data.get("report_count", 1) == 0)
        self.score(S, f"unreported valid values -> 200 NO_REPORTS ({good}/{total})", 3 * good / total, 3)
        # speed
        ms = sorted(self.lookup_ms)
        fast = sum(1 for x in ms if x < 500)
        p95 = ms[int(len(ms) * 0.95) - 1] if ms else 0
        self.score(S, f"lookups under 500 ms ({fast}/{len(ms)}, p95={p95:.0f} ms incl. your network)",
                   3 * fast / max(1, len(ms)), 3)

    # ---------- SECTION 3: map and alerts (10) ----------
    def sec3(self):
        S = "3 Map and alerts"
        print("\n=== 3. Map and alerts (10 pts) ===")
        self.reset()
        spike_p, normal_p, new_p, old_p, recent_p = "560102", "560064", "110016", "400050", "500081"
        base_h = [30 + i * (7 * 24 - 40) / 14 + self.rng.uniform(0, 4) for i in range(14)]
        types = ["digital-arrest", "courier-customs"]
        # SPIKE area: 14 over the prior 7 days (2/day), then 10 on one campaign number in the last 20 hours
        self.bulk(spike_p, 14, base_h, types)
        campaign = "+91" + self.phone10()
        for note in self.rng.sample(NOTES, 10):
            self.report("phone", campaign, spike_p, note=note, scam="digital-arrest",
                        hours_ago=self.rng.uniform(0.5, 20))
        # normal area: same baseline, only 2 today
        self.bulk(normal_p, 14, base_h, types)
        self.bulk(normal_p, 2, [2.0, 10.0], types)
        # new-type area: 4 otp-call over past 3-18 days, then one job-offer in last 6 hours
        for d in (3, 6, 10, 18):
            self.report("phone", "+91" + self.phone10(), new_p, note=self.rng.choice(NOTES), scam="otp-call",
                        hours_ago=d * 24 + self.rng.uniform(0, 5))
        self.report("phone", "+91" + self.phone10(), new_p, note=self.rng.choice(NOTES), scam="job-offer", hours_ago=3)
        # old reports: 10 about a month old (must be ACCEPTED, but off the map), 3 that are 8-9 days old
        old_ok = sum(self.report("phone", "+91" + self.phone10(), old_p, note=self.rng.choice(NOTES),
                                 hours_ago=self.rng.uniform(31 * 24, 35 * 24)).status == 201 for _ in range(10))
        old_ok += sum(self.report("phone", "+91" + self.phone10(), old_p, note=self.rng.choice(NOTES),
                                  hours_ago=self.rng.uniform(8.2 * 24, 9.5 * 24)).status == 201 for _ in range(3))
        # recent area: 7 independent reports in the last 5 days
        self.bulk(recent_p, 7, [self.rng.uniform(5, 5 * 24) for _ in range(7)], SCAM_TYPES[:5])

        r, al = self.alerts(spike_p)
        sp = [a for a in al if a.get("type") == "SPIKE"]
        ok = bool(sp) and sp[0].get("count", 0) >= 5 and "baseline_per_day" in sp[0] and sp[0].get("pincode") == spike_p
        self.check(S, "area with a sudden jump gets a SPIKE alert", ok, 3, f"status={r.status} alerts={al}")
        self.info(f"spike area baseline reported as {sp[0].get('baseline_per_day') if sp else 'n/a'} (expected about 2.0), count {sp[0].get('count') if sp else 'n/a'} (expected about 10)")
        r, al = self.alerts(normal_p)
        self.check(S, "normal area (2 a day) gets NO alert", r.status == 200 and al == [], 2, f"alerts={al}")
        r, al = self.alerts(new_p)
        nt = [a for a in al if a.get("type") == "NEW_TYPE"]
        ok = any(a.get("scam_type") == "job-offer" for a in nt) and not any(a.get("scam_type") == "otp-call" for a in nt) \
            and not any(a.get("type") == "SPIKE" for a in al)
        self.check(S, "a new kind of scam gets NEW_TYPE (and the old kind does not)", ok, 3, f"alerts={al}")
        r = self.call("GET", "/map", params={"pincode": old_p, "days": 7, "radius_km": 2})
        pins = [c.get("pincode") for c in r.data.get("clusters", [])]
        self.check(S, f"month-old and 8-day-old reports are accepted (201) but NOT on the 7-day map", old_ok == 13 and old_p not in pins, 1,
                   f"accepted={old_ok}/13 map pincodes={pins}")
        r = self.call("GET", "/map", params={"pincode": recent_p})  # days/radius default
        cl = [c for c in r.data.get("clusters", []) if c.get("pincode") == recent_p]
        self.check(S, "recent reports appear on the map with the right count (defaults days=7, radius=2)",
                   len(cl) == 1 and cl[0].get("count") == 7 and cl[0].get("severity") in ("CRIT", "HIGH", "MED"), 1,
                   f"status={r.status} clusters={r.data.get('clusters')}")

    # ---------- SECTION 4: privacy (15) ----------
    def sec4(self):
        S = "4 Privacy"
        print("\n=== 4. Privacy (15 pts) ===")
        self.reset()
        start = len(self.bodies)
        # hidden until 3 distinct people
        for t, p in zip(["phone", "upi", "url", "sender_id"], ["560037", "560103", "560100", "560078"]):
            canon, variants, extra = self.indicator(t)
            picks = self.rng.sample(NOTES, 3)
            for n in (1, 2, 3):
                self.report(t, variants[0], p, note=picks[n - 1], hours_ago=self.rng.uniform(1, 30))
                r = self.lookup(t, variants[0])
                dv = str(r.data.get("display_value", ""))
                if n < 3:
                    leaked = any(tok in r.text for tok in extra["raw"] + [canon])
                    masked = dv != canon and ("X" in dv or "*" in dv)
                    self.check(S, f"{t}: hidden with {n} reporter{'s' if n > 1 else ''}", (not leaked) and masked, 0.5,
                               f"display_value={dv!r} leaked_in_response={leaked}")
                else:
                    shown = (extra["raw"][0] in dv) if t == "url" else (dv == canon)
                    self.check(S, f"{t}: shown once 3 people reported", shown and r.data.get("distinct_reporters") == 3, 0.25,
                               f"display_value={dv!r} distinct={r.data.get('distinct_reporters')} expected {canon!r}")
        # anonymous reporters: canaries must never come back
        rc, ipc, nc = f"r_CANARY{self.run}", f"203.0.{self.rng.randint(100, 199)}", f"CANARYNOTE{self.run} the caller said I owe money"
        cv = "+91" + self.phone10()
        others = self.rng.sample(NOTES, 2)
        for i in range(3):
            self.report("phone", cv, "560011", reporter=rc if i == 0 else None, ip=ipc if i == 0 else None,
                        note=nc if i == 0 else others[i - 1])
        self.lookup("phone", cv)
        self.call("GET", "/map", params={"pincode": "560011"})
        self.call("GET", "/map")
        self.call("GET", "/alerts", params={"pincode": "560011"})
        self.call("GET", "/alerts")
        self.call("POST", "/challenges", json={"identifier_type": "phone", "identifier_value": cv, "claimant_name": "Canary Co",
                                                 "contact_email": "canary@example.com", "proof_note": "n/a"})
        scan = "\n".join(self.bodies[start:])
        leaks = [c for c in (rc, ipc, nc, f"CANARYNOTE{self.run}", "canary@example.com", "Canary Co") if c in scan]
        self.check(S, "reporter id, network prefix, note and claimant details never appear in any response", not leaks, 3, f"leaked: {leaks}")
        r = self.lookup("phone", cv)
        ev = r.data.get("evidence", [])
        bad_keys = {k for e in ev for k in e} - EVID_KEYS
        self.check(S, "evidence holds only occurred_at, channel, scam_type, pincode", isinstance(ev, list) and not bad_keys, 1, f"extra keys: {bad_keys}")
        canary_val = f"ZZCANARY{self.run}"
        a = self.call("GET", "/lookup", params={"type": "phone", "value": canary_val})
        b = self.report("phone", canary_val, "560102")
        self.check(S, "error replies do not echo the submitted value", a.status == 400 and b.status == 400 and canary_val not in a.text + b.text, 1,
                   f"status {a.status}/{b.status}")
        # map: no personal location
        r = self.call("GET", "/map", params={"pincode": "560011", "radius_km": 5})
        cls = r.data.get("clusters", [])
        exact = bool(cls) and all(c.get("pincode") in AREAS and abs(c.get("lat", 0) - AREAS[c["pincode"]][2]) < 1e-6
                                  and abs(c.get("lng", 0) - AREAS[c["pincode"]][3]) < 1e-6 for c in cls)
        extra_keys = {k for c in cls for k in c} - MAP_KEYS
        sus = [k for k in extra_keys if re.search(r"report|ip|note|user|device|exact|address|gps|phone", k, re.I)]
        self.check(S, "map points are the area's fixed point, never a reporter's", exact, 2, f"clusters={cls[:2]}")
        self.check(S, "map has no reporter/location-like fields", not sus, 1, f"suspicious keys: {sus}")
        # wording
        texts = [t for t in self.bodies[start:]]
        home = self.call("GET", "/")
        found = []
        if home.status == 200:
            texts.append(home.text)
            for m in re.findall(r'(?:src|href)=["\']([^"\']+\.(?:js|css|json))["\']', home.text):
                if m.startswith(("http://", "https://")) and not m.startswith(self.base):
                    continue
                texts.append(self.call("GET", urljoin(self.base + "/", m)).text)
        for t in texts:
            found += [m.group(0) for m in BANNED.finditer(t)]
        pts = 2 if home.status == 200 else 1
        self.check(S, f"wording: no accusing words in API replies or frontend files{'' if home.status == 200 else ' (frontend not found at /, only API scanned, half marks)'}",
                   not found, pts, f"found: {sorted(set(found))[:5]}")
        if home.status != 200:
            self.rows.append((S, "wording (frontend missing)", 0.0, 1))
        self.info("a judge ALSO reads your result screen by eye: say 'Reported by 7 people near you', never 'this person is a fraud'.")

    # ---------- BONUS (7) ----------
    def bonus(self):
        S = "Bonus"
        print("\n=== Bonus (7 pts) ===")
        self.reset()
        # verified: even after genuine scam reports on some of them
        for t, v in [("phone", "+91 80 4100 2233"), ("upi", "freshbakes@okaxis"), ("sender_id", "HDFCBK")]:
            for note in self.rng.sample(NOTES, 6):
                self.report(t, v, "560038", note=note)
        ok = 0
        for t, v in VERIFIED:
            r = self.lookup(t, v)
            ok += r.status == 200 and r.data.get("verdict") == "VERIFIED_BUSINESS"
            if not (r.status == 200 and r.data.get("verdict") == "VERIFIED_BUSINESS"):
                print(f"       not verified: {t} {v} -> {r.status} {r.data.get('verdict')}")
        self.score(S, f"verified businesses and helplines say VERIFIED_BUSINESS ({ok}/{len(VERIFIED)}), even with 6 scam reports on three of them",
                   3 * ok / len(VERIFIED), 3)
        # dispute
        canon, variants, _ = self.indicator("phone")
        self.campaign("phone", variants, 6, "560034")
        before = self.lookup("phone", variants[0]).data.get("verdict")
        c = self.call("POST", "/challenges", json={"identifier_type": "phone", "identifier_value": variants[0],
                                                     "claimant_name": "Fresh Bakes", "contact_email": "owner@example.com",
                                                     "proof_note": "GST certificate and shop licence attached."})
        self.check(S, "POST /challenges -> 201 {challenge_id, status: under_review}",
                   c.status == 201 and c.data.get("status") == "under_review" and c.data.get("challenge_id"), 1, f"{c.status} {c.data}")
        after = self.lookup("phone", variants[3]).data
        self.check(S, f"after a dispute: challenged=true and never KNOWN_SCAM (was {before})",
                   after.get("challenged") is True and after.get("verdict") != "KNOWN_SCAM", 1,
                   f"challenged={after.get('challenged')} verdict={after.get('verdict')}")
        # fake reports never alert
        if self.fake_alert_ok is None:
            self.info("run section 1 in the same run to score 'fake reports never set off an alert' (2 pts)")
        else:
            self.check(S, "fake reports never set off an alert (checked after section 1's attacks)", self.fake_alert_ok, 2)

    # ---------- SECTION 5: licence (15) ----------
    def sec5(self, long_path, short_path, sign_cmd):
        S = "5 Server and licence"
        print("\n=== 5. Server and licence (15 pts) ===")
        self.check(S, "server is on an https address", self.base.startswith("https://"), 2, self.base)
        g = self.call("GET", "/license")
        self.check(S, "GET /license shows who it is licensed to and when it expires",
                   g.status == 200 and g.data.get("licensee") and g.data.get("expires_at"), 2, f"{g.status} {g.text[:150]}")
        if not long_path or not (short_path or sign_cmd):
            print("  SKIP the live steps: pass --licence-long FILE and (--licence-short FILE or --sign-cmd 'CMD with {out}')")
            return
        long_lic = json.load(open(long_path))
        self.reset()
        # remember some data
        canon, variants, _ = self.indicator("phone")
        self.campaign("phone", variants, 4, "560102")
        before = self.lookup("phone", variants[0]).data
        r = self.call("POST", "/license", json=long_lic)
        self.info(f"POST long licence -> {r.status}")
        # short licence
        if sign_cmd:
            out = os.path.join(tempfile.gettempdir(), f"short_{self.run}.json")
            cmd = sign_cmd.replace("{out}", out)
            print(f"  .. creating short licence: {cmd}")
            subprocess.run(cmd, shell=True, check=False)
            short_path = out
        short_lic = json.load(open(short_path))
        exp = datetime.fromisoformat(short_lic["expires_at"])
        wait = (exp - datetime.now(timezone.utc)).total_seconds()
        if wait > 600 or wait < 0:
            self.check(S, "short licence must expire in the next 0-10 minutes (make one just before running)", False, 2, f"expires in {wait:.0f}s")
            return
        r = self.call("POST", "/license", json=short_lic)
        probe = self.lookup("phone", variants[0])
        self.check(S, "step 2: upload a short licence; app keeps working until it expires", r.status in (200, 201) and probe.status == 200, 2,
                   f"POST {r.status}, lookup {probe.status}")
        print(f"  .. waiting {wait + 3:.0f}s for the licence to expire (your clock vs server clock may differ a little)")
        time.sleep(max(0, wait + 3))
        end = time.time() + 60
        while time.time() < end:
            probe = self.lookup("phone", variants[0])
            if probe.status == 403:
                break
            time.sleep(3)
        locked = probe.status == 403 and probe.data.get("error") == "LICENSE_EXPIRED"
        others = [self.call("POST", "/reports", json={}).status, self.call("GET", "/map").status, self.call("GET", "/alerts").status]
        open_routes = [self.call("GET", "/health").status, self.call("GET", "/license").status]
        s = 0.0
        s += 1 if locked else 0
        s += 1 if all(x == 403 for x in others) else 0
        s += 1 if all(x == 200 for x in open_routes) else 0
        self.score(S, "step 3: after expiry lookup=403 LICENSE_EXPIRED, every other route 403, /health and /license still open", s, 3,
                   f"lookup={probe.status}/{probe.data.get('error')} others={others} open={open_routes}")
        t0 = time.time()
        r = self.call("POST", "/license", json=long_lic)
        back, secs = None, None
        while time.time() - t0 < 70:
            back = self.lookup("phone", variants[0])
            if back.status == 200:
                secs = time.time() - t0
                break
            time.sleep(2)
        self.check(S, "step 4: upload the long licence, app works again within a minute with no restart",
                   back is not None and back.status == 200 and secs is not None and secs <= 60, 2, f"POST {r.status}, recovered in {secs}")
        same = back is not None and back.status == 200 and back.data.get("report_count") == before.get("report_count") \
            and back.data.get("distinct_reporters") == before.get("distinct_reporters")
        self.check(S, "old data is still there after renewal (nothing was deleted)", same, 2,
                   f"before={before.get('report_count')}/{before.get('distinct_reporters')} after={back.data.get('report_count') if back else None}")
        tam = dict(long_lic)
        tam["expires_at"] = (datetime.now(IST) + timedelta(days=400)).replace(microsecond=0).isoformat()
        r = self.call("POST", "/license", json=tam)
        g2 = self.call("GET", "/license")
        self.check(S, "a licence with an edited date is rejected and changes nothing",
                   400 <= r.status < 500 and g2.data.get("expires_at") == g.data.get("expires_at") or (400 <= r.status < 500 and g2.data.get("expires_at") != tam["expires_at"]),
                   2, f"POST {r.status}, expires_at now {g2.data.get('expires_at')}")
        self.call("POST", "/license", json=long_lic)
        self.info("not simulated here: clock-rollback protection (bonus thinking). Demo it by hand if you built it.")

    def summary(self):
        print("\n" + "=" * 60 + "\nSCORECARD (what this tool can simulate)\n" + "=" * 60)
        tot = tmax = 0
        order = []
        for s, _, e, m in self.rows:
            if s not in order:
                order.append(s)
        names = {"1": 20, "2": 15, "3": 10, "4": 15, "5": 15}
        for s in order:
            e = sum(x[2] for x in self.rows if x[0] == s)
            m = sum(x[3] for x in self.rows if x[0] == s)
            cap = names.get(s[0], m)
            print(f"  {s:<36} {e:5.1f} / {m:g}")
            if s != "Bonus":
                tot += e; tmax += m
        b = sum(x[2] for x in self.rows if x[0] == "Bonus")
        print(f"  {'-' * 36}\n  {'Rows 1-5 (of 75)':<36} {tot:5.1f} / {tmax:g}\n  {'Bonus (of 7)':<36} {b:5.1f}")
        fails = [(s, n) for s, n, e, m in self.rows if e < m - 1e-9]
        print(f"\n  {len(fails)} check(s) not at full marks.")
        print("  Not simulated: rows 6-7 (easy to report, demo/code = 25 pts), log contents, hard-coded-rule inspection, clock rollback.")
        return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="Simulate the judges' test tool against your server")
    ap.add_argument("--base", required=True, help="e.g. https://yourteam.onrender.com (or http://localhost:8000)")
    ap.add_argument("--only", default="1,2,3,4,b,5", help="sections to run, comma separated: 1,2,3,4,b,5")
    ap.add_argument("--seed", type=int, default=None, help="repeat a previous run")
    ap.add_argument("--licence-long", help="signed long licence JSON file")
    ap.add_argument("--licence-short", help="signed licence that expires within ~10 minutes (create just before running)")
    ap.add_argument("--sign-cmd", help="command that writes a ~1 minute licence to {out}")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    seed = a.seed if a.seed is not None else random.SystemRandom().randrange(10 ** 9)
    print(f"judge_sim seed={seed} (repeat with --seed {seed}) base={a.base}")
    sim = Sim(a.base, seed, a.verbose)
    h = sim.call("GET", "/health")
    if h.status != 200 or h.data.get("ok") is not True:
        print(f"!! GET /health -> {h.status} {h.text[:100]}  (server up? free hosts sleep: open it once and retry)")
        return 2
    want = {x.strip().lower() for x in a.only.split(",")}
    if "1" in want: sim.sec1()
    if "2" in want: sim.sec2()
    if "3" in want: sim.sec3()
    if "4" in want: sim.sec4()
    if "b" in want: sim.bonus()
    if "5" in want: sim.sec5(a.licence_long, a.licence_short, a.sign_cmd)
    return sim.summary()


if __name__ == "__main__":
    sys.exit(main())