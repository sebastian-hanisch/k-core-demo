"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Preset-Button, fährt jeden Slider an seine
Grenzen, wählt jeden Netztyp, prüft Permalink, Abspielen und die Ausbreitungsmessung; es darf kein Python-Fehler auftreten (insbesondere keine doppelten
Plotly-Schlüssel und keine Slider mit min == max)."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import kco_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "▶"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_app_loads_without_exception():
    at = _fresh_app()
    assert _metric(at, "Knoten / Kanten") == "120 / 360"
    assert not at.error


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def test_all_sliders_at_their_minimum_and_all_at_their_maximum_do_not_raise():
    for edge in ("min", "max"):
        at = _fresh_app()
        for index in range(len(at.slider)):
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            slider.set_value(int(value) if isinstance(slider.value, int) else value)
        at.run(timeout=TIMEOUT)
        assert not at.exception, (edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("typ", C.ALL_TYPES)
def test_every_network_type_renders(typ):
    at = _fresh_app()
    at.selectbox(key="netztyp_select").set_value(typ).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    n = int(_metric(at, "Knoten / Kanten").split(" / ")[0])
    assert n == {C.T_TEACH: 10, C.T_LINK: 350}.get(typ, n) and n > 0


def test_fixed_networks_disable_the_controls_that_do_not_act():
    at = _fresh_app()
    at.selectbox(key="netztyp_select").set_value(C.T_LINK).run(timeout=TIMEOUT)
    assert at.slider(key="n_slider").proto.disabled and at.slider(key="c_slider").proto.disabled and at.number_input(key="seed_input").proto.disabled
    at.selectbox(key="netztyp_select").set_value(C.T_PATH).run(timeout=TIMEOUT)
    assert not at.slider(key="n_slider").proto.disabled and at.slider(key="c_slider").proto.disabled
    at.selectbox(key="netztyp_select").set_value(C.T_RANDOM).run(timeout=TIMEOUT)
    assert not at.slider(key="n_slider").proto.disabled and not at.slider(key="c_slider").proto.disabled and not at.number_input(key="seed_input").proto.disabled


def test_permalink_values_are_clamped_and_unknown_types_ignored():
    at = AppTest.from_file(APP_PATH)
    at.query_params["n"] = "5"
    at.query_params["c"] = "99"
    at.query_params["typ"] = "gibt es nicht"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert at.slider(key="n_slider").value == C.N_MIN and at.slider(key="c_slider").value == C.C_MAX
    assert at.selectbox(key="netztyp_select").value == C.T_RANDOM


def test_permalink_selects_a_network_type():
    at = AppTest.from_file(APP_PATH)
    at.query_params["typ"] = C.T_HUBS
    at.run(timeout=TIMEOUT)
    assert not at.exception and at.selectbox(key="netztyp_select").value == C.T_HUBS


def test_peel_step_slider_follows_the_network():
    at = _fresh_app()
    at.selectbox(key="netztyp_select").set_value(C.T_TEACH).run(timeout=TIMEOUT)
    step = at.slider(key="peel_step")
    assert (step.min, step.max) == (0, 8)                                # acht Durchläufe im Handbeispiel
    step.set_value(5).run(timeout=TIMEOUT)
    assert not at.exception
    assert any("Schwelle k = 2, Durchlauf 3: nichts fällt mehr, der 2-Kern steht (7 Knoten)" in c.value for c in at.caption)
    at.slider(key="peel_step").set_value(6).run(timeout=TIMEOUT)
    assert any("Schwelle k = 3, Durchlauf 1: 3 Knoten haben weniger als 3 Nachbarn und fallen (Kernzahl 2)" in c.value and "Übrig: 4" in c.value for c in at.caption)
    at.sidebar.button(key="preset_Zufallsnetz (Voreinstellung)").click().run(timeout=TIMEOUT)
    assert not at.exception and at.slider(key="peel_step").value == 0     # ein Preset setzt den Schritt zurück


def test_play_button_runs_through_the_frames_on_a_small_network():
    at = _fresh_app()
    at.selectbox(key="netztyp_select").set_value(C.T_TEACH).run(timeout=TIMEOUT)
    at.button(key="play_peel").click().run(timeout=TIMEOUT)
    assert not at.exception


def test_spread_measurement_runs_and_is_invalidated_by_a_setting_change():
    at = _fresh_app()
    at.selectbox(key="netztyp_select").set_value(C.T_HUBS).run(timeout=TIMEOUT)
    at.slider(key="n_slider").set_value(C.N_MIN).run(timeout=TIMEOUT)
    at.slider(key="runs").set_value(C.RUNS_MIN).run(timeout=TIMEOUT)
    at.button(key="spread_run").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert any(m.label == "Zuverlässigkeit der Messung" for m in at.metric)
    assert any("Rangkorrelation" in x.value for x in list(at.info) + list(at.success) + list(at.warning))
    at.slider(key="beta_factor").set_value(2.0).run(timeout=TIMEOUT)
    assert not at.exception
    assert any("neu starten" in i.value for i in at.info)                # Einstellungen geändert: das alte Ergebnis wird nicht gezeigt
    assert not any(m.label == "Zuverlässigkeit der Messung" for m in at.metric)


def test_link_network_shows_its_snapshot_stand():
    at = _fresh_app()
    at.sidebar.button(key="preset_Unser eigenes Link-Netz").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert any("2026-09-30" in i.value for i in at.info)
    assert _metric(at, "Höchste Kernzahl (Degeneracy)") == "48"
