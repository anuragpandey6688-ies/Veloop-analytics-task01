"""Generate the companion simulated datasets that the supplied workbook does not contain.

The supplied workbook (VELoop_Rewards_Data_01.xlsx) holds only Users data. Task 01 section 16
expects Task Activity, Rewards, Wallet, Withdrawals, Referrals, Feature Events and Messy Data,
and section 28 allows the analyst to create additional simulated data if every dataset carries
the label "SIMULATED DATA — CREATED FOR ANALYTICAL TESTING" and its methodology is documented.

Methodology (also written to data/simulated/GENERATION_METHODOLOGY.md):
  * Deterministic: numpy Generator seeded with common.SEED, so every run gives identical output.
  * Anchored on the supplied Users_1000_Clean sheet: only supplied user_ids are used, and a user's
    activity is placed between their registration_datetime and last_login_datetime (assumed IST).
  * Users with no last_login_datetime (all 72 "Pending Verification" users) get no activity.
  * The clean companion tables are internally consistent on purpose. Defects are injected only
    into Messy_Data, and every injected defect is written to messy_injection_log.csv so the
    data-quality audit can be checked against a known ground truth.
  * Distributions deliberately include failure, abandonment, pending, rejection and reversal.
    They are NOT tuned to make VELOOP look successful (section 29) and are NOT estimates of
    real VELOOP behaviour.
"""
import numpy as np
import pandas as pd

from common import (PAYOUT_METHODS, PERIOD_END_UTC, SEED, SIM_DIR, SIM_LABEL, SIM_VE_PER_INR,
                    ist_naive_to_utc, iso, load_supplied)

rng = np.random.default_rng(SEED)
MIN = pd.Timedelta(minutes=1)


def rand_between(start, end, n=None):
    """Uniform random UTC timestamps between start and end (inclusive of start)."""
    span = max((end - start).total_seconds(), 60)
    secs = rng.uniform(0, span, size=n)
    if n is None:
        return (start + pd.Timedelta(seconds=float(secs))).floor("s")
    return pd.DatetimeIndex([start + pd.Timedelta(seconds=float(s)) for s in secs]).floor("s")


def weighted_choice(options, probs, size=None):
    probs = np.array(probs, dtype=float)
    return rng.choice(options, size=size, p=probs / probs.sum())


# --------------------------------------------------------------------------------------------
# Users anchor
# --------------------------------------------------------------------------------------------
users = load_supplied()["Users_1000_Clean"]
users["reg_utc"] = ist_naive_to_utc(users.registration_datetime)
users["ll_utc"] = ist_naive_to_utc(users.last_login_datetime)
users["sessions"] = users.lifetime_sessions.astype(int)
users["win_end"] = users.ll_utc.where(users.ll_utc <= PERIOD_END_UTC, PERIOD_END_UTC)
active = users[users.ll_utc.notna()].copy()
active = active[active.win_end > active.reg_utc].reset_index(drop=True)
active["weight"] = active.sessions + 1

# --------------------------------------------------------------------------------------------
# Sessions (helper, also published) and Feature Events (target 12,000)
# --------------------------------------------------------------------------------------------
session_rows = []
sid = 0
for u in active.itertuples():
    k = max(1, u.sessions)
    starts = sorted(rand_between(u.reg_utc, u.win_end, k - 1)) if k > 1 else []
    starts = list(starts) + [u.win_end]  # last session starts at last login
    for s in starts:
        sid += 1
        session_rows.append((f"VLSES{sid:07d}", u.user_id, s))
sessions = pd.DataFrame(session_rows, columns=["session_id", "user_id", "session_start_utc"])

# Interaction units: each unit becomes one or two ordered events.
UNITS = [
    (("feature_viewed",), 30),
    (("task_viewed",), 18),
    (("daily_reward_claimed", "streak_updated"), 9),
    (("spin_started", "spin_completed"), 6),
    (("spin_started",), 0.6),
    (("mission_started",), 3),
    (("mission_started", "mission_completed"), 2.5),
    (("badge_earned",), 1),
    (("help_article_viewed",), 4),
    (("support_ticket_created",), 0.6),
    (("user_logged_in",), 14),
]
FEATURE_OF = {
    "feature_viewed": None, "task_viewed": "tasks", "daily_reward_claimed": "daily_rewards",
    "streak_updated": "daily_rewards", "spin_started": "spin", "spin_completed": "spin",
    "mission_started": "missions", "mission_completed": "missions", "badge_earned": "badges",
    "help_article_viewed": "help_center", "support_ticket_created": "support",
    "user_logged_in": "account",
}
VIEW_FEATURES = ["home", "wallet", "tasks", "watch_ads", "tap_earn", "earning_session", "spin",
                 "missions", "referrals", "withdrawals", "leaderboard", "level_dashboard"]

