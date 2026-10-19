from prometheus_client import Counter, Histogram

# How many tickets were created, split by category
TICKETS = Counter(
    "hr_tickets_total",
    "Tickets created, by category",
    ["category"],
)

# How long each LLM call took, split by step and model
LLM_LATENCY = Histogram(
    "hr_llm_latency_seconds",
    "How long each LLM call took",
    ["step", "model"],
    buckets=(0.5, 1, 2, 3, 5, 8, 13),
)

# How many tokens LLM calls used
LLM_TOKENS = Counter(
    "hr_llm_tokens_total",
    "Tokens used by LLM calls",
    ["step", "model", "direction"],    # direction: "input" or "output"
)

# How many errors happened, split by where
ERRORS = Counter(
    "hr_errors_total",
    "Errors, by where they happened",
    ["step"],
)