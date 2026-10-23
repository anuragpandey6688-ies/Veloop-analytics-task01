# 05 · Earning & Reward Analytics Specification

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

## Lifecycle and how each stage is measured

| Stage | Measured by | Owner of the truth | KPI |
| --- | --- | --- | --- |
| Discovery | `task_viewed`, `task_opened` (client) | Frontend | Funnel, K-ENG-01 |
| Start | `task_started` (server, creates `activity_id`) | Backend | K-ENG-02 |
| Completion | `task_submitted` (client, user finished) | Frontend / partner | K-RWD-06 |
| Validation | `task_completed` (validation passed) or `task_failed` (validation_failed / tracking_failed / ...) | Backend after partner callback | K-ENG-03, K-ENG-04, K-ENG-06 |
| Reward | `reward_pending` → `reward_credited` / `reward_rejected`; later `reward_reversed` / `reward_corrected` | Reward service | K-RWD-01..06 |

## C1 Task-level analytics

| entity | field_name | data_type | required | allowed_values | definition |
| --- | --- | --- | --- | --- | --- |
| tasks | task_id | string | Yes |  | Identifier of one configured task/offer. |
| tasks | task_type | enum | Yes | watch_ad, survey, app_task, captcha, tap_earn, earning_session, game, social_follow | Kind of task. |
| tasks | feature | enum | Yes | watch_ads, surveys, app_tasks, captcha, tap_earn, earning_session, games, follow_earn, tasks, daily_rewards, spin, missions, badges, level_dashboard, leaderboard, promo_codes, wallet, exchange, withdrawals, referrals, account, onboarding, home, help_center, support | Feature the task is shown in. |
| tasks | fulfilment_source | enum | Yes | veloop_internal, external_partner | Whether completion is decided by VELOOP or by an external partner (ads, surveys, offers). |
| tasks | provider_id | string | Conditional |  | Pseudonymous identifier of the external partner. |
| tasks | reward_unit | enum | Yes | VE, GEM, XP, TOKEN, SPIN | Unit the task pays in. |
| tasks | reward_amount | integer | Yes |  | Configured reward amount for one valid completion. |
| tasks | task_config_status | enum | Yes | active, paused, retired | Whether the task is currently offered. |
| task_activity | activity_id | string | Yes |  | Identifier of one user's attempt at one task, created when the task is started. |
| task_activity | user_id | string | Yes |  | User attempting the task. |
| task_activity | task_id | string | Yes |  | Task attempted. |
| task_activity | task_type | enum | Yes | watch_ad, survey, app_task, captcha, tap_earn, earning_session, game, social_follow | Copied from tasks at start time so history survives config changes. |
| task_activity | feature | enum | Yes | watch_ads, surveys, app_tasks, captcha, tap_earn, earning_session, games, follow_earn, tasks, daily_rewards, spin, missions, badges, level_dashboard, leaderboard, promo_codes, wallet, exchange, withdrawals, referrals, account, onboarding, home, help_center, support | Feature where the task was started. |
| task_activity | session_id | string | No |  | Session in which the task was started. |
| task_activity | started_at_utc | timestamp | Yes |  | When the user started the task. |
| task_activity | completed_at_utc | timestamp | Conditional |  | When the user finished the task action (before validation). |
| task_activity | validated_at_utc | timestamp | Conditional |  | When validation reached a final result. |
| task_activity | activity_status | enum | Yes | in_progress, pending_validation, completed, failed, abandoned | Lifecycle status of the attempt. Describes the activity, not whether a reward was credited. |
| task_activity | validation_status | enum | Yes | pending, passed, failed, not_reached | Result of completion validation. |
| task_activity | failure_category | enum | Conditional | task_failed, tracking_failed, validation_failed, user_abandoned, system_error | Proposed failure classification. Not an internal error code. |
| task_activity | tracking_source | string | Yes |  | Who reported the completion: 'veloop' or a registered partner code. |
| task_activity | external_reference_id | string | Conditional |  | Partner's own transaction reference for the completion (postback ID). |
| task_activity | reward_amount | integer | Conditional |  | Expected reward amount for the attempt at the time of start. |
| task_activity | reward_unit | enum | Conditional | VE, GEM, XP, TOKEN, SPIN | Unit of reward_amount. |

