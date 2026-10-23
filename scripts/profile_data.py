"""Work Package J: profile every dataset (J1), test relationships (J2), test KPI computability (J3).

Outputs build/profiling/*.csv and build/stats.json. Every number in the written deliverables
that describes data comes from build/stats.json, so documents and workbooks cannot drift apart.
All results describe SIMULATED data only.
"""
import json
import re

import numpy as np
import pandas as pd

from common import BUILD_DIR, PERIOD_END_UTC, SIM_DIR, ist_naive_to_utc, load_supplied
from specs.events import QUALIFYING_EVENTS

OUT = BUILD_DIR / "profiling"
OUT.mkdir(parents=True, exist_ok=True)
stats = {}

supplied = load_supplied()
users_clean = supplied["Users_1000_Clean"]
users_messy = supplied["Users_Messy_Audit"]
companion = {p.stem: pd.read_csv(p, dtype=str, keep_default_na=False)
             for p in sorted(SIM_DIR.glob("*.csv")) if p.stem != "messy_injection_log"}

DATASETS = [  # name, frame, origin, primary key, status column
    ("Users_1000_Clean", users_clean, "Supplied", "user_id", "account_status"),
    ("Users_Messy_Audit", users_messy, "Supplied", "user_id", "account_status"),
    ("Task_Activity", companion["Task_Activity"], "Analyst-generated", "activity_id", "activity_status"),
    ("Rewards", companion["Rewards"], "Analyst-generated", "reward_id", "reward_status"),
    ("Wallet", companion["Wallet"], "Analyst-generated", "transaction_id", "transaction_status"),
    ("Withdrawals", companion["Withdrawals"], "Analyst-generated", "withdrawal_id", "withdrawal_status"),
    ("Referrals", companion["Referrals"], "Analyst-generated", "referral_id", "referral_status"),
    ("Feature_Events", companion["Feature_Events"], "Analyst-generated", "event_id", "event_name"),
    ("Messy_Data", companion["Messy_Data"], "Analyst-generated", "record_id", "status"),
    ("Tasks", companion["Tasks"], "Analyst-generated (helper)", "task_id", None),
    ("Sessions", companion["Sessions"], "Analyst-generated (helper)", "session_id", None),
]
LABEL_COLS = {"data_environment"}
DT_RE = re.compile(r"(datetime|_utc)$")
NUMERIC_HINT = {"age", "lifetime_sessions", "active_days", "xp_balance", "days_since_registration", "reward_amount",
                "amount", "final_amount", "amount_inr", "ve_debited"}


def parse_dt(name, s):
    blank = s.str.strip() == ""
    if name.endswith("_utc"):
        parsed = pd.to_datetime(s.where(~blank), errors="coerce", utc=True, format="%Y-%m-%dT%H:%M:%SZ")
    else:
        parsed = pd.to_datetime(s.where(~blank), errors="coerce", format="%Y-%m-%d %H:%M:%S")
    return parsed, int((parsed.isna() & ~blank).sum())


