"""Jede Zahl aus der README wird hier über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Netze der Messreihen: n = 120, c = 6 (Gitter in der Tabelle von Experiment 2: c = 6, also mit einer Diagonale), die fünf festen Netze SWEEP_SEEDS; Ausbreitung:
β = 3-fach der Mean-Field-Schwelle, 100 Läufe je Startknoten. Zufallszahlen laufen über `random.Random` mit festem Seed und sind plattformstabil;
Gleitkommazahlen werden mit Band geprüft."""

from functools import lru_cache
from statistics import median

import pytest

import kco_algorithm as A
import kco_constants as C
import kco_evaluation as ev
import kco_scenario as S


@lru_cache(maxsize=None)
def _analysis(typ, n=120, c=6, seed=35):
    return ev.analyse(ev.Settings(typ, n, c, seed))


@lru_cache(maxsize=None)
def _spread(typ, seed):
    return ev.spread_experiment(ev.Settings(typ, 120, 6, seed), 3.0, 100)


@lru_cache(maxsize=None)
def _steps():
    return ev.sweep_steps()


# --- E1: Schritte -------------------------------------------------------------------------------------------------------------------------------------


def test_bucket_steps_are_exactly_2n_plus_2m_on_every_measured_network():
    for typ in C.ALL_TYPES:
        a = _analysis(typ)
        assert a.bucket.steps == 2 * a.inst.n + 2 * a.inst.m, typ
    for r in _steps():
        if r["netztyp"] in (C.T_GRID, C.T_PATH):
            n = r["n"] if r["netztyp"] == C.T_PATH else round(r["n"] ** 0.5) ** 2
            m = (n - 1) if r["netztyp"] == C.T_PATH else 2 * round(r["n"] ** 0.5) * (round(r["n"] ** 0.5) - 1)
            assert r["bucket"] == 2 * n + 2 * m, r


def test_naive_peeling_costs_little_more_on_typical_networks_and_a_lot_on_the_adversarial_path():
    rows = {(r["netztyp"], r["n"]): r for r in _steps()}
    assert rows[(C.T_RANDOM, 1600)]["factor"] == pytest.approx(2.35, abs=0.05)
    assert rows[(C.T_BA, 1600)]["factor"] == pytest.approx(1.54, abs=0.05)
    assert rows[(C.T_GRID, 1600)]["factor"] == pytest.approx(1.17, abs=0.03)
    assert [round(rows[(C.T_PATH, n)]["factor"], 1) for n in (100, 400, 1600)] == [7.2, 25.9, 100.9]
    assert rows[(C.T_PATH, 1600)]["passes"] == 801


# --- Handbeispiel ------------------------------------------------------------------------------------------------------------------------------------


def test_teaching_network_numbers():
    a = _analysis(C.T_TEACH)
    assert a.core == (2, 2, 2, 1, 1, 0, 3, 3, 3, 3) and a.bucket.steps == 44 and a.naive.steps == 82 and a.naive.passes == 8
    assert a.shells == {0: 1, 1: 2, 2: 3, 3: 4} and a.omega == 4


# --- E2: Kernzahl gegen Grad -----------------------------------------------------------------------------------------------------------------------


def test_core_versus_degree_table_at_the_default_settings():
    rows = {r["netztyp"]: r for r in ev.sweep_types(ev.Settings())}
    expect = {
        C.T_RANDOM: (360, 5, 4, 100, 0.647, 22, 3, 2),
        C.T_POWER: (332, 4, 4, 31, 0.798, 40, 4, 1),
        C.T_BA: (354, 1, 3, 120, None, 35, 4, 0),
        C.T_COMMUNITIES: (360, 4, 4, 98, 0.648, 21, 4, 1),
        C.T_RING: (378, 1, 6, 120, None, 72, 5, 2),
        C.T_GRID: (320, 2, 3, 119, 0.269, 3, 3, 1),
        C.T_HUBS: (187, 5, 5, 10, 0.864, 86, 5, 1),
    }
    for typ, (m, shells, d, top, rho, equal, omega, gap) in expect.items():
        r = rows[typ]
        assert (r["m"], r["schalen"], r["degeneracy"], r["im_hoechsten_kern"], r["omega"], r["luecke"]) == (m, shells, d, top, omega, gap), typ
        assert round(100 * r["gleich"]) == equal, typ
        if rho is None:
            assert r["rho"] is None, typ
        else:
            assert r["rho"] == pytest.approx(rho, abs=0.002), typ