## C2 Failed activity: proposed classification

VELOOP's internal failure codes are unknown, so **none are invented**. Instead, a structured classification is proposed (status: Proposed, A-015):

| failure_category | Meaning | Typical failure_stage | Who controls it |
| --- | --- | --- | --- |
| task_failed | User did not meet task conditions | in_task | User / task design |
| tracking_failed | Partner never confirmed, or confirmation was lost | tracking | External partner |
| validation_failed | Completion reported but rejected by validation | validation | VELOOP rules |
| user_abandoned | Started, no completion within timeout (derived, A-013) | in_task | User |
| system_error | VELOOP-side error | any | VELOOP engineering |

## C3 Reward events: activity is not reward

`task_activity.activity_status = completed` means the activity happened and passed validation. It does **not** mean money moved. Only `rewards.reward_status in (credited, corrected)` with `credited_at_utc` means a reward was actually credited. Allowed reward transitions: `pending → credited | rejected`, then `credited → reversed | corrected`.

| field_name | data_type | required | allowed_values | definition |
| --- | --- | --- | --- | --- |
| reward_id | string | Yes |  | Identifier of one reward decision (pending, credited, reversed, corrected). |
| user_id | string | Yes |  | User receiving the reward. |
| source_type | enum | Yes | task, daily_reward, streak, spin, mission, badge, referral, promo_code, leaderboard, manual_adjustment | What generated the reward. |
| source_id | string | Yes |  | Identifier of the generating record (activity_id, event_id, referral_id...). |
| feature | enum | Yes | watch_ads, surveys, app_tasks, captcha, tap_earn, earning_session, games, follow_earn, tasks, daily_rewards, spin, missions, badges, level_dashboard, leaderboard, promo_codes, wallet, exchange, withdrawals, referrals, account, onboarding, home, help_center, support | Feature credited for the reward. |
| amount | integer | Yes |  | Amount originally granted or expected. |
| final_amount | integer | Yes |  | Amount that stands after corrections or reversal (0 if reversed). |
| unit | enum | Yes | VE, GEM, XP, TOKEN, SPIN | Unit of the reward. |
| reward_status | enum | Yes | pending, credited, rejected, reversed, corrected | Current reward state. Distinguishes 'activity occurred' from 'reward actually credited'. |
| created_at_utc | timestamp | Yes |  | When the reward record was created. |
| credited_at_utc | timestamp | Conditional |  | When the reward was credited to the user. |
| reversed_at_utc | timestamp | Conditional |  | When a credited reward was reversed. |
| reversal_reason_category | enum | Conditional | invalid_activity, tracking_dispute, duplicate_credit, technical_correction, policy_violation | Reason category for reversal or correction. Not a fraud threshold. |
| wallet_transaction_id | string | Conditional |  | Wallet transaction created by crediting this reward (spendable units only). |
| idempotency_key | string | Yes |  | Key that guarantees one reward per source event even if the request is retried. |

## C4 Third-party dependency

Ads, surveys, offers and some social tasks are confirmed by **external partners** (SRC-07: tracking can take about 15 minutes, and third-party failures may prevent credit). The design reflects that VELOOP does not control these outcomes:

* `tasks.fulfilment_source` and `provider_id` separate partner-confirmed tasks from VELOOP-internal ones. Every completion and failure KPI can be split by partner.
* `task_activity.external_reference_id` stores the partner's own reference, so VELOOP records can be reconciled with partner reports and partner retries deduplicated.
* `tracking_failed` is a separate category, so a partner outage is not reported as user failure or VELOOP failure.
* Completion KPIs use a **maturity window** (for example 3 days), because late partner callbacks keep changing recent days.
* Partners may change or reverse outcomes later. Reversals are new events (`reward_reversed`), never silent edits.
