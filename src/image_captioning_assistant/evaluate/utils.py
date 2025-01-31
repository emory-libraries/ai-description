def mean(vals: list[float]) -> float:
    """Find mean of list of values.

    Args:
        vals (list[float]): List of values.

    Returns:
        float: The mean.
    """
    return sum(vals) / len(vals)
