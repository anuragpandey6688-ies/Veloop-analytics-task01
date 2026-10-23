# 06 · Wallet & Withdrawal Analytics Specification

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

Official facts used (SRC-05): minimum withdrawal Rs. 10; methods UPI, PayPal, Amazon Gift Cards, Google Play Gift Cards; usually processed within 24 h, up to 72 h in review cases. VE-to-INR conversion is **not published** (A-010), so INR and VE values are stored separately and never converted by the analyst.

## D1 Wallet transaction model

The wallet is an **append-only ledger**: one row per balance movement, never updated in place. Supported transaction types: `reward_credit`, `reversal`, `adjustment`, `redemption_debit`, `redemption_refund`. `exchange_debit` and `exchange_credit` are **Proposed**: the Gems Exchange exists (SRC-16), but how it is recorded is unknown. The direction (credit/debit) carries the sign and `amount` is always positive.

| field_name | data_type | required | allowed_values | validation | definition |
| --- | --- | --- | --- | --- | --- |
| transaction_id | string | Yes |  | Non-null; immutable; unique within entity | Identifier of one ledger movement. Never reused. |
| user_id | string | Yes |  | Must exist in users | Wallet owner. |
| transaction_type | enum | Yes | reward_credit, reversal, adjustment, exchange_debit, exchange_credit, redemption_debit, redemption_refund | Must be in allowed list; exchange types Proposed | Business type of the movement. |
| direction | enum | Yes | credit, debit | Must agree with transaction_type | Whether the balance goes up (credit) or down (debit). |
| amount | integer | Yes |  | > 0 | Absolute amount moved. Sign is carried by direction. |
| unit | enum | Yes | VE, GEM, TOKEN, SPIN | Must be in allowed list | Wallet unit moved. |
| transaction_status | enum | Yes | pending, completed, failed, reversed | pending->completed\|failed; completed->reversed | Current state of the movement. |
| reference_type | enum | Yes | reward, withdrawal, exchange, manual_adjustment | Must be in allowed list | Kind of business record that caused the movement. |
| reference_id | string | Conditional |  | Must resolve in the table implied by reference_type | Identifier of the causing record (reward_id, withdrawal_id...). |
| related_transaction_id | string | Conditional |  | Required for reversal, adjustment, refund, exchange_credit; must exist | Original transaction that this one reverses, corrects or pairs with. |
| created_at_utc | timestamp | Yes |  | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | When the movement was recorded. |
| completed_at_utc | timestamp | Conditional |  | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= created_at_utc | When the movement became final. |
| balance_after | integer | No |  | >= 0 unless a documented correction | Balance of this unit after the movement. |
| idempotency_key | string | Yes |  | Unique | Key that prevents the same business action creating two ledger rows. |

Reversal/correction relationship: every `reversal`, `adjustment`, `redemption_refund` and `exchange_credit` row must carry `related_transaction_id` pointing to the original row (QC-13). An unlinked correction is a data-quality defect.

## D2 Withdrawal lifecycle

```
withdrawal_requested ──► withdrawal_processing ──► withdrawal_completed ──► (withdrawal_reversed)
                                   │
                                   └──► withdrawal_rejected
```

* On **request**, a `redemption_debit` (pending) is created, so VEs cannot be spent twice.
* On **completion**, the debit becomes completed.
* On **rejection or reversal**, a `redemption_refund` credit is created and linked to the debit.
* Every transition is written to `withdrawal_status_history`. A transition that is not drawn above is rejected (QC-09).

| entity | field_name | data_type | required | allowed_values | definition |
| --- | --- | --- | --- | --- | --- |
| withdrawals | withdrawal_id | string | Yes |  | Identifier of one withdrawal/redemption request. |
| withdrawals | user_id | string | Yes |  | Requesting user. |
| withdrawals | amount_inr | decimal | Yes |  | Requested payout value in Indian rupees. |
| withdrawals | ve_debited | integer | Yes |  | VEs debited from the wallet for the request. |
| withdrawals | payout_method | enum | Yes | UPI, PayPal, Amazon Gift Card, Google Play Gift Card | Requested payout method. |
| withdrawals | withdrawal_status | enum | Yes | requested, processing, completed, rejected, reversed | Current lifecycle state. |
| withdrawals | requested_at_utc | timestamp | Yes |  | When the user submitted the request. |
| withdrawals | processing_at_utc | timestamp | Conditional |  | When review/processing started. |
| withdrawals | final_at_utc | timestamp | Conditional |  | When the request reached completed, rejected or reversed. |
| withdrawals | reason_category | enum | Conditional | verification_failed, payout_details_invalid, policy_violation, payout_partner_failure | Reason category for rejection or reversal. |
| withdrawals | review_type | enum | No | system, manual | Whether the request went through system-only or manual review. |
| withdrawals | debit_transaction_id | string | Yes |  | Wallet redemption_debit created for this request. |
| withdrawals | payout_reference_id | string | Conditional |  | Payout partner's reference for the transfer. Never a UPI ID, account number or card number. |
| withdrawal_status_history | status_history_id | string | Yes |  | Identifier of one withdrawal status transition. |
| withdrawal_status_history | withdrawal_id | string | Yes |  | Withdrawal that changed status. |
| withdrawal_status_history | from_status | enum | Conditional | requested, processing, completed, rejected, reversed | Status before the transition (blank for creation). |
| withdrawal_status_history | to_status | enum | Yes | requested, processing, completed, rejected, reversed | Status after the transition. |
| withdrawal_status_history | changed_at_utc | timestamp | Yes |  | When the transition happened. |

