"""Work Package K: data quality audit.

Scope A: supplied Users_Messy_Audit (rule-based detection, then confirmed against the clean sheet).
Scope B: supplied Users_1000_Clean (logical consistency: the 'clean' sheet still has issues).
Scope C: analyst-generated Messy_Data (14 check types), scored against messy_injection_log.csv.

Detection is rule-based only. The clean sheet and the injection log are used AFTER detection to
measure whether the rules found exactly the planted defects (no peeking during detection).
"""
import json
import re

import pandas as pd

from common import BUILD_DIR, SIM_DIR, load_supplied
from specs.events import EVENTS

OUT = BUILD_DIR / "dq"
OUT.mkdir(parents=True, exist_ok=True)
sup = load_supplied()
clean, messy_u = sup["Users_1000_Clean"], sup["Users_Messy_Audit"]
issues = []
evidence = []  # (issue_id, record key, field, value)


def add(iid, dataset, field, itype, rows, severity, logic, cause, correction, prevention, owner, status="Open", keys=None, col=None):
    keys = list(keys) if keys is not None else []
    issues.append(dict(issue_id=iid, dataset=dataset, field=field, issue_type=itype, records_affected=int(rows),
                       severity=severity, detection_logic=logic, likely_cause=cause, correction=correction,
                       prevention=prevention, owner=owner, status=status,
                       example_records=", ".join(map(str, keys[:6]))))
    for k in keys:
        evidence.append(dict(issue_id=iid, record=k, field=field))


blank = lambda s: s.str.strip() == ""
REQUIRED = ["user_id", "full_name", "email", "age", "state", "city", "registration_datetime", "acquisition_source",
            "primary_device", "account_status", "email_verification_status", "onboarding_status", "lifetime_sessions",
            "active_days", "xp_balance", "referral_code", "consent_status", "marketing_opt_in", "account_created_via"]


def parse_naive(s):
    return pd.to_datetime(s.where(~blank(s)), errors="coerce", format="%Y-%m-%d %H:%M:%S")


# =========================================================================================== A
m = messy_u
d = "Users_Messy_Audit (supplied)"
dup_rows = m[m.drop(columns="data_environment").duplicated(keep="first")]
add("DQ-U01", d, "user_id", "Duplicate IDs / duplicate records", len(dup_rows), "Critical",
    "user_id appears more than once; every repeat is an exact copy of an earlier row (pandas duplicated on all columns).",
    "Record re-inserted by a retried import or append without a key check.", "Keep the first occurrence; delete 8 repeats.",
    "Primary-key uniqueness constraint on user_id at load; idempotent upsert.", "Engineering", "Open", dup_rows.user_id)
for col in REQUIRED + ["gender"]:
    b = m[blank(m[col])]
    if len(b):
        sev = "Low" if col == "gender" else ("High" if col in ("acquisition_source", "onboarding_status", "email_verification_status") else "Medium")
        add(f"DQ-U-MISS-{col}", d, col, "Unexpected null" if col != "gender" else "Missing optional value", len(b), sev,
            f"{col} is blank although the supplied Data_Dictionary marks it {'Optional' if col == 'gender' else 'Required'}.",
            "Field not captured or lost during export.", "Re-source from system of record; else mark 'unknown' explicitly, never guess.",
            "NOT NULL / required-field validation at ingestion.", "Engineering", "Open", b.user_id)
reg_raw = m.registration_datetime
reg = parse_naive(reg_raw)
bad = m[reg.isna() & ~blank(reg_raw)]
add("DQ-U02", d, "registration_datetime", "Malformed dates", len(bad), "High",
    "Value does not parse with format YYYY-MM-DD HH:MM:SS (values: " + ", ".join(repr(v) for v in bad.registration_datetime) + ").",
    "Free-text placeholder ('N/A') and a day/month swap or typo ('2026-14-02 12:00').", "Quarantine rows; recover true timestamp from backend logs.",
    "Typed timestamp column; reject non-ISO strings at ingestion.", "Engineering", "Open", bad.user_id)
dsr = pd.to_numeric(m.days_since_registration, errors="coerce")
REF = pd.Timestamp("2026-09-15 00:00:00")  # reference date inferred from the clean sheet (see deliverable 12)
recomputed = (REF - reg).dt.total_seconds() / 86400
mismatch = m[reg.notna() & ((recomputed - dsr).abs() > 0.06)]
add("DQ-U03", d, "registration_datetime / days_since_registration", "Inconsistent derived value", len(mismatch), "High",
    "days_since_registration differs from (2026-09-15 00:00 - registration_datetime) by more than rounding (0.06 day).",
    "Registration timestamp edited after the derived column was computed, or derived column stale.",
    "Treat registration_datetime from the system of record as truth; recompute derived fields in the transformation layer.",
    "Do not store derived columns in source tables; compute them downstream with a documented reference date.", "Data/Analytics", "Open", mismatch.user_id)