summary, columns, status_rows = [], [], []
for name, df, origin, pk, status_col in DATASETS:
    body = df.drop(columns=[c for c in df.columns if c in LABEL_COLS])
    missing_total = int((df.apply(lambda s: s.str.strip() == "")).sum().sum())
    dt_cols = [c for c in df.columns if DT_RE.search(c)]
    mins, maxs = [], []
    for c in df.columns:
        s = df[c]
        blank = s.str.strip() == ""
        nun = s[~blank].nunique()
        row = dict(dataset=name, column=c, non_blank=int((~blank).sum()), missing=int(blank.sum()),
                   missing_pct=round(100 * blank.mean(), 2), unique_values=int(nun), inferred_type="string",
                   min="", max="", mean="", unparseable=0, top_values="")
        if c in dt_cols:
            parsed, bad = parse_dt(c, s)
            row.update(inferred_type="datetime", unparseable=bad)
            if parsed.notna().any():
                row.update(min=str(parsed.min()), max=str(parsed.max()))
                mins.append(parsed.min().tz_localize(None) if parsed.min().tzinfo else parsed.min())
                maxs.append(parsed.max().tz_localize(None) if parsed.max().tzinfo else parsed.max())
        elif c in NUMERIC_HINT or (nun and pd.to_numeric(s[~blank], errors="coerce").notna().all() and not c.endswith("_id")):
            num = pd.to_numeric(s[~blank], errors="coerce")
            row.update(inferred_type="numeric", unparseable=int(num.isna().sum()))
            if num.notna().any():
                row.update(min=float(num.min()), max=float(num.max()), mean=round(float(num.mean()), 2))
        if nun <= 30:
            row["inferred_type"] = "categorical" if row["inferred_type"] == "string" else row["inferred_type"]
            row["top_values"] = "; ".join(f"{k!r}: {v}" for k, v in s.value_counts().head(12).items())
        columns.append(row)
    pk_series = df[pk]
    exact_dups = int(body.duplicated().sum())
    summary.append(dict(
        dataset=name, origin=origin, records=len(df), columns=len(df.columns), primary_key=pk,
        unique_ids=int(pk_series[pk_series.str.strip() != ""].nunique()), duplicate_ids=int(pk_series[pk_series.str.strip() != ""].duplicated().sum()),
        exact_duplicate_rows=exact_dups, missing_cells=missing_total,
        date_columns=", ".join(dt_cols), date_min=str(min(mins)) if mins else "", date_max=str(max(maxs)) if maxs else "",
        simulated_label=", ".join(sorted(set(df["data_environment"]))) if "data_environment" in df else "MISSING (no label column)"))
    if status_col:
        vc = df[status_col].value_counts()
        for k, v in vc.items():
            status_rows.append(dict(dataset=name, status_column=status_col, value=k, records=int(v), pct=round(100 * v / len(df), 2)))

summary = pd.DataFrame(summary)
columns = pd.DataFrame(columns)
status_dist = pd.DataFrame(status_rows)

# --------------------------------------------------------------------------------------------
# J2 relationship tests
# --------------------------------------------------------------------------------------------
U = set(users_clean.user_id)
tables = dict(companion)
tables["Users_1000_Clean"] = users_clean
tables["Users_Messy_Audit"] = users_messy
rel_rows = []


def fk_test(test_id, child, ccol, parent, pcol, where=None, note=""):
    c = tables[child]
    if where is not None:
        c = c[where(c)]
    vals = c[ccol][c[ccol].str.strip() != ""]
    pvals = set(tables[parent][pcol])
    orphans = vals[~vals.isin(pvals)]
    rel_rows.append(dict(test_id=test_id, child=f"{child}.{ccol}", parent=f"{parent}.{pcol}", child_rows_tested=len(vals),
                         blank_keys=int((c[ccol].str.strip() == "").sum()), matched=int(len(vals) - len(orphans)),
                         orphans=int(len(orphans)), orphan_examples=", ".join(orphans.unique()[:5]),
                         result="PASS" if len(orphans) == 0 else "FAIL", note=note))


not_testable = [
    ("R00a", "Task Activity.user_id", "Supplied workbook has no Task Activity sheet."),
    ("R00b", "Rewards.user_id", "Supplied workbook has no Rewards sheet."),
    ("R00c", "Wallet.user_id", "Supplied workbook has no Wallet sheet."),
    ("R00d", "Withdrawals.user_id", "Supplied workbook has no Withdrawals sheet."),
    ("R00e", "Referrals.user_id", "Supplied workbook has no Referrals sheet; Users has no referrer field."),
    ("R00f", "Feature Events.user_id", "Supplied workbook has no Feature Events sheet."),
]
for tid, child, why in not_testable:
    rel_rows.append(dict(test_id=tid, child=child + " (supplied)", parent="Users_1000_Clean.user_id", child_rows_tested=0, blank_keys=0,
                         matched=0, orphans=0, orphan_examples="", result="NOT TESTABLE", note=why))

