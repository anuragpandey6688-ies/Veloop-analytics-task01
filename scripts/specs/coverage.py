"""Work Package A: product area mapping (A1), user actions (A2), system outcomes (A3),
data coverage matrix (A4) and analytics gaps.

Status meaning in this matrix:
  Confirmed  = feature is described on an official VELOOP page (SRC-xx). Its implementation and
               any existing tracking are still To Be Verified (A-001, A-002).
  To Be Verified = feature mentioned but conflicting or unclear evidence.
  Proposed   = analytics design proposed by the analyst (no evidence the feature/data exists).
  Not live   = official page says the feature is not live yet; do not instrument now.
"""

# area, feature, user action, system action, business outcome, data required, proposed events, source, business question, status, evidence, priority
C = [
    ("Account", "Registration", "Submits sign-up (web form or Google sign-in)", "Creates account, assigns user_id", "New account",
     "user_id, registration_at_utc, registration_method, acquisition_source, signup_platform", "user_registered", "Backend",
     "How many users join, from which channels?", "Confirmed", "SRC-03, SRC-13", "Critical"),
    ("Account", "Login", "Signs in", "Authenticates, creates session", "Session started", "user_id, session_id, login_method, timestamp",
     "user_logged_in; user_logged_out", "Backend", "How often do users come back?", "Confirmed", "SRC-13 (Google login)", "High"),
    ("Account", "Onboarding", "Goes through first-run steps", "Records onboarding progress", "User ready to earn", "onboarding_version, step_key, started/completed timestamps",
     "onboarding_started; onboarding_step_completed; onboarding_completed", "Frontend + backend", "Where do new users drop before their first task?", "To Be Verified", "SRC-03 (status only)", "High"),
    ("Account", "Email verification", "Clicks verification link", "Marks email verified", "Verified account", "email_verified_at_utc", "email_verified", "Backend",
     "How long does verification take; does it block activation?", "Confirmed", "SRC-03", "Medium"),
    ("Account", "Account status", "(none: system/admin action) or requests deletion", "Changes status (active, inactive, suspended, closed)", "Lifecycle state",
     "previous_status, new_status, changed_at_utc, change_reason_category, changed_by_type", "account_status_changed", "Backend",
     "How many accounts are suspended or closed, and when?", "Confirmed", "SRC-03, SRC-06, SRC-13", "Critical"),
    ("Earning", "Task list / discovery", "Browses and opens tasks", "Renders task inventory", "Discovery", "task_id, task_type, list_position", "task_viewed; task_opened",
     "Frontend", "Which tasks attract attention but are not started?", "Proposed", "SRC-11", "Medium"),
    ("Earning", "Watch Ads", "Starts and watches an ad", "Partner tracks view; VELOOP validates; reward credited", "Validated ad view + reward",
     "activity_id, task_id, tracking_source, external_reference_id, validation_status, reward link", "task_started; task_submitted; task_completed; task_failed; reward_pending; reward_credited",
     "Backend + ad partner callback", "What share of ad starts end in a credited reward, and where do they fail?", "Confirmed", "SRC-07", "Critical"),
    ("Earning", "Surveys", "Starts and completes a survey", "Partner reports completion; validation", "Validated survey", "Same as Watch Ads + provider_id",
     "task_started; task_completed; task_failed", "Backend + survey partner", "Which survey partners fail tracking most?", "Confirmed", "Homepage, SRC-04", "High"),
    ("Earning", "App Tasks / Offers", "Installs or signs up for a partner app", "Partner postback; validation (can take long)", "Validated offer", "Same as Watch Ads + external_reference_id",
     "task_started; task_completed; task_failed", "Backend + offer partner", "How long do offer validations take and how many never return?", "Confirmed", "Homepage", "High"),
    ("Earning", "Captcha", "Solves captchas", "Validates answers", "Valid captcha batch", "activity_id, validation_status", "task_started; task_completed; task_failed", "Backend",
     "Is captcha a meaningful earning source?", "Confirmed", "Help route /earning/solve-captcha", "Medium"),
    ("Earning", "Tap & Earn", "Taps within limits", "Counts valid taps, applies limits", "Credited taps", "activity_id per tap batch (not per tap), validation_status",
     "task_started; task_completed; task_failed", "Backend", "How many users use Tap & Earn repeatedly?", "Confirmed", "Help route /earning/tap-and-earn", "Medium"),
    ("Earning", "Earning Session (Mine & earn)", "Starts a session (up to 1 h 30 min)", "Accrues credits, applies boosts", "Session reward", "activity_id, started/completed, reward",
     "task_started; task_completed; task_failed", "Backend", "Do users restart sessions; what share complete?", "Confirmed", "SRC-10", "Medium"),
    ("Earning", "Play & Earn (games)", "Plays a game (Tokens may be spent)", "Records result and rewards", "Game reward", "activity_id, reward unit (GEM/XP/VE)",
     "task_started; task_completed", "Backend", "Do games drive engagement or only cost?", "To Be Verified", "Homepage; other interns' repos only", "Low"),
    ("Earning", "Follow & Earn (social)", "Follows a social account", "Validates follow where possible", "Social reward", "activity_id, tracking_source",
     "task_started; task_completed; task_failed", "Backend", "Can social follows be validated at all?", "Confirmed", "SRC-11", "Low"),
    ("Engagement", "Daily Check-In", "Claims daily reward", "Validates one claim per IST day; credits reward", "Daily claim", "claim_date_ist, streak_length, reward_id",
     "daily_reward_claimed", "Backend", "What share of active users claim daily?", "Confirmed", "SRC-08", "High"),
    ("Engagement", "Streaks", "(implicit: consecutive claims)", "Increments or resets streak", "Streak state", "streak_length, previous_streak_length, streak_action",
     "streak_updated", "Backend", "How often do streaks reset and at what length?", "Confirmed", "SRC-08", "Medium"),
    ("Engagement", "Spin the Wheel", "Spends a Spin and spins", "Determines outcome, credits reward", "Spin outcome", "spin_id, spin_cost_unit, outcome_type, reward_id",
     "spin_started; spin_completed", "Backend", "How many spins are interrupted?", "Confirmed", "SRC-11", "Medium"),
    ("Engagement", "Missions", "Joins and completes mission conditions", "Tracks progress, verifies completion", "Mission complete", "mission_id, mission_progress_id, status, timestamps",
     "mission_started; mission_completed", "Backend", "Which missions are completed and which abandoned?", "Confirmed", "SRC-15", "Medium"),
    ("Engagement", "Badges", "(earned by progress)", "Awards badge", "Badge owned", "badge_id, badge_type, earned_at_utc", "badge_earned", "Backend",
     "Do badges correlate with retention?", "Confirmed", "SRC-15", "Low"),
    ("Engagement", "Levels / XP", "(earned by activity)", "Adds XP, changes level, may correct", "Level change", "previous_level, new_level, XP rewards", "level_reached; reward_credited",
     "Backend", "How fast do users progress?", "Confirmed", "Level System page", "Low"),
    ("Engagement", "Leaderboard", "Views leaderboard / enters weekly leaderboard", "Ranks users, may reward", "Leaderboard reward", "feature view, reward source_type = leaderboard",
     "feature_viewed; reward_credited", "Backend", "Does the leaderboard motivate activity?", "To Be Verified", "SRC-11", "Low"),
    ("Engagement", "Promo Codes", "Enters a promo code", "Validates and grants benefit", "Promo benefit", "promo_code_id, reward_id", "promo_code_redeemed", "Backend",
     "Which promos are redeemed, by whom?", "Confirmed", "SRC-11", "Low"),
    ("Rewards", "Reward lifecycle (all sources)", "(none)", "Creates pending reward, credits, rejects, reverses or corrects", "Reward credited / not credited",
     "reward_id, source_type, source_id, amount, unit, status, timestamps, reason category", "reward_pending; reward_credited; reward_rejected; reward_reversed; reward_corrected",
     "Backend", "How much activity actually turns into credited rewards, and how much is reversed?", "Confirmed", "SRC-06", "Critical"),
    ("Wallet", "Wallet ledger", "Views balances", "Writes ledger rows for every movement", "Correct balances", "transaction_id, type, direction, amount, unit, status, reference, related transaction",
     "wallet_transaction_created; wallet_transaction_completed; wallet_transaction_reversed", "Backend", "Can every balance be explained by its transactions?", "Confirmed", "SRC-04, Wallet overview page", "Critical"),
    ("Wallet", "Gems Exchange / Swap Center", "Converts Gems (or other units) to VEs", "Debits one unit, credits another", "Exchange", "from/to unit and amount, two transaction IDs",
     "currency_exchanged", "Backend", "How much value moves through exchange, at what rate?", "Confirmed", "SRC-16", "Medium"),
    ("Withdrawals", "Withdrawal request", "Requests payout (min Rs. 10) by UPI, PayPal or gift card", "Debits VEs, queues for review", "Request in queue",
     "withdrawal_id, amount_inr, ve_debited, payout_method, debit_transaction_id", "withdrawal_requested", "Backend", "How much payout demand is there and by which method?", "Confirmed", "SRC-05", "Critical"),
    ("Withdrawals", "Review and payout", "(waits)", "Reviews (system/manual), pays, rejects or reverses; refunds VEs if needed", "Completed / rejected / reversed payout",
     "status timestamps, reason_category, review_type, payout_reference_id, refund transaction", "withdrawal_processing; withdrawal_completed; withdrawal_rejected; withdrawal_reversed",
     "Backend + payout partner", "Are payouts processed within the published 24-72 h?", "Confirmed", "SRC-05, SRC-06", "Critical"),
    ("Referrals", "Refer & Earn", "Shares referral code/link", "Creates referral record, links referred user, validates, rewards", "Converted referral",
     "referral_id, referrer_user_id, referred_user_id, stage timestamps, status", "referral_created; referral_registered; referral_activated; referral_converted; referral_rejected",
     "Backend", "How many referred sign-ups become genuine, rewarded referrals?", "Confirmed", "SRC-09", "High"),
    ("Support", "Help Center", "Reads help articles", "Serves content", "Self-service", "content_id, content_category, user_id if logged in", "help_article_viewed", "Frontend",
     "Which topics do users read before contacting support?", "Confirmed", "SRC-11", "Low"),
    ("Support", "Support requests", "Emails support / requests manual review", "Logs and resolves request", "Resolved issue", "ticket_id, issue_category, timestamps, related entity",
     "support_ticket_created; support_ticket_resolved", "Support tool", "What drives support load and how fast is it handled?", "To Be Verified", "SRC-12, A-019", "Medium"),
    ("Navigation", "Screens", "Opens screens", "Renders screen", "Screen view", "screen_name, feature", "feature_viewed", "Frontend", "Which features are discovered?", "Proposed", "", "Low"),
    ("Future", "Lucky Draw, Team Battle, Referral Milestones, Collect Cards, Surprise/Mystery Rewards", "n/a", "n/a", "n/a",
     "Define at launch via change log (deliverable Q)", "None now", "n/a", "n/a", "Not live", "SRC-11 (official 'coming soon')", "Low"),
]