ll_missing = m[blank(m.last_login_datetime) & (m.account_status != "Pending Verification")]
add("DQ-U04", d, "last_login_datetime", "Unexpected null", len(ll_missing), "Medium",
    "last_login_datetime blank for a user who is not 'Pending Verification' (all 72 pending users are blank by design).",
    "Login timestamp not written for this account.", "Re-source from auth logs.", "Conditional-required rule: last_login required when lifetime_sessions > 0 and status != pending_verification.",
    "Engineering", "Open", ll_missing.user_id)

# Confirm scope A against the clean sheet (post-detection check)
mm = m.iloc[:1000].reset_index(drop=True)
cell_diffs = sum(int((mm[c] != clean[c]).sum()) for c in clean.columns)
detected_cells = set()
for e in evidence:
    if e["issue_id"].startswith("DQ-U-MISS") or e["issue_id"] in ("DQ-U02", "DQ-U03", "DQ-U04"):
        detected_cells.add((e["record"], e["field"].split(" /")[0]))
planted = {(mm.user_id[i], c) for c in clean.columns for i in mm.index[mm[c] != clean[c]]}
scope_a_check = dict(planted_cell_changes=len(planted), detected_cell_changes=len(planted & detected_cells),
                     missed=sorted(planted - detected_cells), extra_detected=sorted(detected_cells - planted),
                     planted_duplicate_rows=len(m) - 1000, detected_duplicate_rows=len(dup_rows))

# =========================================================================================== B
c = clean.copy()
d = "Users_1000_Clean (supplied)"
for k in ["lifetime_sessions", "active_days"]:
    c[k] = c[k].astype(int)
c["reg"] = parse_naive(c.registration_datetime)
c["ll"] = parse_naive(c.last_login_datetime)
x = c[(c.active_days == 0) & (c.lifetime_sessions > 0)]
add("DQ-C01", d, "active_days / lifetime_sessions", "Impossible combination", len(x), "High",
    "active_days = 0 while lifetime_sessions > 0 (a session implies at least one active day).",
    "Counters maintained separately and not reconciled, or active_days defined differently (undocumented).",
    "Recompute both counters from session/event history.", "Derive counters from events in the analytics layer; add cross-field rule.", "Data/Analytics", "Open", x.user_id)
x = c[c.ll.notna() & (c.lifetime_sessions == 0)]
add("DQ-C02", d, "last_login_datetime / lifetime_sessions", "Impossible combination", len(x), "High",
    "A last login exists but lifetime_sessions = 0.", "Session counter not incremented on login.", "Recompute from login events.",
    "Single source for sessions (sessions table).", "Engineering", "Open", x.user_id)
x = c[c.ll.isna() & (c.lifetime_sessions > 0)]
add("DQ-C03", d, "last_login_datetime / lifetime_sessions", "Impossible combination", len(x), "Medium",
    "lifetime_sessions > 0 but no last login (all are 'Pending Verification').",
    "Sessions may be counted before verification without a login record, or counter is wrong; definition of 'session' unclear.",
    "Clarify whether unverified users can hold sessions (A-008).", "Document session definition; derive from session table.", "Product + Engineering", "Proposed", x.user_id)
x = c[(c.consent_status == "Pending") & (c.marketing_opt_in == "Yes")]
add("DQ-C04", d, "consent_status / marketing_opt_in", "Governance conflict", len(x), "High",
    "marketing_opt_in = Yes while consent_status = Pending.", "Opt-in captured independently of consent.",
    "Treat these users as not opted in until consent is accepted.", "Rule: marketing_opt_in may be true only if consent_status = accepted.", "Product + Legal", "Open", x.user_id)
x = c[pd.to_numeric(c.days_since_registration) < 0]
add("DQ-C05", d, "days_since_registration", "Negative values where inappropriate", len(x), "Medium",
    "days_since_registration < 0, violating the supplied dictionary rule '>=0'.",
    "Derived with reference date 2026-09-15 00:00 while registrations continue later that day.",
    "Recompute with a documented reference timestamp at the end of the period.", "Compute derived fields downstream with an explicit as-of timestamp.", "Data/Analytics", "Open", x.user_id)