unit_names = [u[0] for u in UNITS]
unit_p = np.array([u[1] for u in UNITS]) / sum(u[1] for u in UNITS)
sess_by_user = sessions.groupby("user_id")
user_weight = active.set_index("user_id").weight
events = []
daily_claimed = set()
target = 12000
while len(events) < target:
    uid = rng.choice(user_weight.index, p=user_weight / user_weight.sum())
    us = sess_by_user.get_group(uid)
    srow = us.iloc[rng.integers(len(us))]
    unit = unit_names[rng.choice(len(UNITS), p=unit_p)]
    t = srow.session_start_utc + pd.Timedelta(seconds=int(rng.integers(0, 1800)))
    t = min(t, PERIOD_END_UTC)
    if unit[0] == "daily_reward_claimed":
        day = t.tz_convert("Asia/Kolkata").date()
        if (uid, day) in daily_claimed:  # one claim per user per IST day
            continue
        daily_claimed.add((uid, day))
    for i, name in enumerate(unit):
        feat = FEATURE_OF[name] or rng.choice(VIEW_FEATURES)
        events.append((uid, srow.session_id, name, feat, t + pd.Timedelta(seconds=20 * i)))
events = events[:target]
fe = pd.DataFrame(events, columns=["user_id", "session_id", "event_name", "feature", "ts"])
fe["ts"] = fe.ts.where(fe.ts <= PERIOD_END_UTC, PERIOD_END_UTC)
fe = fe.sort_values("ts", kind="stable").reset_index(drop=True)
fe.insert(0, "event_id", [f"VLEVT{i:08d}" for i in range(1, len(fe) + 1)])
fe["platform"] = "web"
fe["event_timestamp_utc"] = iso(fe.ts)
# Spin pairs or a dangling spin_started may have been split by the 12,000 cut; that is acceptable
# (an interrupted spin is a real-world case, see help-center Spin the Wheel page).

# --------------------------------------------------------------------------------------------
# Task catalogue + Task Activity (target 6,000)
# --------------------------------------------------------------------------------------------
TASK_TYPES = [  # (task_type, feature, reward_unit, base_amount, third_party)
    ("watch_ad", "watch_ads", "VE", 5, True),
    ("survey", "surveys", "VE", 40, True),
    ("app_task", "app_tasks", "VE", 60, True),
    ("captcha", "captcha", "VE", 2, False),
    ("tap_earn", "tap_earn", "VE", 3, False),
    ("earning_session", "earning_session", "VE", 15, False),
    ("game", "games", "GEM", 4, False),
    ("social_follow", "follow_earn", "GEM", 6, True),
]
TYPE_WEIGHT = [38, 8, 5, 12, 14, 10, 8, 5]
tasks = []
for i in range(40):
    tt = TASK_TYPES[i % len(TASK_TYPES)]
    tasks.append((f"VLTSK{i + 1:04d}", tt[0], tt[1], tt[2], tt[3] * int(rng.integers(1, 4)),
                  "external_partner" if tt[4] else "veloop_internal"))
tasks = pd.DataFrame(tasks, columns=["task_id", "task_type", "feature", "reward_unit",
                                     "reward_amount", "fulfilment_source"])

n_ta = 6000
ta_users = rng.choice(user_weight.index, size=n_ta, p=user_weight / user_weight.sum())
ta_types = weighted_choice([t[0] for t in TASK_TYPES], TYPE_WEIGHT, n_ta)
rows = []
for i in range(n_ta):
    uid, ttype = ta_users[i], ta_types[i]
    cand = tasks[tasks.task_type == ttype]
    task = cand.iloc[rng.integers(len(cand))]
    us = sess_by_user.get_group(uid)
    srow = us.iloc[rng.integers(len(us))]
    start = min(srow.session_start_utc + pd.Timedelta(seconds=int(rng.integers(0, 1500))),
                PERIOD_END_UTC - pd.Timedelta(minutes=5))
    third = task.fulfilment_source == "external_partner"
    # Third-party tasks fail/pend more often: VELOOP does not control partner tracking (C4).
    p = [48, 11, 22, 10] if third else [60, 8, 24, 4]
    status = weighted_choice(["completed", "failed", "abandoned", "pending_validation"], p)
    dur = pd.Timedelta(seconds=int(rng.integers(15, 900)))
    completed_at, validation, failure, reward_amt = pd.NaT, "", "", ""
    if status == "completed":
        completed_at, validation, reward_amt = start + dur, "passed", task.reward_amount
    elif status == "pending_validation":
        completed_at, validation = start + dur, "pending"
    elif status == "failed":
        failure = weighted_choice(
            ["tracking_failed", "validation_failed", "task_failed", "system_error"],
            [4, 3, 2, 1] if third else [1, 3, 3, 2])
        validation = "failed" if failure == "validation_failed" else "not_reached"
    else:
        failure = "user_abandoned"
        validation = "not_reached"
    if pd.notna(completed_at) and completed_at > PERIOD_END_UTC:
        completed_at = PERIOD_END_UTC
    rows.append((uid, task.task_id, task.task_type, task.feature, srow.session_id, start,
                 completed_at, status, validation, failure, reward_amt,
                 task.reward_unit if reward_amt != "" or status == "pending_validation" else "",
                 "partner_network_sim" if third else "veloop"))