COVERAGE = [dict(zip(["product_area", "feature", "user_action", "system_action", "business_outcome", "data_required", "proposed_events",
                      "source", "business_question", "status", "evidence", "priority"], r)) for r in C]

# A2 lifecycles: which steps become events (measurable) and which are derived.
LIFECYCLES = {
    "Task": [("Task viewed", "task_viewed", "Client event"), ("Task opened", "task_opened", "Client event"),
             ("Task started", "task_started", "Server event; creates activity_id"),
             ("User finishes task action", "task_submitted", "Client event (task types with a finish step)"),
             ("Completion validated", "task_completed / task_failed", "Server event after validation (task_completed is emitted only when validation passes)"),
             ("Reward credited", "reward_pending -> reward_credited", "Server events in reward service"),
             ("Abandoned", "(derived)", "Not emitted by the client; derived when no completion within the timeout (A-013), recorded as task_failed with failure_category = user_abandoned")],
    "Withdrawal": [("Requested", "withdrawal_requested", "Server"), ("Under review / processing", "withdrawal_processing", "Server"),
                   ("Completed", "withdrawal_completed", "Server (partner confirmation)"), ("Rejected", "withdrawal_rejected", "Server; refund ledger row"),
                   ("Reversed", "withdrawal_reversed", "Server; refund ledger row")],
    "Referral": [("Referral created", "referral_created", "Server"), ("User registered", "referral_registered", "Server"),
                 ("User activated", "referral_activated", "Server"), ("Referral converted", "referral_converted", "Server; registration alone never counts")],
}

