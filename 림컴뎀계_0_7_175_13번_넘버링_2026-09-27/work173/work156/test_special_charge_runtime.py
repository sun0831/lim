from special_charge_runtime_v1 import SpecialChargeBook


def test_special_charge_is_not_a_single_charge_axis():
    b = SpecialChargeBook()
    b.ensure("고유A").count = 3
    b.ensure("고유B", fixed_power=True).count = 4
    assert b.count_total() == 7
    assert b.count_non_fixed() == 3


def test_fixed_power_special_charge_does_not_become_charge_potency():
    b = SpecialChargeBook()
    b.ensure("고유A").potency = 5
    b.ensure("고유B", fixed_power=True).potency = 99
    assert b.potency_total() == 5


def test_named_special_charge_entries_are_independent():
    b = SpecialChargeBook()
    b.ensure("A").count = 2
    b.ensure("B").count = 7
    b.ensure("A").count += 1
    assert b.entries["A"].count == 3
    assert b.entries["B"].count == 7


def test_explicit_fixed_power_flag_is_preserved():
    b = SpecialChargeBook()
    b.ensure("A", fixed_power=True)
    b.ensure("A")
    assert b.entries["A"].fixed_power is True
