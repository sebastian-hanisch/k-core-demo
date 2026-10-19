"""Generatoren und Handbeispiele: gültige Netze, Determinismus, bekannte Strukturen, Gegenbeispiel-Generator, echtes Link-Netz."""

import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

import kco_algorithm as A
import kco_constants as C
import kco_evaluation as ev
import kco_scenario as S

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("typ", C.ALL_TYPES)
@pytest.mark.parametrize("n,c", [(C.N_MIN, C.C_MIN), (77, 6), (C.N_MAX, C.C_MAX), (C.N_MIN, C.C_MAX), (C.N_MAX, C.C_MIN)])
def test_every_type_gives_a_valid_graph_with_valid_positions(typ, n, c):
    inst = S.make_instance(typ, n, c, 35)
    A.check_graph(inst.adj)
    assert len(inst.pos) == inst.n
    for x, y in inst.pos:
        assert math.isfinite(x) and math.isfinite(y) and -1e-9 <= x <= 1 + 1e-9 and -1e-9 <= y <= 1 + 1e-9


@pytest.mark.parametrize("typ", C.GENERATED_TYPES)
def test_generators_are_deterministic_per_seed_and_differ_between_seeds(typ):
    a = S.make_instance(typ, 80, 6, 5, layout=False)
    assert a.adj == S.make_instance(typ, 80, 6, 5, layout=False).adj
    if typ not in (C.T_GRID,):                                   # das Gitter ist deterministisch und kennt keinen Seed
        assert a.adj != S.make_instance(typ, 80, 6, 6, layout=False).adj


def test_the_grid_is_a_square_and_c_changes_its_neighbourhood():
    four = S.make_instance(C.T_GRID, 100, 4, 0, layout=False)
    tri = S.make_instance(C.T_GRID, 100, 6, 0, layout=False)
    king = S.make_instance(C.T_GRID, 100, 8, 0, layout=False)
    assert four.n == tri.n == king.n == 100
    assert (four.m, tri.m, king.m) == (180, 261, 342)             # 2 * 10 * 9, + 9 * 9 Diagonalen, + weitere 9 * 9
    assert max(len(a) for a in four.adj) == 4 and max(len(a) for a in tri.adj) == 6 and max(len(a) for a in king.adj) == 8


def test_barabasi_albert_has_core_number_m_everywhere():
    """Jeder neue Knoten bringt m Kanten zu früheren Knoten: Mindestgrad m, und das Entfernen in umgekehrter Reihenfolge zeigt Degeneracy m."""
    for c in (2, 4, 6, 12):
        m = max(1, round(c / 2))
        for seed in range(5):
            inst = S.make_instance(C.T_BA, 90, c, seed, layout=False)
            assert set(A.core_numbers_bucket(inst.adj).core) == {m}, (c, seed)
            assert inst.m == m * (m + 1) // 2 + m * (90 - m - 1)


def test_hubs_at_the_edge_have_high_degree_but_core_number_one():
    n = 120
    inst = S.make_instance(C.T_HUBS, n, 6, 35)
    core = A.core_numbers_bucket(inst.adj).core
    cores, hubs, ring, leaves = S.hubs_structure(n)
    assert (cores, hubs, ring, leaves) == (12, 5, 40, 63)
    assert inst.groups[:cores] == ("Kern",) * cores
    hub_ids = [v for v in range(n) if inst.groups[v] == "Hub"]
    assert len(hub_ids) == 5
    for h in hub_ids:
        assert core[h] == 1 and len(inst.adj[h]) >= 10          # hoher Grad, Kernzahl 1
    assert all(core[v] == 1 for v in range(n) if inst.groups[v] == "Blatt")
    assert max(core) >= 4                                         # der Kern ist dicht


def test_communities_keep_about_80_percent_of_the_edges_inside():
    n = 120
    inst = S.make_instance(C.T_COMMUNITIES, n, 6, 35, layout=False)
    group = S.communities_of(n)
    inside = sum(1 for u in range(n) for v in inst.adj[u] if u < v and group[u] == group[v])
    assert inside / inst.m == pytest.approx(0.8, abs=0.02)
    assert inst.m == 360


