# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.


def mean(vals: list[float]) -> float:
    """Find mean of list of values.

    Args:
        vals (list[float]): List of values.

    Returns:
        float: The mean.
    """
    return sum(vals) / len(vals)
