FLOOD_STAGE = 30.0     # ft – minor flood stage (from plotting script)
MAJOR_FLOOD_STAGE = 40.0  # ft – major flood stage


def level_to_global_pf(level_ft: float) -> float:
    """
    Map predicted river level (ft) to a global flood severity in [0, 1].

    Intuition:
    - Well below flood stage  -> very low severity
    - Around flood stage      -> moderate severity (~0.5)
    - Near / above major      -> high severity (~1.0)
    """
    if level_ft <= FLOOD_STAGE - 2:
        return 0.05  # almost no risk
    if level_ft >= MAJOR_FLOOD_STAGE:
        return 1.0

    # Linear ramp between (FLOOD_STAGE - 2) and MAJOR_FLOOD_STAGE
    low = FLOOD_STAGE - 2
    high = MAJOR_FLOOD_STAGE
    return max(0.05, min(1.0, 0.05 + 0.95 * (level_ft - low) / (high - low)))
