ACTIVE_APPLICATION_PLANNING_OUTPUT_DIR = "outputs/application_planning"
ARCHIVED_APPLICATION_PLANNING_OUTPUT_DIR = "outputs/_archive"
SCHEDULER_RUN_HISTORY_PATH = "data/scheduler_run_history.jsonl"

SCORER_V2_POLICY_VERSION = "v1"

SCORER_V2_POLICY = {
    "prefilter": {
        "matched_terms_title_min_score": 0.45,
        "minimum_overlap": {
            "high_title_min_score": 0.80,
            "high_title_min_matched_any": 2,
            "high_title_ds_like_min_matched_any": 1,
            "mid_title_min_score": 0.45,
            "mid_title_min_matched_any": 3,
            # Preserve the currently working live values from the scorer lane.
            "coverage_title_min_score": 0.40,
            "coverage_min_matched_required": 2,
            "coverage_min_ratio": 0.25,
            "small_required_exact_max_count": 2,
            "small_required_exact_min_matched_any": 3,
            "absolute_required_min_matched": 3,
        },
        "required_skill_floor": {
            "large_required_min_count": 10,
            "large_required_min_ratio": 0.30,
            "large_required_min_matched": 4,
            "medium_required_min_count": 6,
            "medium_required_min_ratio": 0.25,
            "small_required_min_count": 3,
            "small_required_min_matched": 2,
        },
    },
    "selector": {
        "tie_epsilon": 0.010,
        "title_only_tie_epsilon": 0.015,
        "non_title_delta_epsilon": 0.002,
        "close_call_review_epsilon": 0.020,
    },
    "shortlist": {
        "high_confidence_apply_score": 0.70,
        "strong_tie_review_score": 0.64,
        "good_match_score": 0.58,
        "max_direct_apply_missing_requirements": 4,
        "max_strong_tie_missing_requirements": 4,
        "borderline_score": 0.50,
        "borderline_low_pass_rate": 0.50,
    },
}

APPLICATION_PRIORITY_POLICY_VERSION = "v2"

APPLICATION_PRIORITY_POLICY = {
    "weights": {
        "ai_signal_score": 0.50,
        "embedding_resume_prior_score": 0.00,
        "base_score": 0.30,
    },
}

APPLICATION_EXECUTION_QUEUE_POLICY_VERSION = "v1"

APPLICATION_EXECUTION_QUEUE_POLICY = {
    "action_rank": {
        "APPLY": 0,
        "APPLY_REVIEW_VARIANTS": 1,
        "MAYBE_TAILOR": 2,
        "SKIP_FOR_NOW": 3,
        "__default__": 99,
    },
    "tie_review_rank": {
        "apply_review_variants": 0,
        "maybe_tailor_variant_review": 1,
        "default": 2,
    },
}