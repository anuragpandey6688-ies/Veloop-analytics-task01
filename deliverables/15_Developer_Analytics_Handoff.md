# 15 · Developer Analytics Handoff

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

This document is written for the engineers who will implement tracking. It covers the 19 events whose errors would corrupt money, identity, lifecycle or referral reporting. The rest are in the tracking plan (08).

## Global rules (apply to every event)

1. **Server is the source of truth** for task completion, rewards, wallet, withdrawals, referrals and account status. Emit the event in the **same database transaction** as the business write (outbox pattern), so an event can never exist without its record, or the record without its event.
2. **`event_id` is generated once** by the producer and reused on every retry. The collection layer deduplicates on it.
3. **Idempotency keys** on reward and wallet writes (`<source_type>:<source_id>`), with a unique index, so a retried request cannot credit twice.
4. **UTC everywhere** (ISO 8601 with `Z`). Reporting converts to IST day.
5. **No personal data or secrets in payloads.** Never include names, emails, phone numbers, UPI IDs, account or card numbers, tokens, passwords or fraud-rule details.
6. Every payload carries `schema_version` and `data_environment`. Staging must emit `staging`.
7. All values come from the allowed lists in the data dictionary (09). Unknown values are rejected, not coerced.
8. These are proposals. Final implementation, especially idempotency, is engineering's decision. Anything that cannot be built as written goes back into the change log (Q).

### REQ-001 · `user_registered`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-001 |
| Event | `user_registered` |
| Trigger | Account record committed successfully in the backend. |
| Source | server |
| Deduplication | One per user_id; dedup on user_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Registrations, cohorts, acquisition mix. |
| KPI dependency | K-USR-01, K-USR-10, K-REF-02 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| registration_method | enum | Must be in allowed list | Yes |
| acquisition_source | enum | Must be in allowed list; 'referral' requires referral_id | Yes |
| signup_platform | enum | Must be in allowed list | Yes |

Optional: `acquisition_campaign`, `referral_id`, `signup_device_type`, `app_version`

Acceptance tests:
1. Creating an account emits exactly one user_registered with the new user_id.
2. Failed sign-up (validation error) emits nothing.
3. acquisition_source is captured once and is not overwritten by later visits.
### REQ-002 · `account_status_changed`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-002 |
| Event | `account_status_changed` |
| Trigger | account_status value changes in the backend. |
| Source | server |
| Deduplication | One per status_change_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Lifecycle and enforcement reporting. |
| KPI dependency | K-USR-11, K-USR-07 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| previous_status | enum | Must differ from new_status | Yes |
| new_status | enum | Must be an allowed transition (deliverable 13 state rules) | Yes |
| change_reason_category | enum | Must be in allowed list | Yes |
| changed_by_type | enum | Must be in allowed list | Yes |

Optional: `app_version`

Acceptance tests:
1. Suspending a test account emits one event with previous_status=active, new_status=suspended.
2. Setting the same status again emits nothing.
3. A matching user_status_history row exists with the same timestamp.
### REQ-003 · `task_started`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-003 |
| Event | `task_started` |
| Trigger | Backend creates the task_activity record (activity_id issued). |
| Source | server |
| Deduplication | One per activity_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Start stage; denominator of completion rate. |
| KPI dependency | K-ENG-02, K-ENG-04 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| activity_id | string | Non-null; immutable; unique within entity | Yes |
| task_id | string | Non-null; immutable; unique within entity | Yes |
| task_type | enum | Must be in allowed list | Yes |
| tracking_source | string | 'veloop' or a value in the partner register | Yes |

Optional: `session_id`, `app_version`

Acceptance tests:
1. Starting a task creates exactly one activity_id and one task_started.
2. Re-opening the same in-progress task does not create a second activity_id (within the timeout).
### REQ-004 · `task_completed`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-004 |
| Event | `task_completed` |
| Trigger | Task completion has passed the applicable validation process. |
| Source | server |
| Deduplication | One per activity_id; dedup on activity_id + event_name. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Completion stage. |
| KPI dependency | K-ENG-03, K-ENG-04, K-RWD-06 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| activity_id | string | Non-null; immutable; unique within entity | Yes |
| task_id | string | Non-null; immutable; unique within entity | Yes |
| task_type | enum | Must be in allowed list | Yes |
| activity_status | enum | Must be in allowed list; only forward transitions | Yes |
| validation_status | enum | 'passed' only with activity_status = completed | Yes |
| reward_amount | integer | >= 0 | Yes |
| reward_unit | enum | Must be in allowed list | Yes |

