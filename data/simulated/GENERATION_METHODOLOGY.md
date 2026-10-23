# Generation methodology: companion simulated datasets

**Label on every row:** `SIMULATED DATA — CREATED FOR ANALYTICAL TESTING`

These datasets are fictional. They were created by the analyst because the supplied workbook contained only Users data. They are not VELOOP users, earnings, withdrawals, revenue, retention, conversion or performance, and must never be mixed with production data.

## Method

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

## Parameters

* Seed: `20260915`; script: `scripts/generate_companion_data.py`; anchor: supplied `Users_1000_Clean` (user_id, registration_datetime, last_login_datetime, lifetime_sessions, acquisition_source).
* Supplied naive timestamps treated as IST (assumption A-004) and converted to UTC; all generated timestamps are ISO 8601 UTC and fall within 01 Apr to 15 Sep 2026 IST.
* Fictional VE-to-INR factor `2` used only so simulated withdrawals and ledger debits agree. It is NOT VELOOP's rate (A-010).
* Payout methods use the four methods published on the official withdrawal page; partner names are generic placeholders (`partner_network_sim`).
* Task outcomes: third-party tasks have higher failure and pending shares than internal tasks, to reflect partner dependency (C4).
* Rewards: one per rewardable source; about 5% of credits reversed and about 2% corrected; 30% of spins produce no prize; credits after the period end stay pending.
* Withdrawals: requested only when the simulated VE balance covers the request; processing time mostly under 24 h with a tail beyond 72 h; outcomes include rejection and reversal with refund rows.
* Referrals: the supplied users with acquisition_source = Referral are linked to a plausible earlier-registered referrer; the rest of the 900 are invites never registered (created/expired).

## Row counts

| Dataset | Rows |
| --- | --- |
| Tasks | 40 |
| Sessions | 11,649 |
| Task_Activity | 6,000 |
| Rewards | 5,651 |
| Wallet | 6,656 |
| Withdrawals | 1,200 |
| Referrals | 900 |
| Feature_Events | 12,000 |
| Messy_Data | 522 |

## Defects injected into Messy_Data (ground truth for the audit)

| Injected issue | Rows |
| --- | --- |
| duplicate_event | 12 |
| duplicate_id | 5 |
| impossible_state_transition | 5 |
| inconsistent_capitalization | 9 |
| inconsistent_naming | 6 |
| invalid_numeric | 6 |
| invalid_status | 7 |
| malformed_date | 8 |
| missing_id | 6 |
| missing_timestamp | 5 |
| negative_value | 5 |
| orphan_record | 6 |
| trailing_spaces | 6 |
| unexpected_null | 4 |

Full row-level log: `messy_injection_log.csv`. Clean tables contain no injected defects.