x = c[c.ll > pd.Timestamp("2026-09-15 23:59:59")]
add("DQ-C06", d, "last_login_datetime", "Out-of-period timestamps", len(x), "Medium",
    "last_login_datetime after the stated dataset period end (15 Sep 2026).", "Snapshot taken later than stated period, or timestamps in a different timezone.",
    "Confirm extraction time and timezone (A-004).", "Store extraction timestamp and timezone with every dataset.", "Data/Analytics", "Open", x.user_id)
x = c[c.ll >= pd.Timestamp("2026-09-15 00:00:00")]
add("DQ-C07", d, "is_active_7d / is_active_30d", "Undocumented derivation", len(x), "Medium",
    "Flags reproduce exactly only with reference date 2026-09-15 00:00 on login time (0 mismatches); users whose last login is after that moment are still counted active.",
    "Reference date and definition (login-based) not documented.", "Document as-of timestamp; re-define activity on qualifying events (K-USR-02).",
    "Derived flags carry definition + as-of metadata.", "Data/Analytics", "Open", x.user_id)
x = c[(c.email_verification_status == "Pending") & (c.account_status == "Active")]
add("DQ-C08", d, "email_verification_status / account_status", "Business-rule question", len(x), "Low",
    "Account 'Active' while email verification is 'Pending'.", "May be valid (e.g. verification not required to use the platform).",
    "None until rule confirmed (A-009).", "Document the rule.", "Product", "Proposed", x.user_id)
add("DQ-C09", d, "platform / primary_device", "Inconsistent naming / semantics", len(c), "Low",
    "platform = 'Web' for 100% of users while primary_device includes Android and iOS.",
    "platform means 'web app' and device means OS; not documented.", "Rename to signup_platform and device_os/device_type.",
    "Dictionary definitions with allowed values.", "Data/Analytics", "Proposed")
add("DQ-C10", d, "full_name, email, age, gender, city", "Unnecessary personal data", len(c), "High",
    "Direct identifiers and sensitive attributes present in an analytics dataset.", "Dataset built from an account export rather than an analytics model.",
    "Remove from analytics layer; keep in identity store only; use age_band if needed.", "Pseudonymous analytics model (deliverable 17).", "Data/Analytics + Engineering", "Open")
add("DQ-C11", "Data_Dictionary (supplied)", "platform, country", "Incomplete documentation", 2, "Low",
    "Columns present in the user sheets but missing from the supplied Data_Dictionary sheet.", "Dictionary not updated when columns added.",
    "Add both fields.", "Validator: every column must have a dictionary entry (scripts/validate.py does this for this project).", "Data/Analytics", "Open")
add("DQ-C12", d, "data_environment", "Missing simulated-data label", len(c), "Medium",
    "Users_1000_Clean has no data_environment column (the audit sheet has one).", "Label added to one sheet only.",
    "Add label column to every sheet.", "Pipeline adds data_environment on load.", "Data/Analytics", "Open")
# Positive reconciliation check (not an issue)
summ = sup["Synthetic_Summary"].set_index("Metric").Value.astype(int)
recon = {"Users": len(c), "Active 7d": int((c.is_active_7d == "Yes").sum()), "Active 30d": int((c.is_active_30d == "Yes").sum()),
         "Verified email": int((c.email_verification_status == "Verified").sum()), "Onboarding completed": int((c.onboarding_status == "Completed").sum()),
         "Google Sign-In": int((c.account_created_via == "Google Sign-In").sum()), "Referral acquisition": int((c.acquisition_source == "Referral").sum()),
         "Suspended": int((c.account_status == "Suspended").sum())}
summary_recon = [dict(metric=k, supplied_summary=int(summ[k]), recomputed=v, match=int(summ[k]) == v) for k, v in recon.items()]

# =========================================================================================== C
md = pd.read_csv(SIM_DIR / "Messy_Data.csv", dtype=str, keep_default_na=False)
inj = pd.read_csv(SIM_DIR / "messy_injection_log.csv", dtype=str, keep_default_na=False)
users_ids = set(clean.user_id)
d = "Messy_Data (analyst-generated)"
ALLOWED = {"withdrawals": {"requested", "processing", "completed", "rejected", "reversed"}, "task_activity": {"started", "completed"}}
CATALOGUE = {e["event_name"] for e in EVENTS}
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
detected = {}


def det(kind, mask):
    detected[kind] = set(md.record_id[mask]) if kind not in ("duplicate_id",) else None
    return md[mask]


