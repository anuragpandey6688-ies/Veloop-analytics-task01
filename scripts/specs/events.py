"""Work Package F: production event tracking plan (event catalogue).

Naming convention: object_action
  * lowercase snake_case, regex ^[a-z]+(_[a-z]+)+$
  * <object> is the business noun (task, reward, withdrawal...), <action> is a past-tense verb
    (or past-tense phrasal verb such as logged_in) from APPROVED_ACTIONS.
  * The feature/domain is a property (feature), not part of the name.
  Why: the Task 01 minimum event list already uses object_action; sorting by name groups each
  object's lifecycle together; names stay short; adding a domain prefix (domain_object_action)
  would duplicate the 'feature' property and break when a feature moves between domains.

Every event is PROPOSED. No event has been verified as implemented in VELOOP (A-001).
Money-related events must be emitted by the server (event_source = server).
"""

APPROVED_ACTIONS = ["registered", "logged_in", "logged_out", "started", "completed", "step_completed", "verified",
                    "changed", "viewed", "opened", "submitted", "failed", "pending", "credited", "reversed",
                    "corrected", "rejected", "claimed", "updated", "earned", "reached", "redeemed", "created",
                    "activated", "converted", "exchanged", "requested", "processing", "resolved"]

ENVELOPE_REQUIRED = ["event_id", "event_name", "user_id", "event_timestamp_utc", "received_at_utc", "feature",
                     "platform", "event_source", "schema_version", "data_environment"]
ENVELOPE_CLIENT_EXTRA = ["session_id"]
ENVELOPE_OPTIONAL = ["app_version"]