ta = pd.DataFrame(rows, columns=["user_id", "task_id", "task_type", "feature", "session_id",
                                 "started", "completed", "activity_status", "validation_status",
                                 "failure_category", "reward_amount", "reward_unit",
                                 "tracking_source"])
ta = ta.sort_values("started", kind="stable").reset_index(drop=True)
ta.insert(0, "activity_id", [f"VLACT{i:07d}" for i in range(1, n_ta + 1)])
# pending_validation keeps its expected amount in a separate column; the credited amount
# lives in Rewards. activity_status describes the activity, not the reward (C3).
ta["started_at_utc"] = iso(ta.started)
ta["completed_at_utc"] = iso(ta.completed)

# --------------------------------------------------------------------------------------------
# Referrals (target 900)
# --------------------------------------------------------------------------------------------
referred = users[users.acquisition_source == "Referral"].copy()
ref_rows = []
for u in referred.itertuples():
    possible = active[(active.reg_utc < u.reg_utc - pd.Timedelta(hours=1)) & (active.user_id != u.user_id)]
    if possible.empty:
        continue
    referrer = possible.iloc[rng.integers(len(possible))]
    created = rand_between(max(referrer.reg_utc, u.reg_utc - pd.Timedelta(days=10)), u.reg_utc - MIN)
    ref_rows.append((referrer.user_id, u.user_id, created, u.reg_utc, u.ll_utc))
n_unreg = 900 - len(ref_rows)
for _ in range(n_unreg):
    referrer = active.iloc[rng.choice(len(active), p=active.weight / active.weight.sum())]
    created = rand_between(referrer.reg_utc, referrer.win_end)
    ref_rows.append((referrer.user_id, "", created, pd.NaT, pd.NaT))
refs = pd.DataFrame(ref_rows, columns=["referrer_user_id", "referred_user_id", "created",
                                       "registered", "referred_last_login"])
refs = refs.sort_values("created", kind="stable").reset_index(drop=True)
refs.insert(0, "referral_id", [f"VLREF{i:06d}" for i in range(1, len(refs) + 1)])
completed_by_user = ta[ta.activity_status == "completed"].groupby("user_id").completed.min()
status, act_at, conv_at, rej_reason = [], [], [], []
for r in refs.itertuples():
    if r.referred_user_id == "":
        st = "expired" if r.created < PERIOD_END_UTC - pd.Timedelta(days=30) else "created"
        status.append(st); act_at.append(pd.NaT); conv_at.append(pd.NaT); rej_reason.append("")
        continue
    first_done = completed_by_user.get(r.referred_user_id, pd.NaT)
    if pd.isna(first_done):  # registered but never completed an eligible first activity
        status.append("registered"); act_at.append(pd.NaT); conv_at.append(pd.NaT); rej_reason.append("")
        continue
    if rng.random() < 0.08:
        status.append("rejected"); act_at.append(first_done); conv_at.append(pd.NaT)
        rej_reason.append(weighted_choice(["verification_failed", "policy_violation"], [2, 1]))
        continue
    conv = first_done + pd.Timedelta(hours=float(rng.uniform(1, 72)))
    if conv > PERIOD_END_UTC:
        status.append("activated"); act_at.append(first_done); conv_at.append(pd.NaT); rej_reason.append("")
    else:
        status.append("converted"); act_at.append(first_done); conv_at.append(conv); rej_reason.append("")
refs["referral_status"] = status
refs["activated"] = act_at
refs["converted"] = conv_at
refs["rejection_reason_category"] = rej_reason
refs["referral_channel"] = weighted_choice(["whatsapp", "telegram", "copy_link", "other"], [5, 2, 3, 1], len(refs))
code = users.set_index("user_id").referral_code
refs["referral_code"] = refs.referrer_user_id.map(code)
for col, src in [("created_at_utc", "created"), ("registered_at_utc", "registered"),
                 ("activated_at_utc", "activated"), ("converted_at_utc", "converted")]:
    refs[col] = iso(pd.to_datetime(refs[src], utc=True))

