"""Orakel-Tests k-core-demo (DEMO-PLAYBOOK §12): jede Kernroutine gegen einen anderen Rechenweg.

- Kernzahlen: networkx.core_number, Brute Force nach Definition (alle Knotenmengen, n <= 11), Familien mit bekanntem Wert, Eigenschaftstests
- Schrittzahlen: Bucket == 2n + 2m, naiv == Gradprüfungen + 2m (unabhängig neu gezählt)
- Maße: networkx (Nähe, Betweenness, PageRank), Cliquenzahl gegen find_cliques
- Rangkorrelation gegen scipy.stats.spearmanr (auch mit Gleichständen), Top-k gegen Aufzählung der Gleichstandsauflösungen
- SIR: eingefrorene Referenzwerte aus kaskaden-demo (sir_simulate, gleiche Regel), dazu Invarianten
"""

import itertools
import random

import pytest

import kco_algorithm as A
import kco_constants as C
import kco_scenario as S
from conftest import adj_from_edges

nx = pytest.importorskip("networkx")
scipy_stats = pytest.importorskip("scipy.stats")


def _nx_graph(adj):
    g = nx.Graph()
    g.add_nodes_from(range(len(adj)))
    g.add_edges_from((i, j) for i in range(len(adj)) for j in adj[i] if i < j)
    return g


def _instances(count_each=20):
    """Feste Zufalls-, Baum-, Gitter-, Verbund- und Sonderinstanzen; kleine Größen, damit Brute Force und networkx schnell sind."""
    rng = random.Random(11)
    out = []
    for _ in range(count_each):
        n = rng.randint(1, 11)
        out.append(adj_from_edges(n, [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < rng.choice([0.1, 0.25, 0.5, 0.8])]))
    for typ in C.GENERATED_TYPES:
        for seed in range(6):
            n = rng.randint(30, 60)
            out.append(S.make_instance(typ, n, rng.randint(C.C_MIN, C.C_MAX), seed, layout=False).adj)
    out.append(adj_from_edges(0, []))
    out.append(adj_from_edges(1, []))
    out.append(adj_from_edges(2, [(0, 1)]))
    out.append(adj_from_edges(7, []))                                                   # nur isolierte Knoten
    out.append(adj_from_edges(8, [(i, j) for i in range(8) for j in range(i + 1, 8)]))   # vollständig
    out.append(S.teach_instance().adj)
    return out


def test_core_numbers_match_networkx_on_many_instances():
    instances = _instances()
    assert len(instances) == 68                                  # so viele feste Instanzen nennt die README
    for adj in instances:
        expected = nx.core_number(_nx_graph(adj)) if len(adj) else {}
        want = tuple(expected[v] for v in range(len(adj)))
        assert A.core_numbers_bucket(adj).core == want
        assert A.core_numbers_naive(adj).core == want


def test_core_numbers_match_brute_force_by_definition():
    """k-Kern = Vereinigung aller Knotenmengen mit Mindestgrad >= k (die Vereinigung zweier solcher Mengen hat ebenfalls Mindestgrad >= k)."""
    rng = random.Random(3)
    for _ in range(30):
        n = rng.randint(1, 10)
        adj = adj_from_edges(n, [(i, j) for i in range(n) for j in range(i + 1, n) if rng.random() < 0.35])
        want = [0] * n
        for k in range(1, n):
            union = set()
            for mask in range(1, 1 << n):
                members = [v for v in range(n) if mask >> v & 1]
                inside = set(members)
                if all(sum(1 for u in adj[v] if u in inside) >= k for v in members):
                    union |= inside
            for v in union:
                want[v] = k
        assert list(A.core_numbers_bucket(adj).core) == want


@pytest.mark.parametrize("name,graph,expected", [
    ("Baum", nx.random_labeled_tree(40, seed=1), 1),
    ("Stern", nx.star_graph(20), 1),
    ("Pfad", nx.path_graph(15), 1),
    ("Kreis", nx.cycle_graph(12), 2),
    ("vollständig", nx.complete_graph(9), 8),
    ("Gitter", nx.grid_2d_graph(6, 6), 2),
    ("Rad", nx.wheel_graph(10), 3),
    ("Hyperwürfel Q4", nx.hypercube_graph(4), 4),
    ("Barbell", nx.barbell_graph(6, 0), 5),
])
def test_known_families_have_a_constant_core_number(name, graph, expected):
    g = nx.convert_node_labels_to_integers(graph)
    adj = adj_from_edges(len(g), list(g.edges()))
    assert set(A.core_numbers_bucket(adj).core) == {expected}, name


def test_steps_are_counted_independently():
    for adj in _instances():
        n, m = len(adj), sum(len(a) for a in adj) // 2
        assert A.core_numbers_bucket(adj).steps == 2 * n + 2 * m
        r = A.core_numbers_naive(adj)
        alive = n
        checks = 0
        for ev in r.log:
            checks += alive
            alive -= len(ev.entfernt)
        assert alive == 0
        assert r.steps == checks + 2 * m                       # jede Entfernung geht die Nachbarliste einmal durch
        assert r.passes == len(r.log)


def test_properties_of_core_numbers():
    for adj in _instances():
        core = A.core_numbers_bucket(adj).core
        assert A.validate_core_numbers(adj, core)
        assert all(0 <= c <= len(adj[v]) for v, c in enumerate(core))
        omega = A.max_clique_size(adj)
        assert omega <= A.clique_upper_bound(core)              # eine Clique der Größe s liegt im (s - 1)-Kern
        if len(adj) > 0:
            assert A.degeneracy(core) >= max(0, omega - 1)