# name, domain, feature, source, trigger, definition, required props, optional props, KPI deps, purpose, priority, qualifying
EV = [
    # ---------------------------------------------------------------- Account
    ("user_registered", "Account", "account", "server", "Account record committed successfully in the backend.",
     "A new VELOOP account now exists.", ["registration_method", "acquisition_source", "signup_platform"],
     ["acquisition_campaign", "referral_id", "signup_device_type"], ["K-USR-01", "K-USR-10", "K-REF-02"],
     "Registrations, cohorts, acquisition mix.", "Critical", False),
    ("user_logged_in", "Account", "account", "server", "Authentication succeeded and a session was created.",
     "User signed in.", ["login_method", "session_id"], ["signup_device_type"], ["K-USR-06"],
     "Session starts and login mix. Not used for DAU (logins are not qualifying activity).", "High", False),
    ("user_logged_out", "Account", "account", "client", "User taps log out, or the server expires the session.",
     "Session ended. Emit only where a logout actually exists.", ["logout_type"], [], [],
     "Session duration accuracy.", "Low", False),
    ("onboarding_started", "Account", "onboarding", "client", "First onboarding screen is displayed to a newly registered user.",
     "User entered onboarding.", ["onboarding_version"], [], ["K-USR-08"], "Onboarding funnel entry.", "High", False),
    ("onboarding_step_completed", "Account", "onboarding", "client", "User completes one onboarding step.",
     "Milestone within onboarding.", ["onboarding_version", "step_key", "step_index"], [], ["K-USR-08"],
     "Step-level drop-off.", "Medium", False),
    ("onboarding_completed", "Account", "onboarding", "server", "Backend marks onboarding complete for the user.",
     "User finished onboarding.", ["onboarding_version"], [], ["K-USR-08"], "Onboarding completion.", "High", False),
    ("email_verified", "Account", "account", "server", "Email verification link/code accepted.",
     "User's email verified.", [], [], ["K-USR-09"], "Verification funnel.", "Medium", False),
    ("account_status_changed", "Account", "account", "server", "account_status value changes in the backend.",
     "Lifecycle transition (e.g. active to suspended).", ["previous_status", "new_status", "change_reason_category", "changed_by_type"],
     [], ["K-USR-11", "K-USR-07"], "Lifecycle and enforcement reporting.", "Critical", False),

    # ---------------------------------------------------------------- Tasks
    ("task_viewed", "Tasks", "tasks", "client", "Task card is at least 50% visible in the viewport for 1 second.",
     "User was shown a task (discovery).", ["task_id", "task_type"], ["list_position"], ["K-ENG-01"],
     "Discovery stage of earning funnel.", "Medium", False),
    ("task_opened", "Tasks", "tasks", "client", "User taps a task card to open its detail or provider screen.",
     "User showed intent on a task.", ["task_id", "task_type"], ["list_position"], [], "Discovery-to-start conversion.", "Medium", False),
    ("task_started", "Tasks", "tasks", "server", "Backend creates the task_activity record (activity_id issued).",
     "An attempt began.", ["activity_id", "task_id", "task_type", "tracking_source"], ["session_id"], ["K-ENG-02", "K-ENG-04"],
     "Start stage; denominator of completion rate.", "Critical", True),
    ("task_submitted", "Tasks", "tasks", "client", "User finishes the task action and returns to VELOOP; validation not yet complete.",
     "User-side completion claimed. Emitted only for task types with a user-visible finish step.", ["activity_id", "task_id"], [], ["K-RWD-06"],
     "Separates user completion from validated completion.", "Medium", True),
    ("task_completed", "Tasks", "tasks", "server", "Task completion has passed the applicable validation process.",
     "A validated completion. Exactly one per activity_id.", ["activity_id", "task_id", "task_type", "activity_status", "validation_status", "reward_amount", "reward_unit"],
     ["external_reference_id"], ["K-ENG-03", "K-ENG-04", "K-RWD-06"], "Completion stage.", "Critical", True),
    ("task_failed", "Tasks", "tasks", "server", "Attempt reaches a final failed state, including validation failure, tracking failure, system error, or abandonment timeout.",
     "Attempt ended without a validated completion.", ["activity_id", "task_id", "task_type", "failure_category", "failure_stage"],
     ["external_reference_id"], ["K-ENG-05", "K-ENG-06"], "Failure analysis by category.", "Critical", False),

    # ---------------------------------------------------------------- Rewards
    ("reward_pending", "Rewards", "wallet", "server", "Reward record created but awaiting validation.",
     "A reward is expected but NOT yet credited.", ["reward_id", "source_type", "source_id", "amount", "unit"], [], ["K-RWD-01", "K-RWD-04"],
     "Pending backlog.", "Critical", False),
    ("reward_credited", "Rewards", "wallet", "server", "Reward committed to the user's balance.",
     "The reward was actually credited (distinct from the activity occurring).", ["reward_id", "source_type", "source_id", "amount", "unit"],
     ["wallet_transaction_id"], ["K-RWD-01", "K-RWD-02", "K-RWD-05", "K-RWD-06"], "Actual reward cost.", "Critical", False),
    ("reward_rejected", "Rewards", "wallet", "server", "A pending reward is not granted after validation.",
     "Reward never credited.", ["reward_id", "reversal_reason_category"], [], ["K-RWD-01"], "Pending outcomes.", "High", False),
    ("reward_reversed", "Rewards", "wallet", "server", "A previously credited reward is fully reversed.",
     "Credited reward removed.", ["reward_id", "amount", "unit", "reversal_reason_category"], ["wallet_transaction_id"], ["K-RWD-03", "K-WAL-04"],
     "Reversal rate.", "Critical", False),
    ("reward_corrected", "Rewards", "wallet", "server", "A credited reward's amount is changed by a correction.",
     "Partial correction of a credited reward.", ["reward_id", "previous_amount", "final_amount", "unit", "reversal_reason_category"],
     ["wallet_transaction_id"], ["K-RWD-02", "K-WAL-04"], "Net reward accuracy.", "High", False),

    # ---------------------------------------------------------------- Daily / Engagement
    ("daily_reward_claimed", "Engagement", "daily_rewards", "server", "Valid daily claim accepted within the IST claim window.",
     "User claimed the daily reward for an IST day.", ["claim_date_ist", "streak_length"], ["reward_id"], ["K-ENG-09"],
     "Daily habit loop.", "High", True),
    ("streak_updated", "Engagement", "daily_rewards", "server", "Streak counter changes (increment, reset or start).",
     "Streak state changed.", ["streak_length", "previous_streak_length", "streak_action"], [], ["K-ENG-09"],
     "Streak continuity and resets.", "Medium", False),
    ("mission_started", "Engagement", "missions", "server", "User joins or is enrolled in a mission.",
     "Mission progress record created.", ["mission_id", "mission_progress_id"], [], ["K-ENG-11"], "Mission funnel.", "Medium", True),
    ("mission_completed", "Engagement", "missions", "server", "All mission conditions verified complete.",
     "Mission completed.", ["mission_id", "mission_progress_id"], ["reward_id"], ["K-ENG-11"], "Mission completion.", "Medium", False),
    ("badge_earned", "Engagement", "badges", "server", "Badge awarded to the user.",
     "User earned a badge.", ["badge_id", "badge_type"], ["reward_id"], ["K-ENG-01"], "Achievement engagement.", "Low", False),
    ("level_reached", "Engagement", "level_dashboard", "server", "User's level changes.",
     "Level changed (normally up; may be a correction).", ["previous_level", "new_level"], [], ["K-ENG-08"], "Progression speed.", "Low", False),
    ("spin_started", "Engagement", "spin", "server", "Spin request accepted and spin cost deducted.",
     "A spin attempt began.", ["spin_id", "spin_cost_unit"], [], ["K-ENG-10"], "Spin usage.", "Medium", True),
    ("spin_completed", "Engagement", "spin", "server", "Spin outcome recorded by the backend.",
     "Spin finished with an outcome.", ["spin_id", "outcome_type"], ["reward_id"], ["K-ENG-10"], "Spin completion and interruption.", "Medium", False),
    ("promo_code_redeemed", "Engagement", "promo_codes", "server", "Promo code accepted and benefit granted.",
     "Promo redemption.", ["promo_code_id"], ["reward_id"], ["K-RWD-05"], "Promo effectiveness.", "Low", True),
    ("feature_viewed", "Engagement", "home", "client", "A product screen becomes visible.",
     "Screen view. Feature property names the screen's feature.", ["screen_name"], [], ["K-ENG-01"], "Navigation analysis.", "Low", False),

    # ---------------------------------------------------------------- Referrals
    ("referral_created", "Referrals", "referrals", "server", "Referrer shares an invite through an in-app share action, or a referral record is created at registration for a code used without a tracked share.",
     "Referral relationship record exists.", ["referral_id", "referrer_user_id", "referral_code"], ["referral_channel"], ["K-REF-01"],
     "Top of referral funnel.", "High", True),
    ("referral_registered", "Referrals", "referrals", "server", "A new account is created with a valid referral code.",
     "Referred user registered. NOT a conversion.", ["referral_id", "referrer_user_id", "referred_user_id"], [], ["K-REF-02", "K-REF-05"],
     "Referral sign-ups.", "Critical", False),
    ("referral_activated", "Referrals", "referrals", "server", "Referred user completes the first eligible activity.",
     "Referred user became active.", ["referral_id", "referred_user_id", "activity_id"], [], ["K-REF-03"], "Referred-user quality.", "High", False),
    ("referral_converted", "Referrals", "referrals", "server", "Referral passes validation and the referral reward is approved.",
     "Successful referral.", ["referral_id", "referrer_user_id", "reward_id"], [], ["K-REF-04", "K-REF-05"], "Referral success and cost.", "Critical", False),
    ("referral_rejected", "Referrals", "referrals", "server", "Referral fails validation.",
     "Referral will not be rewarded.", ["referral_id", "rejection_reason_category"], [], ["K-REF-06"], "Referral abuse handling.", "High", False),

    # ---------------------------------------------------------------- Wallet
    ("wallet_transaction_created", "Wallet", "wallet", "server", "Ledger row inserted.",
     "A balance movement was recorded.", ["transaction_id", "transaction_type", "direction", "amount", "unit", "transaction_status", "reference_type"],
     ["reference_id", "related_transaction_id"], ["K-WAL-01", "K-WAL-05"], "Ledger completeness.", "Critical", False),
    ("wallet_transaction_completed", "Wallet", "wallet", "server", "Ledger row reaches 'completed'.",
     "Balance movement is final.", ["transaction_id", "transaction_type", "direction", "amount", "unit"], [], ["K-WAL-02", "K-WAL-03"],
     "Settled volume.", "Critical", False),
    ("wallet_transaction_reversed", "Wallet", "wallet", "server", "Ledger row is reversed by a linked reversing row.",
     "Movement undone.", ["transaction_id", "related_transaction_id", "amount", "unit"], [], ["K-WAL-04"], "Reversal tracking.", "Critical", False),
    ("currency_exchanged", "Wallet", "exchange", "server", "Exchange request completed in the Gems Exchange / Swap Center.",
     "Internal conversion between units.", ["from_unit", "to_unit", "from_amount", "to_amount", "transaction_id", "credit_transaction_id"],
     [], ["K-WAL-01"], "Exchange usage.", "Medium", True),

    # ---------------------------------------------------------------- Withdrawals
    ("withdrawal_requested", "Withdrawals", "withdrawals", "server", "Withdrawal request accepted by the backend and redemption debit created.",
     "User asked for a payout.", ["withdrawal_id", "amount_inr", "ve_debited", "payout_method", "debit_transaction_id"], [], ["K-WDR-01", "K-WDR-03", "K-WDR-09"],
     "Payout demand.", "Critical", True),
    ("withdrawal_processing", "Withdrawals", "withdrawals", "server", "Request moves into review/processing.",
     "Payout under review.", ["withdrawal_id"], ["review_type"], ["K-WDR-03"], "Queue stage timing.", "High", False),
    ("withdrawal_completed", "Withdrawals", "withdrawals", "server", "Payout partner confirms the transfer.",
     "Payout delivered.", ["withdrawal_id", "amount_inr", "payout_method"], ["payout_reference_id"], ["K-WDR-02", "K-WDR-06", "K-WDR-07", "K-WDR-10"],
     "Completed payouts.", "Critical", False),
    ("withdrawal_rejected", "Withdrawals", "withdrawals", "server", "Request rejected during review.",
     "Payout refused; VEs refunded.", ["withdrawal_id", "reason_category"], ["refund_transaction_id"], ["K-WDR-04", "K-WDR-06"],
     "Rejection analysis.", "Critical", False),
    ("withdrawal_reversed", "Withdrawals", "withdrawals", "server", "A completed payout is reversed (e.g. partner failure).",
     "Completed payout undone.", ["withdrawal_id", "reason_category"], ["refund_transaction_id"], ["K-WDR-05"],
     "Post-completion failures.", "High", False),

    # ---------------------------------------------------------------- Support / Content
    ("help_article_viewed", "Support", "help_center", "client", "Help-center article becomes visible.",
     "User read help content.", ["content_id", "content_category"], [], ["K-SUP-03"], "Self-service usage.", "Low", False),
    ("support_ticket_created", "Support", "support", "server", "Support request logged in the support tool.",
     "User contacted support.", ["ticket_id", "issue_category"], ["related_entity_type", "related_entity_id"], ["K-SUP-01", "K-SUP-02"],
     "Support load and categories.", "Medium", False),
    ("support_ticket_resolved", "Support", "support", "server", "Ticket marked resolved.",
     "Support issue resolved.", ["ticket_id", "ticket_status"], [], ["K-SUP-04"], "Resolution time.", "Low", False),
]

EVENTS = []
for row in EV:
    name, domain, feature, source, trigger, definition, req, opt, kpis, purpose, priority, qualifying = row
    EVENTS.append(dict(event_name=name, domain=domain, feature=feature, event_source=source, trigger=trigger,
                       definition=definition, required_properties=req, optional_properties=opt, kpi_dependency=kpis,
                       business_purpose=purpose, priority=priority, qualifying_activity=qualifying,
                       status="Proposed", implementation_status="Not verified - requires engineering confirmation (A-001)"))

QUALIFYING_EVENTS = [e["event_name"] for e in EVENTS if e["qualifying_activity"]]