## D3 Withdrawal KPIs

| kpi_id | name | definition | formula | required | data_source | frequency | stakeholder | business_purpose | limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K-WDR-01 | Withdrawal Requests | Count and INR value of withdrawal requests submitted. | COUNT(withdrawal_id), SUM(amount_inr) WHERE requested_at_utc in period | withdrawals.withdrawal_id, withdrawals.requested_at_utc, withdrawals.amount_inr | withdrawals | Daily | Finance, Operations | Payout demand. | Requests later rejected are included. |
| K-WDR-02 | Completed Withdrawals | Count and INR value reaching 'completed' in the period. | COUNT(*), SUM(amount_inr) WHERE withdrawal_status = 'completed' AND final_at_utc in period | withdrawals.withdrawal_status, withdrawals.final_at_utc, withdrawals.amount_inr | withdrawals | Daily | Finance, Founder | Payout delivered. | Partner-side failures after completion need payout_reference_id reconciliation. |
| K-WDR-03 | Pending Withdrawal Queue | Count, INR value and age of requests in 'requested' or 'processing' at snapshot time. | COUNT(*), SUM(amount_inr), MAX(now - requested_at_utc) WHERE status in ('requested','processing') | withdrawals.withdrawal_status, withdrawals.requested_at_utc, withdrawals.amount_inr | withdrawals | Hourly / Daily | Operations | Operational load and user waiting time. | Snapshot; requires status history for trends. |
| K-WDR-04 | Rejected Withdrawals and Rejection Rate | Count of rejected requests and share of resolved requests that were rejected, by reason_category. | COUNT(rejected) / COUNT(rejected + completed + reversed) for requests resolved in period | withdrawals.withdrawal_status, withdrawals.reason_category | withdrawals | Weekly | Operations, Trust & Safety | Payout friction and abuse handling. | Reason taxonomy is proposed (A-015). |
| K-WDR-05 | Reversed Withdrawals | Count and INR value of withdrawals reversed after completion. | COUNT(*), SUM(amount_inr) WHERE withdrawal_status = 'reversed' | withdrawals.withdrawal_status, withdrawals.amount_inr, withdrawals.reason_category | withdrawals | Weekly | Finance | Payout failures after completion. | Reversal can occur after reporting period closes. |
| K-WDR-06 | Withdrawal Processing Time | Median and P90 hours from request to final status, for resolved requests. | PERCENTILE(final_at_utc - requested_at_utc, 0.5 / 0.9) | withdrawals.requested_at_utc, withdrawals.final_at_utc | withdrawals | Daily | Operations, Founder | Payout speed vs published expectation (24 h, up to 72 h). | Excludes open requests; pair with K-WDR-03. |
| K-WDR-07 | Withdrawal Completion Rate | Share of resolved requests (requested in the cohort) that completed and were not reversed. | COUNT(completed) / COUNT(completed + rejected + reversed) | withdrawals.withdrawal_status, withdrawals.requested_at_utc | withdrawals | Weekly | Founder, Finance | Payout reliability. | Open requests excluded; recent cohorts immature. |
| K-WDR-08 | Withdrawal Volume (INR) | Sum of amount_inr by status for the period. | SUM(amount_inr) GROUP BY withdrawal_status | withdrawals.amount_inr, withdrawals.withdrawal_status | withdrawals | Daily | Finance | Cash liability and payout spend. | INR only; VE liability needs a confirmed conversion rate. |
| K-WDR-09 | Payout Method Distribution | Share of requests and completed volume by payout_method. | COUNT(*) GROUP BY payout_method / COUNT(*) | withdrawals.payout_method, withdrawals.withdrawal_status | withdrawals | Weekly | Operations, Finance | Partner capacity planning. | Method availability varies by user eligibility (official). |
| K-WDR-10 | Share Resolved Within 72 Hours | Share of resolved requests whose processing time was 72 hours or less. | COUNT(final_at_utc - requested_at_utc <= 72h) / COUNT(resolved) | withdrawals.requested_at_utc, withdrawals.final_at_utc | withdrawals | Daily | Operations, Founder | Checks delivery against the publicly stated processing window. This is a published policy reference, not an internal target. | Policy window may change; read from config, not hard-coded. |

Wallet KPIs: K-WAL-01 Wallet Transactions, K-WAL-02 Credit Volume, K-WAL-03 Redemption Activity, K-WAL-04 Wallet Reversals and Refunds, K-WAL-05 Ledger Reconciliation Exceptions. Full definitions are in 11.

## Open policy question found by simulation

In the simulated ledger, **5 users end with a negative VE balance**. This happens when a reward is reversed after its VEs were already withdrawn. VELOOP's pages describe reversal and forfeiture but not this case. Analytics needs the rule (allow negative balance, recover from future earnings, or write off) before reversal and liability KPIs can be interpreted (A-020).