# --------------------------------------------------------------------------------------------
# Rewards (target ~5,000): one reward per rewardable source
# --------------------------------------------------------------------------------------------
rw = []
for r in ta[ta.activity_status.isin(["completed", "pending_validation"])].itertuples():
    amount = r.reward_amount if r.reward_amount != "" else int(tasks.set_index("task_id").reward_amount[r.task_id])
    rw.append((r.user_id, "task", r.activity_id, r.feature, int(amount), r.reward_unit,
               r.completed, r.activity_status == "pending_validation"))
SRC_REWARD = {"daily_reward_claimed": ("daily_reward", "daily_rewards", "VE", 5),
              "spin_completed": ("spin", "spin", "GEM", 3),
              "mission_completed": ("mission", "missions", "XP", 25),
              "badge_earned": ("badge", "badges", "XP", 50)}
for r in fe[fe.event_name.isin(SRC_REWARD)].itertuples():
    if r.event_name == "spin_completed" and rng.random() < 0.3:
        continue  # simulated "no prize" spin outcome: activity happened, no reward
    src, feat, unit, base = SRC_REWARD[r.event_name]
    rw.append((r.user_id, src, r.event_id, feat, base * int(rng.integers(1, 4)), unit,
               r.ts + pd.Timedelta(seconds=5), False))
for r in refs[refs.referral_status == "converted"].itertuples():
    rw.append((r.referrer_user_id, "referral", r.referral_id, "referrals", 100, "VE", r.converted, False))
rwd = pd.DataFrame(rw, columns=["user_id", "source_type", "source_id", "feature", "amount", "unit",
                                "created", "pending"])
rwd = rwd.sort_values("created", kind="stable").reset_index(drop=True)
rwd.insert(0, "reward_id", [f"VLRWD{i:07d}" for i in range(1, len(rwd) + 1)])
st, cred, rev, rev_reason, final_amt = [], [], [], [], []
for r in rwd.itertuples():
    if r.pending:
        st.append("pending"); cred.append(pd.NaT); rev.append(pd.NaT); rev_reason.append(""); final_amt.append(r.amount)
        continue
    c_at = r.created + pd.Timedelta(seconds=int(rng.integers(1, 900)))
    if c_at > PERIOD_END_UTC:  # credit would land after the period end: still pending at cut-off
        st.append("pending"); cred.append(pd.NaT); rev.append(pd.NaT); rev_reason.append(""); final_amt.append(r.amount)
        continue
    roll = rng.random()
    if roll < 0.05:
        r_at = c_at + pd.Timedelta(hours=float(rng.uniform(2, 240)))
        if r_at <= PERIOD_END_UTC:
            st.append("reversed"); cred.append(c_at); rev.append(r_at)
            rev_reason.append(weighted_choice(["invalid_activity", "tracking_dispute", "duplicate_credit",
                                               "technical_correction"], [4, 2, 1, 1]))
            final_amt.append(0)
            continue
    if roll > 0.98:
        st.append("corrected"); cred.append(c_at); rev.append(pd.NaT); rev_reason.append("technical_correction")
        final_amt.append(max(1, int(r.amount * 0.5)))
        continue
    st.append("credited"); cred.append(c_at); rev.append(pd.NaT); rev_reason.append(""); final_amt.append(r.amount)
rwd["reward_status"] = st
rwd["final_amount"] = final_amt
rwd["credited"] = cred
rwd["reversed"] = rev
rwd["reversal_reason_category"] = rev_reason
rwd["created_at_utc"] = iso(pd.to_datetime(rwd.created, utc=True))
rwd["credited_at_utc"] = iso(pd.to_datetime(rwd.credited, utc=True))
rwd["reversed_at_utc"] = iso(pd.to_datetime(rwd.reversed, utc=True))

# --------------------------------------------------------------------------------------------
# Wallet transactions + Withdrawals
# Wallet holds spendable units (VE, GEM). XP is progression only (Assumption A-012).
# --------------------------------------------------------------------------------------------
wt = []  # user, type, direction, amount, unit, status, ref_type, ref_id, related_idx, created, completed
for r in rwd[rwd.unit.isin(["VE", "GEM"]) & rwd.reward_status.isin(["credited", "reversed", "corrected"])].itertuples():
    wt.append([r.user_id, "reward_credit", "credit", r.amount, r.unit, "completed", "reward", r.reward_id, None,
               r.credited, r.credited])
    idx = len(wt) - 1
    if r.reward_status == "reversed":
        wt.append([r.user_id, "reversal", "debit", r.amount, r.unit, "completed", "reward", r.reward_id, idx,
                   r.reversed, r.reversed])
        wt[idx][5] = "reversed"
    elif r.reward_status == "corrected":
        adj = r.amount - r.final_amount
        t = r.credited + pd.Timedelta(hours=6)
        wt.append([r.user_id, "adjustment", "debit", adj, r.unit, "completed", "reward", r.reward_id, idx,
                   min(t, PERIOD_END_UTC), min(t, PERIOD_END_UTC)])