fk_test("R01", "Users_Messy_Audit", "user_id", "Users_1000_Clean", "user_id", note="Supplied audit sheet against supplied clean sheet.")
fk_test("R02", "Task_Activity", "user_id", "Users_1000_Clean", "user_id")
fk_test("R03", "Rewards", "user_id", "Users_1000_Clean", "user_id")
fk_test("R04", "Wallet", "user_id", "Users_1000_Clean", "user_id")
fk_test("R05", "Withdrawals", "user_id", "Users_1000_Clean", "user_id")
fk_test("R06", "Referrals", "referrer_user_id", "Users_1000_Clean", "user_id")
fk_test("R07", "Referrals", "referred_user_id", "Users_1000_Clean", "user_id")
fk_test("R08", "Feature_Events", "user_id", "Users_1000_Clean", "user_id")
fk_test("R09", "Sessions", "user_id", "Users_1000_Clean", "user_id")
fk_test("R10", "Task_Activity", "task_id", "Tasks", "task_id")
fk_test("R11", "Task_Activity", "session_id", "Sessions", "session_id")
fk_test("R12", "Feature_Events", "session_id", "Sessions", "session_id")
fk_test("R13", "Rewards", "source_id", "Task_Activity", "activity_id", where=lambda d: d.source_type == "task")
fk_test("R14", "Rewards", "source_id", "Feature_Events", "event_id", where=lambda d: d.source_type.isin(["daily_reward", "spin", "mission", "badge"]))
fk_test("R15", "Rewards", "source_id", "Referrals", "referral_id", where=lambda d: d.source_type == "referral")
fk_test("R16", "Rewards", "wallet_transaction_id", "Wallet", "transaction_id")
fk_test("R17", "Wallet", "related_transaction_id", "Wallet", "transaction_id")
fk_test("R18", "Wallet", "reference_id", "Rewards", "reward_id", where=lambda d: d.reference_type == "reward")
fk_test("R19", "Wallet", "reference_id", "Withdrawals", "withdrawal_id", where=lambda d: d.reference_type == "withdrawal")
fk_test("R20", "Withdrawals", "debit_transaction_id", "Wallet", "transaction_id")
fk_test("R21", "Messy_Data", "user_id", "Users_1000_Clean", "user_id", note="Orphans expected: injected defect.")

rels = pd.DataFrame(rel_rows)