# A3: user event vs system event vs business outcome
EVENT_CLASSES = [
    ("User event", "Something the user does, observed by client or server.", "task_opened, task_started, daily_reward_claimed, withdrawal_requested, spin_started"),
    ("System event", "Something VELOOP's systems decide or record without a direct user action.", "task_completed (after validation), reward_credited, reward_reversed, withdrawal_completed, account_status_changed, referral_converted"),
    ("Business outcome", "A measured result computed from events; never emitted directly.", "Task completion rate, credited reward volume, withdrawal completion rate, referral conversion rate"),
]

# Analytics gaps (A4 expected output: at least 10)
GAPS = [
    ("G01", "No event-level activity data", "Supplied data is one snapshot row per user (last_login, lifetime_sessions, flags).", "DAU/WAU/MAU, retention and funnels cannot be computed.", "Critical"),
    ("G02", "Referred users cannot be linked to referrers", "Users has referral_source_detail = 'Friend/Family' only; no referral_id or referrer_user_id.", "Referral funnel and referral cost cannot be measured.", "Critical"),
    ("G03", "Timestamps have no timezone", "registration_datetime and last_login_datetime are naive.", "Day boundaries can be wrong by 5.5 h; daily reward/streak KPIs misalign with the IST claim window.", "High"),
    ("G04", "No account status history", "account_status is current state only.", "Suspension trends and lifecycle timing cannot be measured.", "High"),
    ("G05", "Balances without a ledger", "xp_balance is a stored balance; no transactions.", "Balances cannot be reconciled or explained.", "Critical"),
    ("G06", "Undocumented derived fields", "is_active_7d/30d and days_since_registration use an unstated reference date (inferred 2026-09-15 00:00) and login-based activity.", "Flags are not reproducible; definitions conflict with qualifying-activity DAU.", "Medium"),
    ("G07", "Seven of eight expected datasets missing", "Only Users supplied.", "Relationship and KPI tests impossible on supplied data (J2/J3).", "High"),
    ("G08", "No session identifier", "Only a lifetime counter.", "Session-level and returning-user analysis impossible.", "High"),
    ("G09", "No event_id / idempotency key", "No unique event or transaction identifiers in supplied structure.", "Duplicate events/credits cannot be detected.", "Critical"),
    ("G10", "No third-party tracking fields", "No provider_id, external_reference_id or validation status.", "Partner tracking failures cannot be separated from VELOOP failures (C4).", "High"),
    ("G11", "No onboarding or verification timestamps", "Status fields only.", "Time-to-onboard and cohort-based rates impossible.", "Medium"),
    ("G12", "Personal data in analytics dataset", "full_name, email, exact age, gender, city present.", "Privacy risk with no analytical need.", "High"),
    ("G13", "Platform/device semantics unclear", "platform = Web for all; primary_device mixes OS values; app status unknown.", "Platform split unreliable.", "Low"),
    ("G14", "No currency conversion rates", "Not published or supplied.", "Reward liability in INR cannot be computed.", "High"),
    ("G15", "Consent and marketing opt-in conflict", "34 users opted in while consent pending.", "Marketing audience may include non-consented users.", "High"),
    ("G16", "Supplied dictionary incomplete", "platform and country undocumented; no allowed values for account_status beyond 'controlled list'.", "Ambiguous fields.", "Low"),
]
