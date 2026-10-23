"""Cross-consistency validator. Fails (exit 1) if any deliverable contradicts another.

Checks specs against each other, simulated data against specs, and generated documents for
leftover placeholders, broken references, missing simulated-data banners and em-dashes
(allowed only inside the two mandated dataset labels).
"""
import json
import re
import sys

import pandas as pd

from common import BUILD_DIR, OUT_DIR, SIM_DIR, SIM_LABEL, SUPPLIED_LABEL
from specs import coverage as CV
from specs import dictionary as DI
from specs import enums as E
from specs import events as EV
from specs import kpis as KP
from specs import model as MO
from specs import operations as OP
from specs import registers as RG

errors, passed = [], []


def check(name, bad):
    bad = list(bad)
    (errors.append(f"FAIL {name}: {bad[:10]}") if bad else passed.append(name))


fields = pd.DataFrame(DI.FIELDS)
field_names = set(fields.field_name)
ent_field = set(zip(fields.entity, fields.field_name))
event_names = [e["event_name"] for e in EV.EVENTS]
kpi_ids = [k["kpi_id"] for k in KP.KPIS]

# ---------------------------------------------------------------- specs
check("event names unique", {e for e in event_names if event_names.count(e) > 1})
check("event names match object_action regex", [e for e in event_names if not re.fullmatch(r"[a-z]+(_[a-z]+)+", e)])
check("event names end with an approved past-tense action", [e for e in event_names if not any(e.endswith("_" + a) for a in EV.APPROVED_ACTIONS)])
check("brief minimum events present", [e for e in [
    "user_registered", "user_logged_in", "user_logged_out", "onboarding_started", "onboarding_completed", "task_viewed", "task_opened",
    "task_started", "task_completed", "task_failed", "reward_credited", "reward_pending", "reward_reversed", "daily_reward_claimed",
    "streak_updated", "mission_started", "mission_completed", "badge_earned", "spin_started", "spin_completed", "referral_created",
    "referral_registered", "referral_activated", "referral_converted", "wallet_transaction_created", "wallet_transaction_completed",
    "wallet_transaction_reversed", "withdrawal_requested", "withdrawal_processing", "withdrawal_completed", "withdrawal_rejected",
    "withdrawal_reversed"] if e not in event_names])
check(">= 25 events", [] if len(event_names) >= 25 else [len(event_names)])
check("event properties defined in dictionary", [(e["event_name"], p) for e in EV.EVENTS
                                                 for p in e["required_properties"] + e["optional_properties"] if p not in field_names])
check("envelope fields defined", [p for p in EV.ENVELOPE_REQUIRED + EV.ENVELOPE_CLIENT_EXTRA + EV.ENVELOPE_OPTIONAL if p not in field_names])
check("event features are allowed values", [(e["event_name"], e["feature"]) for e in EV.EVENTS if e["feature"] not in E.FEATURES])
check("money/status events are server-side", [e["event_name"] for e in EV.EVENTS if e["domain"] in ("Rewards", "Wallet", "Withdrawals", "Referrals")
                                             and e["event_source"] != "server"])
check("event KPI dependencies exist", [(e["event_name"], k) for e in EV.EVENTS for k in e["kpi_dependency"] if k not in kpi_ids])
check("KPI ids unique", {k for k in kpi_ids if kpi_ids.count(k) > 1})
check(">= 30 KPIs", [] if len(kpi_ids) >= 30 else [len(kpi_ids)])
check("every KPI has all 11 required attributes", [k["kpi_id"] for k in KP.KPIS for a in
                                                   ["name", "definition", "formula", "required_fields", "data_source", "frequency", "stakeholder",
                                                    "business_purpose", "interpretation", "limitation", "status"] if not k[a]])
check("KPI required fields exist as entity.field", [(k["kpi_id"], f) for k in KP.KPIS for f in k["required_fields"]
                                                    if tuple(f.split(".")) not in ent_field])
check("KPIs contain no targets", [k["kpi_id"] for k in KP.KPIS if re.search(r"\b(target|should (be|have|reach))\b", " ".join(map(str, k.values())), re.I)
                                  and "not an internal target" not in k["business_purpose"]])
check("dictionary (entity, field) unique", fields[fields.duplicated(["entity", "field_name"])].field_name.tolist())
check(">= 75 dictionary fields", [] if len(fields) >= 75 else [len(fields)])
check("dictionary required in Yes/No/Conditional", fields[~fields.required.isin(["Yes", "No", "Conditional"])].field_name.tolist())
check("dictionary sensitivity valid", fields[~fields.sensitivity.isin(["Public", "Internal", "Restricted"])].field_name.tolist())
check("dictionary all 12 attributes filled", [f["field_name"] for f in DI.FIELDS for a in
                                              ["entity", "field_name", "data_type", "definition", "example", "required", "validation", "source",
                                               "sensitivity", "analytical_use", "status"] if not f[a]])
check("enum-typed fields list allowed values", fields[(fields.data_type == "enum") & (fields.allowed_values == "")].field_name.tolist())
check("no personal identifiers in model", [f for f in ["full_name", "email", "phone", "gender", "city", "age", "upi_id", "password"] if f in field_names])

