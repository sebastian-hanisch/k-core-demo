"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Sweeps über die festen Instanzen."""

import kco_constants as C
import kco_evaluation as ev
import kco_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, preset in C.PRESETS.items():
        assert preset["netztyp"] in C.ALL_TYPES, name
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.C_MIN <= preset["c"] <= C.C_MAX and 0 <= preset["seed"] <= C.SEED_MAX, name


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Zufallsnetz (Voreinstellung)"]) == ev.Settings()
    assert next(iter(C.PRESETS)) == "Zufallsnetz (Voreinstellung)"


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_network_type_is_reachable_and_the_presets_cover_every_type_family():
    assert set(C.ALL_TYPES) == set(C.GENERATED_TYPES) | set(C.FIXED_TYPES)
    used = {p["netztyp"] for p in C.PRESETS.values()}
    assert {C.T_TEACH, C.T_LINK, C.T_PATH, C.T_BA, C.T_HUBS, C.T_RANDOM} <= used


def test_every_generated_type_explains_what_c_means():
    for typ in C.GENERATED_TYPES:
        assert C.C_MEANING[typ]


def test_slider_maximum_keeps_the_worst_case_cheap_enough():
    """Worst-Case-Test am Slider-Maximum (Timeout statt Zeit-Assertion): größtes Netz, dichtester Fall, alle Auswertungen."""
    for typ in C.GENERATED_TYPES:
        a = ev.analyse(ev.Settings(typ, C.N_MAX, C.C_MAX, 1))
        assert a.valid and a.inst.n >= C.N_MAX - 20