Optional: `external_reference_id`, `app_version`

Acceptance tests:
1. When a valid task completion occurs, exactly one analytically usable completion event is recorded for the task/user transaction, subject to the final engineering implementation and idempotency design.
2. A partner callback retried 3 times produces one task_completed.
3. A completion that fails validation produces task_failed (validation_failed), not task_completed.
### REQ-005 · `task_failed`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-005 |
| Event | `task_failed` |
| Trigger | Attempt reaches a final failed state, including validation failure, tracking failure, system error, or abandonment timeout. |
| Source | server |
| Deduplication | One per activity_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Failure analysis by category. |
| KPI dependency | K-ENG-05, K-ENG-06 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| activity_id | string | Non-null; immutable; unique within entity | Yes |
| task_id | string | Non-null; immutable; unique within entity | Yes |
| task_type | enum | Must be in allowed list | Yes |
| failure_category | enum | Required when activity_status in (failed, abandoned) | Yes |
| failure_stage | enum | Must be in allowed list | Yes |

Optional: `external_reference_id`, `app_version`

Acceptance tests:
1. A simulated partner tracking timeout produces task_failed with failure_category=tracking_failed, failure_stage=tracking.
2. No activity has both task_completed and task_failed.
### REQ-006 · `reward_pending`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-006 |
| Event | `reward_pending` |
| Trigger | Reward record created but awaiting validation. |
| Source | server |
| Deduplication | One per reward_id; reward idempotency_key = <source_type>:<source_id>. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Pending backlog. |
| KPI dependency | K-RWD-01, K-RWD-04 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| reward_id | string | Non-null; immutable; unique within entity | Yes |
| source_type | enum | Must be in allowed list | Yes |
| source_id | string | Must resolve in the table implied by source_type | Yes |
| amount | integer | > 0 | Yes |
| unit | enum | Must be in allowed list | Yes |

Optional: `app_version`

Acceptance tests:
1. A task awaiting partner validation shows one reward_pending and no reward_credited.
### REQ-007 · `reward_credited`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-007 |
| Event | `reward_credited` |
| Trigger | Reward committed to the user's balance. |
| Source | server |
| Deduplication | One per reward_id; idempotency_key unique. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Actual reward cost. |
| KPI dependency | K-RWD-01, K-RWD-02, K-RWD-05, K-RWD-06 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| reward_id | string | Non-null; immutable; unique within entity | Yes |
| source_type | enum | Must be in allowed list | Yes |
| source_id | string | Must resolve in the table implied by source_type | Yes |
| amount | integer | > 0 | Yes |
| unit | enum | Must be in allowed list | Yes |

Optional: `wallet_transaction_id`, `app_version`

Acceptance tests:
1. Crediting a reward emits one reward_credited and creates one wallet reward_credit row (wallet units) with matching amount and unit.
2. Retrying the credit API with the same idempotency_key does not create a second credit.
3. XP rewards emit reward_credited without a wallet row (until A-012 is resolved).
### REQ-008 · `reward_reversed`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-008 |
| Event | `reward_reversed` |
| Trigger | A previously credited reward is fully reversed. |
| Source | server |
| Deduplication | One per reward_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Reversal rate. |
| KPI dependency | K-RWD-03, K-WAL-04 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| reward_id | string | Non-null; immutable; unique within entity | Yes |
| amount | integer | > 0 | Yes |
| unit | enum | Must be in allowed list | Yes |
| reversal_reason_category | enum | Required when status in (reversed, corrected) | Yes |

Optional: `wallet_transaction_id`, `app_version`

Acceptance tests:
1. Reversing a credited reward emits reward_reversed and one wallet reversal row whose related_transaction_id is the original credit.
2. final_amount becomes 0; amount keeps the original value.
### REQ-009 · `daily_reward_claimed`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-009 |
| Event | `daily_reward_claimed` |
| Trigger | Valid daily claim accepted within the IST claim window. |
| Source | server |
| Deduplication | One per user_id + claim_date_ist. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Daily habit loop. |
| KPI dependency | K-ENG-09 |
| Priority | High |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| claim_date_ist | date | YYYY-MM-DD; one claim per user per date | Yes |
| streak_length | integer | >= 0 | Yes |

