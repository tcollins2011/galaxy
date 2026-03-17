"""Shared utilities for agent evaluation tests."""


def calculate_model_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate API cost for a given model and token usage.

    Pricing as of 2024:
    - claude-opus-4-6: $15/1M input, $75/1M output
    - claude-sonnet-4-5: $3/1M input, $15/1M output
    - claude-haiku-4-5: $0.80/1M input, $4/1M output

    Args:
        model_name: Model identifier (e.g., "claude-sonnet-4-5", "anthropic:claude-sonnet-4-5")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Total cost in dollars
    """
    # Strip provider prefix (e.g., "anthropic:", "openai:", "google:")
    if ":" in model_name:
        model_name = model_name.split(":", 1)[1]

    # Normalize: lowercase, strip "claude-" prefix
    model_name = model_name.lower().replace("claude-", "")

    # Pricing per million tokens (input, output)
    pricing = {
        # Anthropic Claude
        "opus-4-6": (15.0, 75.0),
        "opus-4": (15.0, 75.0),
        "sonnet-4-6": (3.0, 15.0),
        "sonnet-4-5": (3.0, 15.0),
        "sonnet-4": (3.0, 15.0),
        "haiku-4-6": (0.80, 4.0),
        "haiku-4-5": (0.80, 4.0),
        "haiku-4": (0.80, 4.0),
        # OpenAI
        "gpt-4o": (2.50, 10.0),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4-turbo": (10.0, 30.0),
        "gpt-3.5-turbo": (0.50, 1.50),
        "gpt-5.4": (2.50, 15.0),
        # Google
        "gemini-2.0-flash": (0.10, 0.40),
        "gemini-2.5-pro": (1.25, 10.0),
        "gemini-1.5-pro": (1.25, 5.00),
        "gemini-1.5-flash": (0.075, 0.30),
    }

    # Get pricing or use a $0 fallback for unknown models
    input_price, output_price = pricing.get(model_name, (0.0, 0.0))

    # Calculate cost
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price

    return round(input_cost + output_cost, 4)