for e, (desc, pk, fks, grain, why) in MO.ENTITIES.items():
    check(f"model {e}: PK in dictionary", [p for p in pk if (e, p) not in ent_field])
    check(f"model {e}: FK fields in dictionary", [f for f, _, _ in fks if (e, f) not in ent_field])
check("ER fields in dictionary", [(e, f.split()[0]) for e, fl in MO.ER_FIELDS.items() for f in fl if (e, f.split()[0]) not in ent_field])
check("ER entities == model entities", set(MO.ER_FIELDS) ^ set(MO.ENTITIES))
check("required model entities present", [e for e in ["users", "tasks", "task_activity", "rewards", "wallet_transactions", "withdrawals", "referrals", "feature_events"] if e not in MO.ENTITIES])
check("mermaid edges use model entities", [(a, b) for a, _, b, _ in MO.MERMAID_EDGES if a not in MO.ENTITIES or b not in MO.ENTITIES])


def kpi_refs(text):
    out = set(re.findall(r"K-[A-Z]{3}-\d{2}", text))
    for prefix, lo, hi in re.findall(r"(K-[A-Z]{3}-)(\d{2})\.\.(?:K-[A-Z]{3}-)?(\d{2})", text):
        out |= {f"{prefix}{i:02d}" for i in range(int(lo), int(hi) + 1)}
    return out


check("dashboard metrics reference existing KPIs", [(d["visual"], k) for d in OP.DASHBOARDS for k in kpi_refs(d["metric"]) if k not in kpi_ids])
check("every dashboard visual references a KPI", [d["visual"] for d in OP.DASHBOARDS if not kpi_refs(d["metric"])])
check("handoff events exist", [e for e in OP.HANDOFF if e not in event_names])
check("all Critical events have handoff specs", [e["event_name"] for e in EV.EVENTS if e["priority"] == "Critical" and e["event_name"] not in OP.HANDOFF])
cov_events = {x.strip() for c in CV.COVERAGE for x in c["proposed_events"].split(";")} - {"None now"}
check("coverage events exist", [e for e in cov_events if e not in event_names])
life_events = {x.strip() for v in CV.LIFECYCLES.values() for _, ev, _ in v for x in re.split(r"[/;]|->", ev) if x.strip() and "derived" not in x}
check("lifecycle events exist", [e for e in life_events if e not in event_names])
check("every catalogue event appears in coverage matrix", [e for e in event_names if e not in cov_events])
check(">= 10 analytics gaps", [] if len(CV.GAPS) >= 10 else [len(CV.GAPS)])

# ---------------------------------------------------------------- simulated data vs specs
TABLE_ENTITY = {"Tasks": "tasks", "Sessions": "sessions", "Task_Activity": "task_activity", "Rewards": "rewards", "Wallet": "wallet_transactions",
                "Withdrawals": "withdrawals", "Referrals": "referrals", "Feature_Events": "feature_events"}
ENUM_CHECK = {("Task_Activity", "activity_status"): E.ACTIVITY_STATUSES, ("Task_Activity", "validation_status"): E.VALIDATION_STATUSES,
              ("Task_Activity", "failure_category"): E.FAILURE_CATEGORIES, ("Task_Activity", "task_type"): E.TASK_TYPES,
              ("Task_Activity", "feature"): E.FEATURES, ("Task_Activity", "reward_unit"): E.REWARD_UNITS,
              ("Rewards", "reward_status"): E.REWARD_STATUSES, ("Rewards", "source_type"): E.REWARD_SOURCE_TYPES, ("Rewards", "unit"): E.REWARD_UNITS,
              ("Rewards", "reversal_reason_category"): E.REVERSAL_REASONS, ("Rewards", "feature"): E.FEATURES,
              ("Wallet", "transaction_type"): E.TRANSACTION_TYPES, ("Wallet", "direction"): E.DIRECTIONS, ("Wallet", "unit"): E.WALLET_UNITS,
              ("Wallet", "transaction_status"): E.TRANSACTION_STATUSES, ("Wallet", "reference_type"): E.REFERENCE_TYPES,
              ("Withdrawals", "withdrawal_status"): E.WITHDRAWAL_STATUSES, ("Withdrawals", "payout_method"): E.PAYOUT_METHODS,
              ("Withdrawals", "reason_category"): E.WITHDRAWAL_REASONS, ("Referrals", "referral_status"): E.REFERRAL_STATUSES,
              ("Referrals", "referral_channel"): E.REFERRAL_CHANNELS, ("Referrals", "rejection_reason_category"): E.REFERRAL_REJECTION_REASONS,
              ("Feature_Events", "event_name"): event_names, ("Feature_Events", "feature"): E.FEATURES, ("Feature_Events", "platform"): E.PLATFORMS,
              ("Tasks", "fulfilment_source"): E.FULFILMENT_SOURCES}