Optional: `reward_id`, `app_version`

Acceptance tests:
1. Two claims on the same IST day: the second is refused and no event is emitted.
2. A claim at 23:59 IST and one at 00:01 IST count for two different claim dates.
### REQ-010 · `referral_registered`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-010 |
| Event | `referral_registered` |
| Trigger | A new account is created with a valid referral code. |
| Source | server |
| Deduplication | One per referral_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Referral sign-ups. |
| KPI dependency | K-REF-02, K-REF-05 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| referral_id | string | Must exist in referrals.referral_id when present | Yes |
| referrer_user_id | string | Must exist in users | Yes |
| referred_user_id | string | Must exist in users; must differ from referrer_user_id | Yes |

Optional: `app_version`

Acceptance tests:
1. A sign-up with a valid code emits referral_registered with both user IDs; referral_status = registered (not converted).
2. Self-referral attempt: referrer_user_id = referred_user_id is rejected.
### REQ-011 · `referral_converted`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-011 |
| Event | `referral_converted` |
| Trigger | Referral passes validation and the referral reward is approved. |
| Source | server |
| Deduplication | One per referral_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Referral success and cost. |
| KPI dependency | K-REF-04, K-REF-05 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| referral_id | string | Must exist in referrals.referral_id when present | Yes |
| referrer_user_id | string | Must exist in users | Yes |
| reward_id | string | Non-null; immutable; unique within entity | Yes |

Optional: `app_version`

Acceptance tests:
1. Conversion only after first eligible activity and validation; emits reward_id that exists in rewards.
2. A referral that is registered but never activated never emits referral_converted.
### REQ-012 · `wallet_transaction_created`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-012 |
| Event | `wallet_transaction_created` |
| Trigger | Ledger row inserted. |
| Source | server |
| Deduplication | One per transaction_id; idempotency_key unique. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Ledger completeness. |
| KPI dependency | K-WAL-01, K-WAL-05 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| transaction_id | string | Non-null; immutable; unique within entity | Yes |
| transaction_type | enum | Must be in allowed list; exchange types Proposed | Yes |
| direction | enum | Must agree with transaction_type | Yes |
| amount | integer | > 0 | Yes |
| unit | enum | Must be in allowed list | Yes |
| transaction_status | enum | pending->completed\|failed; completed->reversed | Yes |
| reference_type | enum | Must be in allowed list | Yes |

Optional: `reference_id`, `related_transaction_id`, `app_version`

Acceptance tests:
1. Every balance change produces exactly one ledger row.
2. Reversal rows always carry related_transaction_id.
3. Sum of ledger per user/unit equals displayed balance in a test account.
### REQ-013 · `wallet_transaction_completed`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-013 |
| Event | `wallet_transaction_completed` |
| Trigger | Ledger row reaches 'completed'. |
| Source | server |
| Deduplication | One per transaction_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Settled volume. |
| KPI dependency | K-WAL-02, K-WAL-03 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| transaction_id | string | Non-null; immutable; unique within entity | Yes |
| transaction_type | enum | Must be in allowed list; exchange types Proposed | Yes |
| direction | enum | Must agree with transaction_type | Yes |
| amount | integer | > 0 | Yes |
| unit | enum | Must be in allowed list | Yes |

Optional: `app_version`

Acceptance tests:
1. Pending redemption debit emits completed only when the withdrawal completes.
### REQ-014 · `wallet_transaction_reversed`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-014 |
| Event | `wallet_transaction_reversed` |
| Trigger | Ledger row is reversed by a linked reversing row. |
| Source | server |
| Deduplication | One per transaction_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Reversal tracking. |
| KPI dependency | K-WAL-04 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| transaction_id | string | Non-null; immutable; unique within entity | Yes |
| related_transaction_id | string | Required for reversal, adjustment, refund, exchange_credit; must exist | Yes |
| amount | integer | > 0 | Yes |
| unit | enum | Must be in allowed list | Yes |

Optional: `app_version`

Acceptance tests:
1. Reversed row status becomes 'reversed' and a linked reversing row exists.
### REQ-015 · `withdrawal_requested`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-015 |
| Event | `withdrawal_requested` |
| Trigger | Withdrawal request accepted by the backend and redemption debit created. |
| Source | server |
| Deduplication | One per withdrawal_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Payout demand. |
| KPI dependency | K-WDR-01, K-WDR-03, K-WDR-09 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| withdrawal_id | string | Non-null; immutable; unique within entity | Yes |
| amount_inr | decimal | >= published minimum (Rs. 10 as of 2026-10-01) | Yes |
| ve_debited | integer | > 0; equals linked redemption_debit amount | Yes |
| payout_method | enum | Must be in allowed list | Yes |
| debit_transaction_id | string | Must exist in wallet_transactions | Yes |