def test_constant_core_in_barabasi_albert_and_ring_on_all_five_networks_and_a_median_correlation_elsewhere():
    shells = {typ: [len(_analysis(typ, seed=s).shells) for s in C.SWEEP_SEEDS] for typ in C.GENERATED_TYPES}
    assert shells[C.T_BA] == [1] * 5 and shells[C.T_RING] == [1] * 5
    for typ in (C.T_RANDOM, C.T_POWER, C.T_COMMUNITIES, C.T_GRID, C.T_HUBS):
        assert min(shells[typ]) >= 2, typ
    med = {typ: median(_analysis(typ, seed=s).rho for s in C.SWEEP_SEEDS) for typ in (C.T_RANDOM, C.T_POWER, C.T_COMMUNITIES, C.T_GRID, C.T_HUBS)}
    assert med[C.T_RANDOM] == pytest.approx(0.67, abs=0.01) and med[C.T_POWER] == pytest.approx(0.86, abs=0.01)
    assert med[C.T_COMMUNITIES] == pytest.approx(0.62, abs=0.01) and med[C.T_GRID] == pytest.approx(0.27, abs=0.01)
    assert med[C.T_HUBS] == pytest.approx(0.86, abs=0.01)


def test_ba_core_is_exactly_m_and_the_clique_bound_is_tight_there():
    a = _analysis(C.T_BA)
    assert set(a.core) == {3} and a.omega == 4 == a.degeneracy + 1


def test_hubs_at_the_edge_have_core_number_one_and_a_high_degree():
    a = _analysis(C.T_HUBS)
    hubs = [v for v, g in enumerate(a.inst.groups) if g == "Hub"]
    assert [a.core[h] for h in hubs] == [1] * 5
    assert min(len(a.inst.adj[h]) for h in hubs) >= 12


# --- Link-Netz --------------------------------------------------------------------------------------------------------------------------------------


def test_link_network_numbers():
    a = _analysis(C.T_LINK)
    assert (a.inst.n, a.inst.m) == (350, 2374) and S.link_stand() == "2026-09-30"
    assert a.shells == {0: 1, 3: 121, 4: 95, 5: 51, 6: 16, 7: 14, 8: 2, 9: 1, 48: 49}
    assert a.degeneracy == 48 and a.omega == 49 and a.degeneracy + 1 == a.omega
    pages = [v for v, g in enumerate(a.inst.groups) if g == "Seite"]
    assert sorted(a.core[v] for v in pages).count(48) == 49 and a.core[[a.inst.labels[v] for v in pages].index("404.html")] == 0
    demos = [v for v, g in enumerate(a.inst.groups) if g == "Demo"]
    equal = [v for v in demos if a.core[v] == len(a.inst.adj[v])]
    assert len(equal) == 284                                              # 284 von 300 Demos: Kernzahl == Grad (Grad 3 bis 9)
    unequal = {a.inst.labels[v]: (len(a.inst.adj[v]), a.core[v]) for v in demos if v not in equal}
    assert len(unequal) == 16 and unequal["hill-climbing-demo"] == (16, 6)  # die Ausnahmen sind Demos mit vielen Demo-zu-Demo-Querverlinkungen
    assert a.rho == pytest.approx(0.998, abs=0.001)


# --- E3: Ausbreitung ---------------------------------------------------------------------------------------------------------------------------------


def _med_rho(typ, measure):
    vals = [_spread(typ, s).rho[measure] for s in C.SWEEP_SEEDS]
    return None if any(v is None for v in vals) else median(vals)


