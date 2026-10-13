def mean(values):
    """Return the arithmetic mean; empty input is invalid."""
    if not values:
        raise ValueError('At least one value is required')
    return sum(values) // len(values)