Optional: `app_version`

Acceptance tests:
1. A request emits withdrawal_requested and one pending redemption_debit with ve_debited.
2. A request below the published minimum is rejected by the API and emits nothing.
3. Double-tapping submit creates one withdrawal_id.
### REQ-016 · `withdrawal_processing`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-016 |
| Event | `withdrawal_processing` |
| Trigger | Request moves into review/processing. |
| Source | server |
| Deduplication | One per withdrawal_id per transition. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Queue stage timing. |
| KPI dependency | K-WDR-03 |
| Priority | High |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| withdrawal_id | string | Non-null; immutable; unique within entity | Yes |

Optional: `review_type`, `app_version`

Acceptance tests:
1. Moving to review emits one event; processing timestamp >= requested timestamp.
### REQ-017 · `withdrawal_completed`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-017 |
| Event | `withdrawal_completed` |
| Trigger | Payout partner confirms the transfer. |
| Source | server |
| Deduplication | One per withdrawal_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Completed payouts. |
| KPI dependency | K-WDR-02, K-WDR-06, K-WDR-07, K-WDR-10 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| withdrawal_id | string | Non-null; immutable; unique within entity | Yes |
| amount_inr | decimal | >= published minimum (Rs. 10 as of 2026-10-01) | Yes |
| payout_method | enum | Must be in allowed list | Yes |

Optional: `payout_reference_id`, `app_version`

Acceptance tests:
1. Partner confirmation emits withdrawal_completed; redemption debit becomes completed; final timestamp >= processing.
### REQ-018 · `withdrawal_rejected`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-018 |
| Event | `withdrawal_rejected` |
| Trigger | Request rejected during review. |
| Source | server |
| Deduplication | One per withdrawal_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Rejection analysis. |
| KPI dependency | K-WDR-04, K-WDR-06 |
| Priority | Critical |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| withdrawal_id | string | Non-null; immutable; unique within entity | Yes |
| reason_category | enum | Required when status in (rejected, reversed) | Yes |

Optional: `refund_transaction_id`, `app_version`

Acceptance tests:
1. Rejection emits reason_category and creates one redemption_refund ledger row of equal amount.
### REQ-019 · `withdrawal_reversed`

| Item | Specification |
| --- | --- |
| Requirement ID | REQ-019 |
| Event | `withdrawal_reversed` |
| Trigger | A completed payout is reversed (e.g. partner failure). |
| Source | server |
| Deduplication | One per withdrawal_id. Collection layer drops repeated `event_id`. |
| Timestamp | `event_timestamp_utc` = moment the business state changed (not when the event was sent), ISO 8601 UTC; `received_at_utc` stamped by collection. |
| Why needed | Post-completion failures. |
| KPI dependency | K-WDR-05 |
| Priority | High |

Payload (required fields):

| property | data_type | validation | required |
| --- | --- | --- | --- |
| event_id | string | Non-null; immutable; unique within entity; UUID in production; duplicates are dropped on ingestion | Yes |
| event_name | enum | Must match ^[a-z]+(_[a-z]+)+$ and be in catalogue | Yes |
| user_id | string | Non-null; immutable; unique within entity; pattern agreed with engineering (simulated: ^VLUSR\d{6}$) | Yes |
| event_timestamp_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | Yes |
| received_at_utc | timestamp | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= event_timestamp_utc - 5 min | Yes |
| feature | enum | Must be in allowed list | Yes |
| platform | enum | Must be in allowed list | Yes |
| event_source | enum | Must match the catalogue's declared source | Yes |
| schema_version | integer | >= 1; must match a version in the change log | Yes |
| data_environment | enum | Must equal 'production' in any table feeding management dashboards | Yes |
| withdrawal_id | string | Non-null; immutable; unique within entity | Yes |
| reason_category | enum | Required when status in (rejected, reversed) | Yes |

Optional: `refund_transaction_id`, `app_version`

Acceptance tests:
1. Only a completed withdrawal can be reversed; emits refund row.