# Gems to VE exchanges (Gems Exchange Center exists per help center; rate is fictional here).
gem_users = rwd[(rwd.unit == "GEM") & (rwd.reward_status == "credited")].user_id.value_counts()
for uid in gem_users[gem_users >= 3].index[:120]:
    t = min(rwd[(rwd.user_id == uid) & (rwd.unit == "GEM")].credited.max() + pd.Timedelta(hours=2), PERIOD_END_UTC)
    wt.append([uid, "exchange_debit", "debit", 10, "GEM", "completed", "exchange", "", None, t, t])
    wt.append([uid, "exchange_credit", "credit", 20, "VE", "completed", "exchange", "", len(wt) - 1, t, t])

wallet = pd.DataFrame(wt, columns=["user_id", "transaction_type", "direction", "amount", "unit", "transaction_status",
                                   "reference_type", "reference_id", "related_idx", "created", "completed"])


def ve_balance(uid, at):
    w = wallet[(wallet.user_id == uid) & (wallet.unit == "VE") & (wallet.created <= at) & (wallet.transaction_status != "failed")]
    return w.loc[w.direction == "credit", "amount"].sum() - w.loc[w.direction == "debit", "amount"].sum()


# Withdrawals: target 1,200 requests. A request is only generated when the user's simulated
# VE balance covers it AT REQUEST TIME. A reward reversed after the VEs were already redeemed
# can still push a balance below zero later; this is kept on purpose because it is a real
# policy question for VELOOP (see assumption register A-020).
ve_earners = rwd[(rwd.unit == "VE") & (rwd.reward_status != "pending")].groupby("user_id").amount.sum()
ve_earners = ve_earners[ve_earners >= 10 * SIM_VE_PER_INR]
wd_rows, attempts = [], 0
spent = {}
while len(wd_rows) < 1200 and attempts < 40000:
    attempts += 1
    uid = rng.choice(ve_earners.index, p=ve_earners / ve_earners.sum())
    u = active[active.user_id == uid].iloc[0]
    if u.reg_utc + pd.Timedelta(days=1) >= PERIOD_END_UTC - pd.Timedelta(hours=1):
        continue  # registered too close to period end to request a withdrawal
    req = rand_between(u.reg_utc + pd.Timedelta(days=1), PERIOD_END_UTC - pd.Timedelta(hours=1))
    amount_inr = int(weighted_choice([10, 20, 50, 100], [5, 4, 2, 1]))
    need = amount_inr * SIM_VE_PER_INR
    if ve_balance(uid, req) - spent.get(uid, 0) < need:
        continue
    spent[uid] = spent.get(uid, 0) + need
    wd_rows.append((uid, req, amount_inr, need, weighted_choice(PAYOUT_METHODS, [6, 1, 2, 2])))
wd = pd.DataFrame(wd_rows, columns=["user_id", "requested", "amount_inr", "ve_debited", "payout_method"])
wd = wd.sort_values("requested", kind="stable").reset_index(drop=True)
wd.insert(0, "withdrawal_id", [f"VLWDR{i:06d}" for i in range(1, len(wd) + 1)])
proc, final, status, reason = [], [], [], []
for r in wd.itertuples():
    # Processing duration: mostly under 24h, a tail beyond the published 72h window.
    dur_h = float(weighted_choice([rng.uniform(1, 24), rng.uniform(24, 72), rng.uniform(72, 168)], [70, 22, 8]))
    f_at = r.requested + pd.Timedelta(hours=dur_h)
    # Review starts after the request and before the final decision.
    p_at = r.requested + pd.Timedelta(hours=dur_h * float(rng.uniform(0.05, 0.6)))
    outcome = weighted_choice(["completed", "rejected", "reversed"], [86, 10, 4])
    if p_at > PERIOD_END_UTC:
        proc.append(pd.NaT); final.append(pd.NaT); status.append("requested"); reason.append(""); continue
    if f_at > PERIOD_END_UTC:
        proc.append(p_at); final.append(pd.NaT); status.append("processing"); reason.append(""); continue
    if outcome == "reversed":
        rev_at = f_at + pd.Timedelta(hours=float(rng.uniform(1, 48)))
        if rev_at > PERIOD_END_UTC:
            outcome = "completed"  # reversal would fall after the period: stays completed
        else:
            f_at = rev_at
    proc.append(p_at); final.append(f_at); status.append(outcome)
    reason.append("" if outcome == "completed" else weighted_choice(
        ["verification_failed", "payout_details_invalid", "policy_violation", "payout_partner_failure"],
        [3, 3, 2, 2] if outcome == "rejected" else [0, 1, 2, 4]))
