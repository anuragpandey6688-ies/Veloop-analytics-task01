# 07 · Referral & Engagement Analytics

> **Status:** proposed specification. No event, field, table or KPI in this document has been verified as implemented in VELOOP production (see Assumption A-001). Facts taken from official VELOOP pages cite a source ID from the Source & Verification Register (deliverable 19).

## Referral funnel: registration is not conversion

```
referral_created ──► referral_registered ──► referral_activated ──► referral_converted
                               │                     │
                               └──────► referral_rejected / expired
```

Official basis (SRC-09): the referred user "may need to complete a first eligible activity" and pass verification **before** a referral reward is approved. So:

* **Registered:** the referred user created an account with a valid code. This counts towards K-REF-02 only.
* **Activated:** the referred user completed the first eligible activity (the definition is pending, A-017).
* **Converted:** validation passed and the referral reward was approved (`reward_id` set).
* **Rejected:** validation failed. Only a reason category is stored, never the detection rule.

## E1 Referral data

| field_name | data_type | required | allowed_values | validation | definition |
| --- | --- | --- | --- | --- | --- |
| referral_id | string | Yes |  | Non-null; immutable; unique within entity | Identifier of one referral relationship. |
| referrer_user_id | string | Yes |  | Must exist in users | User who referred. |
| referred_user_id | string | Conditional |  | Must exist in users; must differ from referrer_user_id | User who registered through the referral. Blank until registration. |
| referral_code | string | Yes |  | Must belong to referrer_user_id | Referrer's code used. Codes are public share codes, not secrets. |
| referral_channel | enum | No | whatsapp, telegram, copy_link, other | Must be in allowed list | Channel used to share the invite, when known. |
| referral_status | enum | Yes | created, registered, activated, converted, rejected, expired | created->registered->activated->converted; ->rejected\|expired | Furthest stage reached. Registration alone is NOT conversion. |
| created_at_utc | timestamp | Yes |  | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew | When the referral record was created. |
| registered_at_utc | timestamp | Conditional |  | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= created_at_utc | When the referred user registered. |
| activated_at_utc | timestamp | Conditional |  | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= registered_at_utc | When the referred user completed the first eligible activity. |
| converted_at_utc | timestamp | Conditional |  | ISO 8601 UTC with Z suffix; not in the future beyond 5 min clock skew; >= activated_at_utc | When the referral passed validation and the referral reward was approved. |
| rejection_reason_category | enum | Conditional | verification_failed, policy_violation | Required when status = rejected | Why a referral was rejected. |
| reward_id | string | Conditional |  | Required when converted; must exist in rewards | Referral reward issued on conversion. |

In the supplied dataset, 119 users have `acquisition_source = Referral`, but no field links them to a referrer. This is the single biggest referral gap (G02).

## E2 Engagement measurement

| Measure | Definition | KPI |
| --- | --- | --- |
| Feature adoption | Share of active users using a feature at least once in the period | K-ENG-01 |
| Repeat usage | Share of a feature's users active on it on 2 or more IST days | K-ENG-07 |
| Task activity | Starts, validated completions, completion/abandonment/failure rates | K-ENG-02..06 |
| Daily activity | DAU on qualifying events; daily reward claim rate | K-USR-02, K-ENG-09 |
| Feature frequency | Active days per active user; events per active user per feature | K-ENG-08 |
| Active users | DAU / WAU / MAU and stickiness | K-USR-02..05 |
| Returning users | Active now, active before, registered before the window | K-USR-06 |

Qualifying activity events (10): `task_started`, `task_submitted`, `task_completed`, `daily_reward_claimed`, `mission_started`, `spin_started`, `promo_code_redeemed`, `referral_created`, `currency_exchanged`, `withdrawal_requested`.