# Semantic relationship checks (beyond key existence)
uc = users_clean.copy()
uc["reg_utc"] = ist_naive_to_utc(uc.registration_datetime)
reg = uc.set_index("user_id").reg_utc
sem = []
ta = companion["Task_Activity"]
t_start = pd.to_datetime(ta.started_at_utc, utc=True)
sem.append(("S01", "Task activity starts on or after the user's registration", int((t_start < ta.user_id.map(reg)).sum()), len(ta)))
fe = companion["Feature_Events"]
sem.append(("S02", "Feature events on or after the user's registration", int((pd.to_datetime(fe.event_timestamp_utc, utc=True) < fe.user_id.map(reg)).sum()), len(fe)))
pending_ids = set(uc[uc.account_status == "Pending Verification"].user_id)
sem.append(("S03", "No task activity for 'Pending Verification' users (they have no login)", int(ta.user_id.isin(pending_ids).sum()), len(ta)))
ref = companion["Referrals"]
ref_users = set(uc[uc.acquisition_source == "Referral"].user_id)
linked = set(ref.referred_user_id[ref.referred_user_id != ""])
sem.append(("S04", "Every supplied user with acquisition_source = Referral can be linked to a referrer (only in companion data)", len(ref_users - linked), len(ref_users)))
sem.append(("S05", "No self-referrals", int((ref.referrer_user_id == ref.referred_user_id).sum()), len(ref)))
rw = companion["Rewards"]
wl = companion["Wallet"]
cred_wallet = rw[rw.unit.isin(["VE", "GEM"]) & rw.reward_status.isin(["credited", "reversed", "corrected"])]
sem.append(("S06", "Every credited/reversed/corrected VE or GEM reward has a wallet credit", int((cred_wallet.wallet_transaction_id == "").sum()), len(cred_wallet)))
wd = companion["Withdrawals"]
sem.append(("S07", "Every withdrawal has exactly one redemption debit", int((wl[wl.transaction_type == "redemption_debit"].reference_id.value_counts().reindex(wd.withdrawal_id).fillna(0) != 1).sum()), len(wd)))
# Running VE balance never negative in companion ledger
w = wl[wl.unit == "VE"].copy()
w["signed"] = np.where(w.direction == "credit", 1, -1) * w.amount.astype(int)
w = w[w.transaction_status != "failed"].sort_values(["user_id", "created_at_utc", "direction"])
w["bal"] = w.groupby("user_id").signed.cumsum()
sem.append(("S08", "Simulated VE running balance never negative (a negative balance means a reward was reversed after its VEs were redeemed)", int(w.groupby("user_id").bal.min().lt(0).sum()), w.user_id.nunique()))
def order_violations(df, cols):
    t = [pd.to_datetime(df[c].replace("", None), utc=True) for c in cols]
    bad = pd.Series(False, index=df.index)
    for a, b in zip(t, t[1:]):
        bad |= (a.notna() & b.notna() & (b < a))
    return int(bad.sum())


sem.append(("S09", "Withdrawal timestamps ordered: requested <= processing <= final", order_violations(wd, ["requested_at_utc", "processing_at_utc", "final_at_utc"]), len(wd)))
sem.append(("S10", "Task timestamps ordered: started <= completed", order_violations(ta, ["started_at_utc", "completed_at_utc"]), len(ta)))
sem.append(("S11", "Reward timestamps ordered: created <= credited <= reversed", order_violations(rw, ["created_at_utc", "credited_at_utc", "reversed_at_utc"]), len(rw)))
sem.append(("S12", "Referral timestamps ordered: created <= registered <= activated <= converted", order_violations(ref, ["created_at_utc", "registered_at_utc", "activated_at_utc", "converted_at_utc"]), len(ref)))
sem.append(("S13", "Wallet timestamps ordered: created <= completed", order_violations(wl, ["created_at_utc", "completed_at_utc"]), len(wl)))
sem = pd.DataFrame(sem, columns=["test_id", "check", "violations", "rows_tested"])
sem["result"] = np.where(sem.violations == 0, "PASS", np.where(sem.test_id == "S08", "FLAG (kept on purpose, see A-020)", "FAIL"))

# --------------------------------------------------------------------------------------------
# J3 KPI computability tests (supplied structure vs companion structure)
# --------------------------------------------------------------------------------------------
day = lambda s: pd.to_datetime(s, utc=True).dt.tz_convert("Asia/Kolkata").dt.date
fe["day"] = day(fe.event_timestamp_utc)
q = fe[fe.event_name.isin(QUALIFYING_EVENTS)]
ta["day"] = day(ta.started_at_utc)
ta_q = ta.assign(event_name="task_started")[["user_id", "day", "event_name"]]
qual = pd.concat([q[["user_id", "day", "event_name"]], ta_q])
last_day = PERIOD_END_UTC.tz_convert("Asia/Kolkata").date()
dau_last = qual[qual.day == last_day].user_id.nunique()
mau_window = qual[(qual.day > last_day - pd.Timedelta(days=30))]
mau = mau_window.user_id.nunique()
wau = qual[(qual.day > last_day - pd.Timedelta(days=7))].user_id.nunique()
win_start = last_day - pd.Timedelta(days=29)
before = set(qual[qual.day < win_start].user_id)
reg_day = uc.set_index("user_id").reg_utc.dt.tz_convert("Asia/Kolkata").dt.date
returning = sum(1 for u in set(mau_window.user_id) if u in before and reg_day[u] < win_start)
ta_mature = ta[pd.to_datetime(ta.started_at_utc, utc=True) <= PERIOD_END_UTC - pd.Timedelta(days=3)]
comp_rate = (ta_mature.activity_status.eq("completed") & ta_mature.validation_status.eq("passed")).mean()
resolved = wd[wd.withdrawal_status.isin(["completed", "rejected", "reversed"])]
proc_h = (pd.to_datetime(resolved.final_at_utc, utc=True) - pd.to_datetime(resolved.requested_at_utc, utc=True)).dt.total_seconds() / 3600
regd = ref[ref.referral_status.isin(["registered", "activated", "converted", "rejected"])]
credited = rw[rw.reward_status.isin(["credited", "reversed", "corrected"])]
uc_verified = (users_clean.email_verification_status == "Verified").mean()