def test_clique_number_matches_networkx():
    for adj in _instances():
        g = _nx_graph(adj)
        want = max((len(c) for c in nx.find_cliques(g)), default=0)
        assert A.max_clique_size(adj) == want


def test_measures_match_networkx():
    for adj in _instances(count_each=8):
        if len(adj) < 2:
            continue
        g = _nx_graph(adj)
        n = len(adj)
        assert A.closeness(adj) == pytest.approx([nx.closeness_centrality(g, u=v, wf_improved=True) for v in range(n)])
        bet = nx.betweenness_centrality(g, normalized=False)
        assert A.betweenness(adj) == pytest.approx([bet[v] for v in range(n)])
        pr = nx.pagerank(g, alpha=0.85, tol=1e-12, max_iter=1000)
        assert A.pagerank(adj) == pytest.approx([pr[v] for v in range(n)], abs=1e-9)


def test_rank_correlation_matches_scipy_with_ties():
    rng = random.Random(5)
    for _ in range(60):
        n = rng.randint(3, 30)
        x = [rng.randint(0, 6) for _ in range(n)]
        y = [rng.randint(0, 6) + rng.random() * rng.choice([0, 1]) for _ in range(n)]
        want = scipy_stats.spearmanr(x, y).statistic
        got = A.rank_correlation(x, y)
        if want != want:                                  # NaN: eine Seite konstant
            assert got is None
        else:
            assert got == pytest.approx(want, abs=1e-9)


def test_average_ranks_match_scipy():
    rng = random.Random(6)
    for _ in range(30):
        values = [rng.randint(0, 5) for _ in range(rng.randint(1, 25))]
        assert A.average_ranks(values) == pytest.approx(list(scipy_stats.rankdata(values, method="average")))


def test_topk_expected_matches_enumeration_of_tie_resolutions():
    """Erwartungswert über alle gleich wahrscheinlichen Auflösungen: jede Anordnung der Gleichstandsgruppen nach Permutation, die ersten k zählen."""
    rng = random.Random(7)
    for _ in range(40):
        n = rng.randint(2, 6)
        values = [rng.randint(0, 2) for _ in range(n)]
        score = [rng.randint(0, 9) for _ in range(n)]
        k = rng.randint(1, n)
        totals = []
        for perm in itertools.permutations(range(n)):
            order = sorted(range(n), key=lambda v: (-values[v], perm.index(v)))
            totals.append(sum(score[v] for v in order[:k]) / k)
        assert A.topk_expected(values, score, k) == pytest.approx(sum(totals) / len(totals))


# --- SIR gegen eingefrorene Referenzwerte aus kaskaden-demo ---------------------------------------------------------------------------------------------

CIRC20 = sorted({(min(i, (i + d) % 20), max(i, (i + d) % 20)) for i in range(20) for d in (1, 3)})
# (beta, run_seed, patient_zero, Endgröße), mit kas_algorithm.sir_simulate aus kaskaden-demo erzeugt (mu = 0,3)
CIRC20_REFERENCE = [(0.6, 391445, 14, 20), (0.1, 195187, 8, 1), (0.3, 527205, 0, 19), (0.6, 84740, 14, 20), (0.6, 981871, 10, 20),
                    (0.6, 42882, 19, 20), (0.1, 737652, 12, 2), (0.6, 443114, 14, 20), (0.1, 249573, 5, 8), (0.1, 138858, 1, 5),
                    (0.6, 66403, 16, 20), (0.6, 930363, 12, 20), (0.3, 214916, 3, 20), (0.6, 831516, 7, 20)]
TEACH_REFERENCE = [(0.1, 810109, 6, 1), (0.1, 415805, 4, 1), (0.3, 848833, 4, 8), (0.1, 743231, 0, 3), (0.3, 57450, 0, 1), (0.3, 145901, 6, 4),
                   (0.1, 445356, 0, 3), (0.6, 4062, 1, 9), (0.6, 207272, 1, 2), (0.3, 8653, 3, 2), (0.1, 565989, 1, 1), (0.6, 88957, 0, 8),
                   (0.3, 563701, 9, 7), (0.3, 72163, 3, 2)]


def test_sir_matches_the_reference_runs_of_kaskaden_demo(teach):
    circ = adj_from_edges(20, CIRC20)
    for beta, seed, p0, expected in CIRC20_REFERENCE:
        assert A.sir_final_size(circ, beta, 0.3, seed, p0) == expected, (beta, seed, p0)
    for beta, seed, p0, expected in TEACH_REFERENCE:
        assert A.sir_final_size(teach.adj, beta, 0.3, seed, p0) == expected, (beta, seed, p0)


def test_sir_final_size_is_between_one_and_the_component_size():
    for adj in _instances(count_each=6):
        if not adj:
            continue
        g = _nx_graph(adj)
        comp = {v: len(nx.node_connected_component(g, v)) for v in range(len(adj))}
        for v in range(0, len(adj), max(1, len(adj) // 6)):
            for seed in range(3):
                size = A.sir_final_size(adj, 0.4, 0.3, seed, v)
                assert 1 <= size <= comp[v]
        assert A.sir_final_size(adj, 1.0, 0.0, 1, 0) == comp[0]


def test_spread_power_is_the_mean_of_the_two_halves():
    teach = S.teach_instance()
    r = A.sir_spread_power(teach.adj, 0.4, 0.3, 10, 4)
    for p, a, b in zip(r.power, r.half_a, r.half_b):
        assert p == pytest.approx((a + b) / 2)