def test_spread_rank_correlation_medians():
    """Median über die fünf festen Netze je Netztyp (n = 120, c = 6, β = 3-fach β_c, 100 Läufe)."""
    expect = {  # Grad, Kernzahl, Nähe
        C.T_RANDOM: (0.89, 0.64, 0.89), C.T_POWER: (0.83, 0.80, 0.83), C.T_BA: (0.80, None, 0.81), C.T_COMMUNITIES: (0.86, 0.60, 0.76),
        C.T_RING: (0.37, None, 0.59), C.T_GRID: (0.70, 0.22, 0.86), C.T_HUBS: (0.87, 0.87, 0.82),
    }
    for typ, (grad, kern, close) in expect.items():
        assert _med_rho(typ, "Grad") == pytest.approx(grad, abs=0.011), typ
        assert _med_rho(typ, "Closeness") == pytest.approx(close, abs=0.011), typ
        if kern is None:
            assert _med_rho(typ, "Kernzahl") is None, typ
        else:
            assert _med_rho(typ, "Kernzahl") == pytest.approx(kern, abs=0.011), typ


def test_the_core_number_beats_the_degree_in_the_rank_correlation_only_in_the_core_periphery_nets():
    wins = {}
    for typ in C.GENERATED_TYPES:
        results = [_spread(typ, s) for s in C.SWEEP_SEEDS]
        if results[0].rho["Kernzahl"] is None:
            wins[typ] = None
        else:
            wins[typ] = sum(1 for r in results if r.rho["Kernzahl"] > r.rho["Grad"])
    assert wins == {C.T_RANDOM: 0, C.T_POWER: 2, C.T_BA: None, C.T_COMMUNITIES: 0, C.T_RING: None, C.T_GRID: 0, C.T_HUBS: 3}


def test_best_five_percent_by_core_number_are_worse_starters_than_by_degree_except_in_the_hub_network():
    for typ in C.GENERATED_TYPES:
        grad = median(_spread(typ, s).top["Grad"] for s in C.SWEEP_SEEDS)
        kern = median(_spread(typ, s).top["Kernzahl"] for s in C.SWEEP_SEEDS)
        if typ == C.T_HUBS:
            assert kern > grad + 3, typ
            assert (kern, grad) == (pytest.approx(24.4, abs=0.1), pytest.approx(19.7, abs=0.1))
        else:
            assert kern < grad, typ
    for s in C.SWEEP_SEEDS:                                       # konstantes Maß: die Auswahl ist die Zufallswahl (Erwartungswert über alle Gleichstände)
        r = _spread(C.T_BA, s)
        assert r.top["Kernzahl"] == pytest.approx(r.random)


def test_highest_median_rank_correlation_per_network_type():
    best = {}
    for typ in C.GENERATED_TYPES:
        med = {m: _med_rho(typ, m) for m in C.MEASURES}
        med = {m: v for m, v in med.items() if v is not None}
        best[typ] = max(med, key=med.get)
    counts = {m: sum(1 for b in best.values() if b == m) for m in C.MEASURES}
    assert counts == {"Grad": 2, "Kernzahl": 1, "Betweenness": 1, "PageRank": 0, "Closeness": 3}, best
    assert best == {C.T_RANDOM: "Closeness", C.T_POWER: "Grad", C.T_BA: "Closeness", C.T_COMMUNITIES: "Grad", C.T_RING: "Closeness", C.T_GRID: "Betweenness", C.T_HUBS: "Kernzahl"}
    assert (_med_rho(C.T_POWER, "Grad"), _med_rho(C.T_POWER, "Closeness")) == (pytest.approx(0.829, abs=0.002), pytest.approx(0.828, abs=0.002))   # praktisch gleichauf


def test_reliability_of_the_spread_measurement_is_stated_and_mostly_above_0_7():
    rel = {typ: median(_spread(typ, s).reliability for s in C.SWEEP_SEEDS) for typ in C.GENERATED_TYPES}
    assert rel[C.T_RING] < 0.4                                    # im Ring unterscheiden sich die Knoten kaum: die Messung ist dort unzuverlässig
    for typ in (C.T_RANDOM, C.T_POWER, C.T_BA, C.T_COMMUNITIES, C.T_GRID, C.T_HUBS):
        assert rel[typ] >= 0.69, typ