kpi_tests = [
    ("K-USR-01", "New Registrations", "Yes", "registration_datetime exists, one row per user_id.", "Timezone of registration_datetime (assumed IST, A-004).",
     f"{len(users_clean)} registrations between {users_clean.registration_datetime.min()[:10]} and {users_clean.registration_datetime.max()[:10]}"),
    ("K-USR-02", "Daily Active Users", "No", "Supplied data has only last_login_datetime (a single latest snapshot) and login-based flags; no per-day activity history.",
     "Event-level activity: feature_events with user_id, event_name, event_timestamp_utc; agreed qualifying-event list.",
     f"{dau_last} users on {last_day} (IST) in companion Feature_Events + Task_Activity"),
    ("K-USR-03", "Weekly Active Users", "Partial", "is_active_7d exists but is login-based, uses an undocumented reference date (inferred 2026-09-15 00:00) and cannot be recomputed for other weeks.",
     "Event history + documented reference date.", f"{wau} users in the 7 IST days to {last_day} (companion)"),
    ("K-USR-04", "Monthly Active Users", "Partial", "Same limitation as WAU (is_active_30d).", "Event history.", f"{mau} users in the 30 IST days to {last_day} (companion)"),
    ("K-USR-06", "Returning Users", "No", "No session or login history; only a lifetime_sessions counter.", "sessions table or user_logged_in events with timestamps.",
     f"{returning} of {mau} users active in the 30 IST days to {last_day} were also active earlier and registered before the window (companion)"),
    ("K-USR-08", "Onboarding Completion Rate", "Partial", "onboarding_status exists but no start/complete timestamps, so no cohort or 7-day window.",
     "onboarding_started_at_utc, onboarding_completed_at_utc.", f"Snapshot only: {int((users_clean.onboarding_status == 'Completed').sum())} of {len(users_clean)} users show 'Completed'"),
    ("K-USR-09", "Email Verification Rate", "Partial", "Status exists; no verification timestamp so the 7-day window cannot be applied.", "email_verified_at_utc.",
     f"Snapshot only: {round(100 * uc_verified, 1)}% of supplied users 'Verified'"),
    ("K-USR-11", "Account Suspensions", "No", "account_status is a snapshot; when a user became Suspended is unknown.", "user_status_history.", "Not computable from either structure"),
    ("K-ENG-04", "Task Completion Rate", "No (supplied) / Yes (companion)", "No task data supplied.", "task_activity with activity_status and validation_status.",
     f"{round(100 * comp_rate, 1)}% of companion attempts started up to 3 days before period end were validated completions"),
    ("K-RWD-02", "Rewards Credited", "No (supplied) / Yes (companion)", "No reward data supplied; xp_balance is a balance without a ledger.", "rewards with reward_status, final_amount, unit.",
     f"{len(credited)} reward records reached credited at least once in companion data"),
    ("K-RWD-02 (INR)", "Reward cost in INR", "No", "No approved VE/GEM to INR conversion rate in any source.", "Official conversion rates with effective dates.", "Not computable"),
    ("K-WDR-06", "Withdrawal Processing Time", "No (supplied) / Yes (companion)", "No withdrawal data supplied.", "requested_at_utc and final_at_utc per withdrawal.",
     f"Median {round(float(proc_h.median()), 1)} h, P90 {round(float(proc_h.quantile(0.9)), 1)} h over {len(resolved)} resolved companion withdrawals"),
    ("K-REF-05", "Referral Conversion Rate", "No", "Supplied Users has referral_source_detail = 'Friend/Family' only: no referrer ID, no activation or conversion.",
     "referrals table with referrer_user_id, referred_user_id and stage timestamps.",
     f"{int((ref.referral_status == 'converted').sum())} converted of {len(regd)} registered companion referrals"),
    ("K-SUP-01", "Support Requests", "No", "No support data supplied or generated as a table (only support_ticket_created events).", "support_tickets table from the support tool.",
     f"{int((fe.event_name == 'support_ticket_created').sum())} support_ticket_created events in companion Feature_Events; no timestamps for response"),
]
kpi_tests = pd.DataFrame(kpi_tests, columns=["kpi_id", "kpi", "computable_from_supplied", "why", "additional_data_required", "result_on_simulated_data"])
kpi_tests["data_note"] = "Simulated values for structure testing only, not VELOOP results"