wd["processing"] = proc
wd["final"] = final
wd["withdrawal_status"] = status
wd["reason_category"] = reason
wd["requested_at_utc"] = iso(wd.requested)
wd["processing_at_utc"] = iso(pd.to_datetime(wd.processing, utc=True))
wd["final_at_utc"] = iso(pd.to_datetime(wd.final, utc=True))

# Redemption debit for every request; refund credit when rejected or reversed.
for r in wd.itertuples():
    debit_status = {"completed": "completed", "requested": "pending", "processing": "pending",
                    "rejected": "reversed", "reversed": "reversed"}[r.withdrawal_status]
    wt.append([r.user_id, "redemption_debit", "debit", r.ve_debited, "VE", debit_status, "withdrawal",
               r.withdrawal_id, None, r.requested, r.final if debit_status == "completed" else pd.NaT])
    if r.withdrawal_status in ("rejected", "reversed"):
        wt.append([r.user_id, "redemption_refund", "credit", r.ve_debited, "VE", "completed", "withdrawal",
                   r.withdrawal_id, len(wt) - 1, r.final, r.final])
wallet = pd.DataFrame(wt, columns=["user_id", "transaction_type", "direction", "amount", "unit", "transaction_status",
                                   "reference_type", "reference_id", "related_idx", "created", "completed"])
order = wallet.created.argsort(kind="stable")
new_id = {old: f"VLTXN{new + 1:07d}" for new, old in enumerate(order)}
wallet["transaction_id"] = [new_id[i] for i in range(len(wallet))]
wallet["related_transaction_id"] = wallet.related_idx.map(lambda i: new_id[int(i)] if pd.notna(i) else "")
wallet = wallet.iloc[order].reset_index(drop=True)
wallet["created_at_utc"] = iso(pd.to_datetime(wallet.created, utc=True))
wallet["completed_at_utc"] = iso(pd.to_datetime(wallet.completed, utc=True))
debit_of = wallet[wallet.transaction_type == "redemption_debit"].set_index("reference_id").transaction_id
wd["debit_transaction_id"] = wd.withdrawal_id.map(debit_of)
wallet_of_reward = wallet[wallet.transaction_type == "reward_credit"].set_index("reference_id").transaction_id
rwd["wallet_transaction_id"] = rwd.reward_id.map(wallet_of_reward).fillna("")
rwd["amount"] = rwd.amount.astype(int)

# --------------------------------------------------------------------------------------------
# Final column selection
# --------------------------------------------------------------------------------------------
OUT = {
    "Tasks": tasks,
    "Sessions": sessions.assign(session_start_utc=iso(sessions.session_start_utc)),
    "Task_Activity": ta[["activity_id", "user_id", "task_id", "task_type", "feature", "session_id",
                         "started_at_utc", "completed_at_utc", "activity_status", "validation_status",
                         "failure_category", "reward_amount", "reward_unit", "tracking_source"]],
    "Rewards": rwd[["reward_id", "user_id", "source_type", "source_id", "feature", "amount", "final_amount",
                    "unit", "reward_status", "created_at_utc", "credited_at_utc", "reversed_at_utc",
                    "reversal_reason_category", "wallet_transaction_id"]],
    "Wallet": wallet[["transaction_id", "user_id", "transaction_type", "direction", "amount", "unit", "transaction_status",
                      "reference_type", "reference_id", "related_transaction_id", "created_at_utc",
                      "completed_at_utc"]],
    "Withdrawals": wd[["withdrawal_id", "user_id", "amount_inr", "ve_debited", "payout_method",
                       "withdrawal_status", "requested_at_utc", "processing_at_utc", "final_at_utc",
                       "reason_category", "debit_transaction_id"]],
    "Referrals": refs[["referral_id", "referrer_user_id", "referred_user_id", "referral_code",
                       "referral_channel", "referral_status", "created_at_utc", "registered_at_utc",
                       "activated_at_utc", "converted_at_utc", "rejection_reason_category"]],
    "Feature_Events": fe[["event_id", "user_id", "session_id", "event_name", "feature", "platform",
                          "event_timestamp_utc"]],
}
for name in OUT:
    OUT[name] = OUT[name].copy()
    OUT[name]["data_environment"] = SIM_LABEL