for t, ent in TABLE_ENTITY.items():
    df = pd.read_csv(SIM_DIR / f"{t}.csv", dtype=str, keep_default_na=False)
    check(f"{t}: every column defined in dictionary entity {ent}", [c for c in df.columns if c != "data_environment" and (ent, c) not in ent_field])
    check(f"{t}: every row labelled simulated", [] if (df.data_environment == SIM_LABEL).all() else ["unlabelled rows"])
for (t, c), allowed in ENUM_CHECK.items():
    df = pd.read_csv(SIM_DIR / f"{t}.csv", dtype=str, keep_default_na=False)
    check(f"{t}.{c} values allowed", sorted(set(df[c][df[c] != ""]) - set(allowed)))
md = pd.read_csv(SIM_DIR / "Messy_Data.csv", dtype=str, keep_default_na=False)
check("Messy_Data labelled and >= 500 rows", [] if (md.data_environment == SIM_LABEL).all() and len(md) >= 500 else ["label or size"])
check("methodology documented", [] if (SIM_DIR / "GENERATION_METHODOLOGY.md").exists() else ["missing GENERATION_METHODOLOGY.md"])

# ---------------------------------------------------------------- results
dq = json.loads((BUILD_DIR / "stats_dq.json").read_text())
check("supplied Synthetic_Summary reconciles", [] if dq["summary_reconciles"] else ["mismatch"])
check("DQ detection: all injected defects found, no false positives",
      [] if dq["scope_c_tp"] == dq["scope_c_injected"] and dq["scope_c_fp"] == 0 else [dq])
check("DQ detection on supplied messy sheet exact", [] if not dq["scope_a"]["missed"] and not dq["scope_a"]["extra_detected"] else [dq["scope_a"]])
sem = pd.read_csv(BUILD_DIR / "profiling" / "J2_semantic_checks.csv")
check("semantic checks pass (S08 intentionally flagged)", sem[(sem.result == "FAIL")].test_id.tolist())
rel = pd.read_csv(BUILD_DIR / "profiling" / "J2_relationships.csv")
check("only the intended relationship test fails (R21)", sorted(set(rel[rel.result == "FAIL"].test_id) - {"R21"}))

# ---------------------------------------------------------------- documents
docs = {p.name: p.read_text() for p in OUT_DIR.glob("*.md")}
check("21 numbered deliverables present", sorted({f"{i:02d}" for i in range(1, 22)} - {n[:2] for n in docs}))
all_text = "\n".join(docs.values())
check("no unformatted placeholders", re.findall(r"\{(?:n_[a-z_]+|NEG|REFU|[A-Z]\[[^\]]*\])\}", all_text))
ids = {"A": {a[0] for a in RG.ASSUMPTIONS}, "SRC": {s[0] for s in RG.SOURCES}, "BL": {b[0] for b in OP.BACKLOG}, "G": {g[0] for g in CV.GAPS},
       "QC": {r[0] for r in OP.DQ_RULES}, "K": set(kpi_ids)}
dq_ids = set(pd.read_csv(BUILD_DIR / "dq" / "dq_issues.csv").issue_id)
spec_text = all_text + json.dumps([OP.DQ_RULES, OP.READINESS, OP.BACKLOG, RG.ASSUMPTIONS, CV.COVERAGE, CV.GAPS], default=str)
check("assumption refs exist", sorted(set(re.findall(r"\bA-\d{3}\b", spec_text)) - ids["A"]))
check("source refs exist", sorted(set(re.findall(r"\bSRC-\d{2}\b", spec_text)) - ids["SRC"]))
check("backlog refs exist", sorted(set(re.findall(r"\bBL-\d{2}\b", spec_text)) - ids["BL"]))
check("gap refs exist", sorted(set(re.findall(r"\bG\d{2}\b", spec_text)) - ids["G"]))
check("QC refs exist", sorted(set(re.findall(r"\bQC-\d{2}\b", spec_text)) - ids["QC"]))
check("KPI refs in docs exist", sorted(kpi_refs(all_text) - ids["K"]))
check("DQ issue refs exist", sorted({d for d in re.findall(r"\bDQ-[A-Z]-?[A-Z0-9-]*\d\b", spec_text) if not d.startswith("DQ-U-MISS")} - dq_ids))
for name in ["01", "12", "13", "21"]:
    doc = next(v for k, v in docs.items() if k.startswith(name))
    check(f"doc {name} carries simulated-data banner", [] if "SIMULATED DATA NOTICE" in doc else [name])
dash_ok = lambda t: t.replace(SIM_LABEL, "").replace(SUPPLIED_LABEL, "")
check("no em-dashes outside mandated labels (docs)", [k for k, v in docs.items() if "—" in dash_ok(v)])
check("no fabricated performance phrasing", [m for m in re.findall(r"VELOOP (?:has|had) [\d,.]+[^.]*", all_text)])
counts = json.loads((BUILD_DIR / "counts.json").read_text())
check("doc counts match specs", [] if counts["n_events"] == len(event_names) and counts["n_kpis"] == len(kpi_ids)
      and counts["n_fields"] == len(fields) and counts["n_entities"] == len(MO.ENTITIES) else [counts])

print(f"{len(passed)} checks passed, {len(errors)} failed")
for e in errors:
    print(e)
sys.exit(1 if errors else 0)
