"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import dataclasses

import kco_constants as C
import kco_evaluation as ev


def _analysis(shells=None, rho=0.5, share=0.25):
    a = ev.analyse(ev.Settings(C.T_TEACH))                       # 10 Knoten, 4 Schalen, Degeneracy 3
    return dataclasses.replace(a, shells=shells if shells is not None else a.shells, rho=rho, share_equal=share)


def test_de_uses_a_decimal_comma():
    assert ev.de(1.26, 1) == "1,3"
    assert ev.de(0.9487, 3) == "0,949" and ev.de(3, 0) == "3"


def test_information_verdict_constant_core_is_a_warning():
    kind, text = ev.verdict_information(_analysis(shells={3: 10}))
    assert kind == "warning" and "Alle 10 Knoten haben dieselbe Kernzahl 3" in text and "keine Information" in text


def test_information_verdict_threshold_is_inclusive_at_095():
    assert ev.verdict_information(_analysis(rho=0.95))[0] == "info"
    kind, text = ev.verdict_information(_analysis(rho=0.949, share=0.5))
    assert kind == "success" and "Rangkorrelation 0,949" in text and "nur bei 50 % der Knoten" in text
    assert "4 Schalen" in text and "(3-Kern) enthält 4 von 10 Knoten" in text           # Handbeispiel: der 3-Kern hat 4 Knoten


def test_information_verdict_names_correlation_and_share_when_similar():
    kind, text = ev.verdict_information(_analysis(rho=0.97, share=0.8))
    assert kind == "info" and "Rangkorrelation 0,970" in text and "bei 80 % der Knoten" in text and "kaum etwas Neues" in text


def test_information_verdict_without_correlation_is_info():
    kind, text = ev.verdict_information(_analysis(rho=None))
    assert kind == "info" and "Grade sind alle gleich" in text


def _rows():
    def row(t, n, f, passes=10):
        return {"netztyp": t, "n": n, "factor": f, "passes": passes, "bucket": 1, "naive": f}
    return [row(C.T_RANDOM, 100, 1.8), row(C.T_RANDOM, 1600, 2.34), row(C.T_BA, 1600, 1.54), row(C.T_GRID, 1600, 1.17), row(C.T_PATH, 1600, 100.9, 801)]


def test_steps_verdict_names_range_and_path_factor_at_the_largest_size():
    kind, text = ev.verdict_steps(_rows())
    assert kind == "info"
    assert "Bei n = 1600" in text and "das 1,2- bis 2,3-fache" in text and "**101-fache** (801 Durchläufe)" in text


def test_steps_verdict_without_path_says_so():
    kind, text = ev.verdict_steps([r for r in _rows() if r["netztyp"] != C.T_PATH])
    assert kind == "info" and "fehlen" in text


def _type_rows(shells):
    return [{"netztyp": t, "schalen": s} for t, s in zip(C.GENERATED_TYPES, shells)]


def test_types_verdict_counts_constant_types():
    kind, text = ev.verdict_types(_type_rows([5, 4, 1, 4, 1, 2, 5]))
    assert kind == "warning" and "**2 von 7**" in text and f"{C.T_BA}, {C.T_RING}" in text
    kind, text = ev.verdict_types(_type_rows([5, 4, 3, 4, 2, 2, 5]))
    assert kind == "success" and "In allen 7 Netztypen" in text


def _spread(rho_core=0.6, rho_grad=0.9, top_core=70.0, top_grad=80.0, reliability=0.73):
    rho = {"Grad": rho_grad, "Kernzahl": rho_core, "Betweenness": 0.84, "PageRank": 0.87, "Closeness": 0.88}
    top = {"Grad": top_grad, "Kernzahl": top_core, "Betweenness": 77.5, "PageRank": 79.0, "Closeness": 79.5}
    return ev.SpreadExperiment(0.1, 0.03, 100, 6, 40.0, reliability, rho, top, 76.0, 38.0)


def test_spread_verdict_for_a_weak_core_measure_is_info_with_rank_and_numbers():
    kind, text = ev.verdict_spread(_spread())
    assert kind == "info"
    assert "Rangkorrelation 0,60" in text and "Platz 5 von 5" in text and "der Grad 0,90" in text and "am besten Grad mit 0,90" in text
    assert "Die besten 6 Starter nach Kernzahl erreichen im Mittel 70,0 Knoten, nach Grad 80,0, am besten Grad mit 80,0" in text
    assert "Zuverlässigkeit der Messung: 0,73" in text and "Zufallswahl 38,0" in text and "Auswahl nach den Messläufen 76,0" in text


def test_spread_verdict_is_success_when_the_core_measure_has_the_best_correlation():
    kind, text = ev.verdict_spread(_spread(rho_core=0.95, rho_grad=0.9))
    assert kind == "success" and "Platz 1 von 5" in text and "am besten Kernzahl mit 0,95" in text


def test_spread_verdict_for_a_constant_core_measure_is_a_warning():
    r = _spread()
    r = dataclasses.replace(r, rho={**r.rho, "Kernzahl": None}, top={**r.top, "Kernzahl": 38.0})
    kind, text = ev.verdict_spread(r)
    assert kind == "warning" and "konstant" in text and "(38,0)" in text and "Beste Rangkorrelation: Closeness (0,90)" not in text
    assert "Beste Rangkorrelation: Grad (0,90)" in text


def test_spread_verdict_handles_an_unknown_reliability():
    kind, text = ev.verdict_spread(_spread(reliability=None))
    assert "Zuverlässigkeit der Messung: unbestimmt" in text