# --------------------------------------------------------------------------------------------
# Messy_Data: a lifecycle event log sampled from the clean tables, then corrupted on purpose.
# Each injected defect hits a distinct row so detected counts can be compared exactly.
# --------------------------------------------------------------------------------------------
log_rows = []
sample_wd = OUT["Withdrawals"][OUT["Withdrawals"].withdrawal_status.isin(["completed", "rejected"])].sample(90, random_state=SEED)
for r in sample_wd.itertuples():
    log_rows.append(("withdrawals", r.user_id, r.withdrawal_id, "withdrawal_requested", "requested", r.requested_at_utc, r.amount_inr, "INR", r.payout_method))
    log_rows.append(("withdrawals", r.user_id, r.withdrawal_id, "withdrawal_processing", "processing", r.processing_at_utc, r.amount_inr, "INR", r.payout_method))
    log_rows.append(("withdrawals", r.user_id, r.withdrawal_id, f"withdrawal_{r.withdrawal_status}", r.withdrawal_status, r.final_at_utc, r.amount_inr, "INR", r.payout_method))
sample_ta = OUT["Task_Activity"][OUT["Task_Activity"].activity_status == "completed"].sample(120, random_state=SEED)
for r in sample_ta.itertuples():
    log_rows.append(("task_activity", r.user_id, r.activity_id, "task_started", "started", r.started_at_utc, "", "", ""))
    log_rows.append(("task_activity", r.user_id, r.activity_id, "task_completed", "completed", r.completed_at_utc, r.reward_amount, r.reward_unit, ""))
messy = pd.DataFrame(log_rows, columns=["source_table", "user_id", "reference_id", "event_name", "status",
                                        "event_timestamp_utc", "amount", "unit", "payout_method"])
messy["amount"] = messy.amount.astype(str)
messy.insert(0, "record_id", [f"VLMSY{i:05d}" for i in range(1, len(messy) + 1)])

injections = []
pool = list(rng.permutation(len(messy)))


def take(n, pred=None):
    out = []
    for i in list(pool):
        if pred is None or pred(messy.loc[i]):
            out.append(i); pool.remove(i)
            if len(out) == n:
                break
    assert len(out) == n, "not enough rows to inject"
    return out


def inject(kind, field, idx, new_values):
    for i, v in zip(idx, new_values):
        injections.append((messy.at[i, "record_id"], kind, field, messy.at[i, field], v))
        messy.at[i, field] = v


is_wd = lambda r: r.source_table == "withdrawals"
is_task = lambda r: r.source_table == "task_activity"
ix = take(6); inject("missing_id", "user_id", ix, [""] * 6)
ix = take(5); inject("missing_timestamp", "event_timestamp_utc", ix, [""] * 5)
ix = take(8); inject("malformed_date", "event_timestamp_utc", ix,
                     ["2026-13-05T10:00:00Z", "15/07/2026 10:22", "2026-06-31T08:00:00Z", "N/A",
                      "July 3 2026", "2026-08-12 25:10:00", "20260704", "2026-07-0T11:00:00Z"])
ix = take(7); inject("invalid_status", "status", ix, ["done", "approved", "succeeded", "unknown", "paid", "ok", "in-review"])
ix = take(9); inject("inconsistent_capitalization", "status", ix,
                     [messy.at[i, "status"].upper() if k % 2 else messy.at[i, "status"].title() for k, i in enumerate(ix)])
ix = take(6); inject("trailing_spaces", "event_name", ix, [messy.at[i, "event_name"] + " " for i in ix])
ix = take(6, lambda r: r.amount != ""); inject("invalid_numeric", "amount", ix, ["ten", "1O0", "50 INR", "#VALUE!", "NaN", "--"])
ix = take(5, lambda r: r.amount != ""); inject("negative_value", "amount", ix, [f"-{messy.at[i, 'amount']}" for i in ix])
ix = take(4, lambda r: r.source_table == "withdrawals"); inject("unexpected_null", "payout_method", ix, [""] * 4)
ix = take(6); inject("orphan_record", "user_id", ix, [f"VLUSR9{900 + k:05d}" for k in range(6)])
ix = take(6); inject("inconsistent_naming", "event_name", ix,
                     [{"withdrawal_requested": "WithdrawalRequested", "withdrawal_processing": "withdrawal-processing",
                       "withdrawal_completed": "withdrawalCompleted", "withdrawal_rejected": "Withdrawal Rejected",
                       "task_started": "TaskStarted", "task_completed": "task-complete"}[messy.at[i, "event_name"]] for i in ix])