r = md[md.record_id.duplicated(keep=False)]
detected["duplicate_id"] = set(r.record_id)
add("DQ-M01", d, "record_id", "Duplicate IDs", int(md.record_id.duplicated().sum()), "Critical", "record_id not unique.",
    "ID generated by copying or by a non-unique sequence.", "Re-key affected rows from source; keep both until source confirms.", "Unique constraint; server-generated IDs.", "Engineering", "Open", sorted(detected["duplicate_id"]))
x = det("missing_id", blank(md.user_id))
add("DQ-M02", d, "user_id", "Missing IDs", len(x), "Critical", "user_id blank.", "Event emitted before user context set.", "Recover from session or reference record; else exclude from user KPIs.", "Reject events without user_id at collection.", "Engineering", "Open", x.record_id)
x = det("missing_timestamp", blank(md.event_timestamp_utc))
add("DQ-M03", d, "event_timestamp_utc", "Missing timestamps", len(x), "High", "event_timestamp_utc blank.", "Producer did not set time.", "Use received_at_utc only if documented; else quarantine.", "Required timestamp at producer + collection.", "Engineering", "Open", x.record_id)
x = det("malformed_date", ~blank(md.event_timestamp_utc) & ~md.event_timestamp_utc.str.match(ISO))
x2 = md[md.event_timestamp_utc.str.match(ISO)]
invalid_cal = x2[pd.to_datetime(x2.event_timestamp_utc, errors="coerce", utc=True).isna()]
x = pd.concat([x, invalid_cal]); detected["malformed_date"] = set(x.record_id)
add("DQ-M04", d, "event_timestamp_utc", "Malformed dates", len(x), "High", "Not ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ) or not a real calendar date/time.",
    "Mixed formats from different producers; manual edits.", "Parse known formats with explicit rules; quarantine the rest.", "Single timestamp format enforced by SDK and schema.", "Engineering", "Open", x.record_id)
st = md.status.str.strip()
valid_after_lower = md.apply(lambda r: r.status.strip().lower() in ALLOWED.get(r.source_table, set()), axis=1)
x = det("invalid_status", ~valid_after_lower)
add("DQ-M05", d, "status", "Invalid statuses", len(x), "High", "status (case-insensitive) not in the allowed list for the source table.",
    "Free-text statuses from manual processes or partner systems.", "Map to approved values only where meaning is certain; else quarantine.", "Enum validation against approved values.", "Engineering", "Open", x.record_id)
x = det("inconsistent_capitalization", valid_after_lower & (st != st.str.lower()))
add("DQ-M06", d, "status", "Inconsistent capitalization", len(x), "Low", "status valid only after lower-casing.", "No canonical casing.", "Lower-case in transformation.", "Enum validation is case-sensitive.", "Data/Analytics", "Open", x.record_id)
ws = md.drop(columns=["data_environment"]).apply(lambda s: s != s.str.strip()).any(axis=1)
x = det("trailing_spaces", ws)
add("DQ-M07", d, "event_name (any text field)", "Trailing spaces", len(x), "Low", "Leading/trailing whitespace in any text field.", "Manual entry or string concatenation.", "Trim in transformation.", "Trim at collection; schema regex.", "Data/Analytics", "Open", x.record_id)
amt = md.amount.str.strip()
num = pd.to_numeric(amt.where(amt != ""), errors="coerce")
x = det("invalid_numeric", (amt != "") & num.isna())
add("DQ-M08", d, "amount", "Invalid numeric values", len(x), "High", "amount not parseable as a number.", "Text in numeric field (units, typos, spreadsheet errors).", "Recover from source; never coerce silently.", "Numeric type at schema level.", "Engineering", "Open", x.record_id)
x = det("negative_value", num < 0)
add("DQ-M09", d, "amount", "Negative values where inappropriate", len(x), "High", "amount < 0 (amounts are absolute; direction is separate).", "Sign used instead of direction field.", "Use abs(amount) only if direction confirms; else quarantine.", "amount > 0 rule; direction enum.", "Engineering", "Open", x.record_id)
x = det("unexpected_null", (md.source_table == "withdrawals") & blank(md.payout_method))
add("DQ-M10", d, "payout_method", "Unexpected nulls", len(x), "Medium", "payout_method blank on a withdrawal record.", "Field dropped in export.", "Re-source from withdrawals table.", "Conditional-required rule.", "Engineering", "Open", x.record_id)
x = det("orphan_record", ~blank(md.user_id) & ~md.user_id.isin(users_ids))
add("DQ-M11", d, "user_id", "Orphan records", len(x), "Critical", "user_id not found in Users.", "Test/deleted accounts or wrong ID.", "Hold out of KPIs until resolved.", "Referential integrity check at load.", "Engineering", "Open", x.record_id)
key_cols = [c for c in md.columns if c not in ("record_id", "data_environment")]
x = det("duplicate_event", md.duplicated(subset=key_cols, keep="first"))
add("DQ-M12", d, "row", "Duplicate events", len(x), "Critical", "Identical rows (all fields except record_id).", "Producer retry without idempotency key.", "Drop later copies.", "event_id generated once and reused on retry; dedup on event_id.", "Engineering", "Open", x.record_id)
x = det("inconsistent_naming", ~md.event_name.str.strip().str.match(r"^[a-z]+(_[a-z]+)+$") | ~md.event_name.str.strip().isin(CATALOGUE))
add("DQ-M13", d, "event_name", "Inconsistent naming", len(x), "Medium", "event_name not snake_case object_action or not in the catalogue.", "No naming standard enforced.", "Map to catalogue names.", "Schema registry rejects unknown names.", "Engineering", "Open", x.record_id)


