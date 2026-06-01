import pandas as pd

from riskmodeler.func import binning
from riskmodeler.model import lrmodel


def test_group_variable_helpers_work_together():
    model = lrmodel()
    variable_df = pd.DataFrame(
        [
            {"variable": "f_group_age", "list": ["f_group_age_0", "f_group_age_1"]},
            {"variable": "f_group_income", "list": ["f_group_income_0", "f_group_income_1"]},
        ]
    )

    selected = ["f_group_age"]
    selected_variables = model._group_selected_variables(variable_df, selected)
    remaining_variables = model._group_remaining_variables(
        selected_variables + ["f_group_income_0"],
        ["f_group_age_1"],
    )

    assert selected_variables == ["f_group_age_0", "f_group_age_1"]
    assert set(remaining_variables) == {"f_group_age_0", "f_group_income_0"}


def test_criterion_score_flips_llr_only():
    model = lrmodel()

    class DummyResult:
        llr = 12.5
        aic = 101.2

    result = DummyResult()

    assert model._criterion_score(result, "llr") == -12.5
    assert model._criterion_score(result, "aic") == 101.2


def test_build_group_variable_metadata_creates_dummy_columns():
    model = lrmodel()
    df = pd.DataFrame(
        {
            "f_group_age": [0, 1, 1, 2],
            "f_group_income": [3, 3, 4, 4],
        }
    )

    group_varlist, variable_df, match_df = model._build_group_variable_metadata(df, ["age", "income"])

    assert group_varlist == ["f_group_age", "f_group_income"]
    assert "f_group_age_0" in df.columns
    assert "f_group_income_3" in df.columns
    assert set(variable_df["variable"]) == {"f_group_age", "f_group_income"}
    assert set(match_df["ori_var"]) == {"age", "income"}


def test_restrict_candidate_variables_removes_constant_columns():
    model = lrmodel()
    df = pd.DataFrame(
        {
            "var_a": [1, 1, 1, 1],
            "var_b": [0, 1, 0, 1],
            "var_c": [1, 2, 3, 4],
        }
    )
    record_list = []

    filtered = model._restrict_candidate_variables(df, ["var_a", "var_b", "var_c"], True, record_list)

    assert "var_a" not in filtered
    assert set(filtered) == {"var_b", "var_c"}
    assert len(record_list) == 2


def test_normalize_min_samples_leaf_never_returns_zero():
    assert binning.normalize_min_samples_leaf(0) == 1
    assert binning.normalize_min_samples_leaf(-3) == 1
    assert binning.normalize_min_samples_leaf(2) == 2
