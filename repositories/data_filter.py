from __future__ import annotations


def build_data_filter(
    column_name: str,
    tiers: list[str | None],
    selected_models: list[str] | None = None,
) -> tuple[str, list[str]]:
    """
    column_name: TIER hoặc data.TIER.

    Không chọn Tier: không trả dữ liệu.
    Không chọn Model: không trả dữ liệu.
    """

    normal_tiers = [
        str(tier)
        for tier in tiers
        if tier is not None
    ]

    if not normal_tiers:
        return "AND 0 = 1", []

    placeholders = ", ".join(
        "?" for _ in normal_tiers
    )

    sql = (
        f"AND {column_name} "
        f"IN ({placeholders})"
    )

    params = list(normal_tiers)

    models = sorted(
        set(selected_models or [])
    )

    #  Không chọn Model: không trả dữ liệu.
    if not models:
        return "AND 0 = 1", []

    if models:
        # TIER -> MODEL
        # data.TIER -> data.MODEL
        prefix = column_name.rpartition(".")[0]

        model_column = (
            f"{prefix}.MODEL"
            if prefix
            else "MODEL"
        )

        placeholders = ", ".join(
            "?" for _ in models
        )

        sql += (
            f" AND {model_column} "
            f"IN ({placeholders})"
        )

        params.extend(models)

    return sql, params