def norm_event(v):
    v = v.strip()
    v = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", v)
    return re.sub(r"[\s\-]+", "_", v).lower()


STAGE = {"withdrawal_requested": 0, "withdrawal_processing": 1, "withdrawal_completed": 2, "withdrawal_rejected": 2, "withdrawal_reversed": 3,
         "task_started": 0, "task_completed": 1}
w = md.copy()
w["stage"] = w.event_name.map(norm_event).map(STAGE)
w["ts"] = pd.to_datetime(w.event_timestamp_utc.where(w.event_timestamp_utc.str.match(ISO)), errors="coerce", utc=True)
w = w[w.stage.notna() & w.ts.notna()].drop_duplicates(subset=key_cols)
bad_rows = []
for ref_id, g in w.groupby("reference_id"):
    g = g.sort_values("stage")
    prev_max = None
    for row in g.itertuples():
        if prev_max is not None and row.ts < prev_max:
            bad_rows.append(row.record_id)
        prev_max = row.ts if prev_max is None else max(prev_max, row.ts)
x = det("impossible_state_transition", md.record_id.isin(bad_rows))
add("DQ-M14", d, "event_timestamp_utc / event_name", "Impossible state transitions", len(x), "Critical",
    "Within one reference_id, a later lifecycle stage is timestamped before an earlier stage (e.g. completed before requested).",
    "Clock issues, back-dated manual edits or out-of-order replay.", "Quarantine lifecycle; rebuild from status history.", "State machine enforced in backend; status history append-only.", "Engineering", "Open", x.record_id)

# Score scope C detection against the injection log
score = []
for kind in sorted(inj.injected_issue.unique()):
    planted = inj[inj.injected_issue == kind]
    if kind == "duplicate_id":
        planted_ids, found = set(planted.injected_value), detected["duplicate_id"]
    else:
        planted_ids, found = set(planted.record_id), detected.get(kind, set())
    score.append(dict(issue_type=kind, injected=len(planted_ids), detected=len(found), true_positive=len(planted_ids & found),
                      missed=len(planted_ids - found), false_positive=len(found - planted_ids),
                      false_positive_note=""))
score = pd.DataFrame(score)

issues_df = pd.DataFrame(issues)
issues_df.to_csv(OUT / "dq_issues.csv", index=False)
pd.DataFrame(evidence).to_csv(OUT / "dq_evidence.csv", index=False)
score.to_csv(OUT / "dq_detection_score.csv", index=False)
pd.DataFrame(summary_recon).to_csv(OUT / "supplied_summary_reconciliation.csv", index=False)
json.dump(dict(scope_a=scope_a_check, issues=len(issues_df), by_severity=issues_df.severity.value_counts().to_dict(),
               scope_c_injected=int(score.injected.sum()), scope_c_tp=int(score.true_positive.sum()),
               scope_c_missed=int(score.missed.sum()), scope_c_fp=int(score.false_positive.sum()),
               summary_reconciles=all(r["match"] for r in summary_recon)),
          open(BUILD_DIR / "stats_dq.json", "w"), indent=2, default=str)
print(issues_df[["issue_id", "field", "issue_type", "records_affected", "severity"]].to_string())
print(json.dumps(scope_a_check, indent=1, default=str))
print(score.to_string())
print(pd.DataFrame(summary_recon).to_string())