def test_power_law_network_has_a_heavy_tail_and_the_requested_mean_degree():
    inst = S.make_instance(C.T_POWER, 250, 6, 35, layout=False)
    deg = A.degrees(inst.adj)
    assert sum(deg) / len(deg) == pytest.approx(6, rel=0.35)
    assert max(deg) >= 3 * sum(deg) / len(deg)


def test_ring_has_at_least_the_lattice_degree():
    inst = S.make_instance(C.T_RING, 100, 6, 35, layout=False)
    assert min(len(a) for a in inst.adj) >= 6


def test_teaching_network_matches_the_hand_calculation(teach):
    assert teach.n == 10 and teach.m == 12 and teach.labels == tuple(str(i) for i in range(10))


def test_adversarial_path_makes_the_naive_peeling_quadratic():
    """Gegenbeispiel-Generator: er muss wirklich ein ungünstiger Pfad sein (ein erster Versuch war wirkungslos, weil die Umnummerierung die Pfadreihenfolge zurückstellte)."""
    ratios = []
    for n in (100, 200, 400):
        adj, pos = S.gen_path_adversarial(n)
        A.check_graph(adj)
        b, nv = A.core_numbers_bucket(adj), A.core_numbers_naive(adj)
        assert b.core == nv.core and set(b.core) == {1}
        assert nv.passes >= n // 2                                # je Durchlauf fallen nur die zwei Enden
        ratios.append(nv.steps / b.steps)
    assert ratios[0] > 5 and ratios[1] > 1.5 * ratios[0] and ratios[2] > 1.5 * ratios[1]    # der Faktor wächst mit n


def test_link_network_is_the_real_snapshot():
    inst = S.make_instance(C.T_LINK, 10, 2, 0)
    assert inst.n == 350 and inst.m == 2374
    assert sum(1 for g in inst.groups if g == "Seite") == 50 and sum(1 for g in inst.groups if g == "Demo") == 300
    assert S.link_stand() == "2026-09-30"
    data = json.loads((ROOT / "data" / "link_netz.json").read_text(encoding="utf-8"))
    assert len(data["namen"]) == 350 and len(data["kanten"]) == 2374 and data["stand"] == "2026-09-30"
    assert all(a < b for a, b in data["kanten"])                   # einfach, ohne Schleifen, jede Kante einmal


def test_force_layout_is_deterministic_and_handles_tiny_graphs():
    adj = S.teach_instance().adj
    assert S.layout_force(adj, 3) == S.layout_force(adj, 3)
    assert S.layout_force(((),), 1) == ((0.5, 0.5),)
    assert len(S.layout_force(((1,), (0,)), 1)) == 2


def test_unknown_type_is_rejected():
    with pytest.raises(ValueError):
        S.make_instance("gibt es nicht", 50, 6, 1)


def test_results_do_not_depend_on_the_hash_seed():
    """Dasselbe Szenario in zwei Prozessen mit verschiedenem PYTHONHASHSEED rechnet dasselbe (keine Iteration über Mengen, die das Ergebnis beeinflusst)."""
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "import kco_evaluation as ev, kco_constants as C\n"
        "out = []\n"
        "for t in (C.T_RANDOM, C.T_POWER, C.T_COMMUNITIES, C.T_HUBS, C.T_RING):\n"
        "    a = ev.analyse(ev.Settings(t, 60, 6, 7))\n"
        "    out.append((a.core, a.bucket.steps, a.naive.steps, a.omega))\n"
        "print(repr(out))\n"
    ) % str(ROOT)
    outputs = []
    for hash_seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONIOENCODING="utf-8")
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=120)
        assert proc.returncode == 0, proc.stderr
        outputs.append(proc.stdout)
    assert outputs[0] == outputs[1]


def test_fixed_types_ignore_n_and_c():
    """Die gesperrten Regler wirken wirklich nicht: gleiche Zahlen für verschiedene n, c und Seeds."""
    for typ in (C.T_TEACH, C.T_LINK):
        a = ev.analyse(ev.Settings(typ, 30, 2, 1))
        b = ev.analyse(ev.Settings(typ, 250, 12, 999))
        assert a.core == b.core and a.inst.adj == b.inst.adj
    p1 = ev.analyse(ev.Settings(C.T_PATH, 100, 2, 1))
    p2 = ev.analyse(ev.Settings(C.T_PATH, 100, 12, 999))
    assert p1.inst.adj == p2.inst.adj
