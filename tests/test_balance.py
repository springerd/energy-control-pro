from custom_components.energy_control_pro.logic import calculate_balance


def test_calculate_balance_export_case() -> None:
    result = calculate_balance(solar_w=4200, load_w=1800)

    assert result["surplus_w"] == 2400
    assert result["grid_import_w"] == 0
    assert result["grid_export_w"] == 2400


def test_calculate_balance_import_case() -> None:
    result = calculate_balance(solar_w=900, load_w=2300)

    assert result["surplus_w"] == -1400
    assert result["grid_import_w"] == 1400
    assert result["grid_export_w"] == 0


def test_calculate_balance_balanced_case() -> None:
    result = calculate_balance(solar_w=1500, load_w=1500)

    assert result["surplus_w"] == 0
    assert result["grid_import_w"] == 0
    assert result["grid_export_w"] == 0