# Impossible transitions: completed/rejected final step timestamped before the request, on
# withdrawals whose rows are otherwise untouched.
touched = {r[0] for r in injections}
clean_wd_ids = [w for w, g in messy[messy.source_table == "withdrawals"].groupby("reference_id")
                if not set(g.record_id) & touched and len(g) == 3]
for w in clean_wd_ids[:5]:
    g = messy[messy.reference_id == w]
    req_i = g.index[g.event_name == "withdrawal_requested"][0]
    fin_i = g.index[~g.event_name.isin(["withdrawal_requested", "withdrawal_processing"])][0]
    new_t = (pd.Timestamp(messy.at[req_i, "event_timestamp_utc"]) - pd.Timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    inject("impossible_state_transition", "event_timestamp_utc", [fin_i], [new_t])
    pool.remove(fin_i) if fin_i in pool else None

# Duplicate IDs: copy a record_id onto another (different) row.
ix = take(5); src = take(5)
inject("duplicate_id", "record_id", ix, [messy.at[s, "record_id"] for s in src])
# Duplicate events: exact copies of 12 untouched rows appended with fresh record ids.
dup_src = take(12)
dups = messy.loc[dup_src].copy()
dups["record_id"] = [f"VLMSY{len(messy) + k + 1:05d}" for k in range(len(dups))]
for d, s in zip(dups.record_id, dup_src):
    injections.append((d, "duplicate_event", "row", messy.at[s, "record_id"], "exact duplicate of event"))
messy = pd.concat([messy, dups], ignore_index=True)
messy["data_environment"] = SIM_LABEL
OUT["Messy_Data"] = messy
inj = pd.DataFrame(injections, columns=["record_id", "injected_issue", "field", "original_value", "injected_value"])
inj["data_environment"] = SIM_LABEL

SIM_DIR.mkdir(parents=True, exist_ok=True)
for name, df in OUT.items():
    df.to_csv(SIM_DIR / f"{name}.csv", index=False)
inj.to_csv(SIM_DIR / "messy_injection_log.csv", index=False)
for name, df in OUT.items():
    print(f"{name:16s} {len(df):6d} rows")
print("injected defects", len(inj), inj.injected_issue.value_counts().to_dict())

# --------------------------------------------------------------------------------------------
# Methodology document (section 28 requirement)
# --------------------------------------------------------------------------------------------
lines = [f"# Generation methodology: companion simulated datasets", "",
         f"**Label on every row:** `{SIM_LABEL}`", "",
         "These datasets are fictional. They were created by the analyst because the supplied workbook contained only Users data. "
         "They are not VELOOP users, earnings, withdrawals, revenue, retention, conversion or performance, and must never be mixed with production data.", "",
         "## Method", "", __doc__.split("Methodology (also written to data/simulated/GENERATION_METHODOLOGY.md):")[1].strip(), "",
         "## Parameters", "",
         f"* Seed: `{SEED}`; script: `scripts/generate_companion_data.py`; anchor: supplied `Users_1000_Clean` (user_id, registration_datetime, last_login_datetime, lifetime_sessions, acquisition_source).",
         "* Supplied naive timestamps treated as IST (assumption A-004) and converted to UTC; all generated timestamps are ISO 8601 UTC and fall within 01 Apr to 15 Sep 2026 IST.",
         f"* Fictional VE-to-INR factor `{SIM_VE_PER_INR}` used only so simulated withdrawals and ledger debits agree. It is NOT VELOOP's rate (A-010).",
         "* Payout methods use the four methods published on the official withdrawal page; partner names are generic placeholders (`partner_network_sim`).",
         "* Task outcomes: third-party tasks have higher failure and pending shares than internal tasks, to reflect partner dependency (C4).",
         "* Rewards: one per rewardable source; about 5% of credits reversed and about 2% corrected; 30% of spins produce no prize; credits after the period end stay pending.",
         "* Withdrawals: requested only when the simulated VE balance covers the request; processing time mostly under 24 h with a tail beyond 72 h; outcomes include rejection and reversal with refund rows.",
         "* Referrals: the supplied users with acquisition_source = Referral are linked to a plausible earlier-registered referrer; the rest of the 900 are invites never registered (created/expired).", "",
         "## Row counts", "", "| Dataset | Rows |", "| --- | --- |"] + [f"| {k} | {len(v):,} |" for k, v in OUT.items()] + [
         "", "## Defects injected into Messy_Data (ground truth for the audit)", "", "| Injected issue | Rows |", "| --- | --- |"] + [
         f"| {k} | {v} |" for k, v in inj.injected_issue.value_counts().sort_index().items()] + [
         "", "Full row-level log: `messy_injection_log.csv`. Clean tables contain no injected defects."]
(SIM_DIR / "GENERATION_METHODOLOGY.md").write_text("\n".join(lines) + "\n")