# --------------------------------------------------------------------------------------------
# Key stats for documents
# --------------------------------------------------------------------------------------------
stats["datasets"] = summary.set_index("dataset")[["records", "columns", "unique_ids", "duplicate_ids", "exact_duplicate_rows", "missing_cells", "date_min", "date_max"]].to_dict("index")
stats["relationship_fail"] = rels[rels.result == "FAIL"].test_id.tolist()
stats["relationship_not_testable"] = int((rels.result == "NOT TESTABLE").sum())
stats["relationship_tests"] = len(rels)
stats["semantic_fail"] = sem[sem.result == "FAIL"].test_id.tolist()
stats["referral_users_unlinked_in_companion"] = int(sem.set_index("test_id").violations["S04"])
stats["kpi_tests"] = len(kpi_tests)
stats["kpi_not_computable_supplied"] = int(kpi_tests.computable_from_supplied.str.startswith("No").sum())
stats["kpi_partial_supplied"] = int((kpi_tests.computable_from_supplied == "Partial").sum())
stats["kpi_yes_supplied"] = int((kpi_tests.computable_from_supplied == "Yes").sum())
stats["sim_returning"] = int(returning); stats["sim_dau_last_day"] = int(dau_last); stats["sim_wau"] = int(wau); stats["sim_mau"] = int(mau)
stats["sim_completion_rate_pct"] = round(100 * comp_rate, 1)
stats["sim_wdr_median_h"] = round(float(proc_h.median()), 1)
stats["sim_wdr_p90_h"] = round(float(proc_h.quantile(0.9)), 1)

summary.to_csv(OUT / "J1_summary.csv", index=False)
columns.to_csv(OUT / "J1_columns.csv", index=False)
status_dist.to_csv(OUT / "J1_status_distribution.csv", index=False)
rels.to_csv(OUT / "J2_relationships.csv", index=False)
sem.to_csv(OUT / "J2_semantic_checks.csv", index=False)
kpi_tests.to_csv(OUT / "J3_kpi_tests.csv", index=False)
(BUILD_DIR / "stats_profile.json").write_text(json.dumps(stats, indent=2, default=str))
print(summary[["dataset", "records", "columns", "unique_ids", "duplicate_ids", "exact_duplicate_rows", "missing_cells", "date_min", "date_max"]].to_string())
print(rels[["test_id", "child", "parent", "child_rows_tested", "orphans", "result"]].to_string())
print(sem.to_string())
print(kpi_tests[["kpi_id", "computable_from_supplied", "result_on_simulated_data"]].to_string())
