"""Kern gegen Handrechnung auf der Mini-Instanz (DEMO-PLAYBOOK §1b): je Einheit eine Aussage, von Hand gerechnet."""

import math

import pytest

import kco_algorithm as A
from conftest import adj_from_edges


def test_core_numbers_of_the_teaching_network_by_hand(teach):
    """Kernzahlen 2, 2, 2, 1, 1, 0, 3, 3, 3, 3 (siehe conftest); beide Verfahren liefern sie."""
    expected = (2, 2, 2, 1, 1, 0, 3, 3, 3, 3)
    assert A.core_numbers_bucket(teach.adj).core == expected
    assert A.core_numbers_naive(teach.adj).core == expected


def test_bucket_steps_are_exactly_2n_plus_2m(teach):
    """n = 10, m = 12: 2 * 10 + 2 * 12 = 44 Schritte."""
    assert A.core_numbers_bucket(teach.adj).steps == 44


def test_naive_peeling_log_and_steps_by_hand(teach):
    """Acht Durchläufe: k = 1: {5}, {}; k = 2: {4}, {3}, {}; k = 3: {0, 1, 2}, {}; k = 4: {6, 7, 8, 9}.
    Gradprüfungen 10 + 9 + 9 + 8 + 7 + 7 + 4 + 4 = 58, dazu 2m = 24 Gradabzüge: 82 Schritte."""
    r = A.core_numbers_naive(teach.adj)
    assert [(e.k, e.durchlauf, e.entfernt) for e in r.log] == [
        (1, 1, (5,)), (1, 2, ()), (2, 1, (4,)), (2, 2, (3,)), (2, 3, ()), (3, 1, (0, 1, 2)), (3, 2, ()), (4, 1, (6, 7, 8, 9)),
    ]
    assert r.passes == 8
    assert r.steps == 82


def test_removed_after_is_cumulative(teach):
    log = A.core_numbers_naive(teach.adj).log
    assert A.removed_after(log, 0) == frozenset()
    assert A.removed_after(log, 1) == {5}
    assert A.removed_after(log, 4) == {3, 4, 5}
    assert A.removed_after(log, len(log)) == frozenset(range(10))


def test_peeling_order_of_the_bucket_algorithm_is_a_degeneracy_order(teach):
    """Jeder Knoten hat zum Zeitpunkt seiner Entfernung höchstens seine Kernzahl viele noch nicht entfernte Nachbarn."""
    r = A.core_numbers_bucket(teach.adj)
    position = {v: i for i, v in enumerate(r.order)}
    assert sorted(r.order) == list(range(10))
    for v in range(10):
        later = sum(1 for u in teach.adj[v] if position[u] > position[v])
        assert later <= r.core[v]


def test_k_core_nodes_shells_degeneracy_and_clique_bound(teach):
    core = A.core_numbers_bucket(teach.adj).core
    assert A.k_core_nodes(core, 3) == [6, 7, 8, 9]
    assert A.k_core_nodes(core, 2) == [0, 1, 2, 6, 7, 8, 9]
    assert A.k_core_nodes(core, 4) == []
    assert A.shell_sizes(core) == {0: 1, 1: 2, 2: 3, 3: 4}
    assert A.degeneracy(core) == 3
    assert A.clique_upper_bound(core) == 4
    assert A.max_clique_size(teach.adj) == 4         # der vollständige Vierer


def test_validate_core_numbers_accepts_the_true_values_and_rejects_inflated_ones(teach):
    assert A.validate_core_numbers(teach.adj, (2, 2, 2, 1, 1, 0, 3, 3, 3, 3))
    assert not A.validate_core_numbers(teach.adj, (3, 2, 2, 1, 1, 0, 3, 3, 3, 3))   # Knoten 0 hat nur 2 Nachbarn
    assert not A.validate_core_numbers(teach.adj, (2, 2, 2, 2, 1, 0, 3, 3, 3, 3))   # Knoten 3 hat nur einen Nachbarn mit Kernzahl >= 2


def test_check_graph_rejects_malformed_graphs():
    A.check_graph(((1,), (0,)))
    for bad in (((0,),), ((1,), ()), ((2, 1), (0,), (0,)), ((1, 1), (0, 0))):
        with pytest.raises(ValueError):
            A.check_graph(bad)


# --- Maße -----------------------------------------------------------------------------------------------------------------------------------------


def test_measures_on_the_path_with_four_nodes():
    """Pfad 0-1-2-3: Grade 1,2,2,1; Nähe (r / Summe) * (r / (n - 1)): Enden 3/6 = 0,5, innen 3/4 = 0,75; Betweenness innen 2 (zwei Paare), außen 0."""
    adj = adj_from_edges(4, [(0, 1), (1, 2), (2, 3)])
    assert A.degrees(adj) == [1, 2, 2, 1]
    assert A.closeness(adj) == pytest.approx([0.5, 0.75, 0.75, 0.5])
    assert A.betweenness(adj) == pytest.approx([0.0, 2.0, 2.0, 0.0])


def test_measures_on_the_star_with_three_leaves():
    """Stern: Mitte hat Nähe 1,0 und Betweenness 3 (drei Blattpaare), Blätter Nähe 3/5 = 0,6 und Betweenness 0;
    PageRank (d = 0,85): Mitte 0,0375 * 3,55 / 0,2775 = 0,47973, Blatt 0,17342."""
    adj = adj_from_edges(4, [(0, 1), (0, 2), (0, 3)])
    assert A.closeness(adj) == pytest.approx([1.0, 0.6, 0.6, 0.6])
    assert A.betweenness(adj) == pytest.approx([3.0, 0.0, 0.0, 0.0])
    pr = A.pagerank(adj)
    assert pr[0] == pytest.approx(0.47973, rel=1e-4) and pr[1] == pytest.approx(0.17342, rel=1e-4)
    assert sum(pr) == pytest.approx(1.0)


def test_closeness_of_disconnected_nodes_follows_wasserman_faust():
    """Zwei Knoten verbunden, einer allein: r = 1 erreichbar, Summe 1: (1/1) * (1/2) = 0,5; der einzelne Knoten hat 0."""
    adj = adj_from_edges(3, [(0, 1)])
    assert A.closeness(adj) == pytest.approx([0.5, 0.5, 0.0])


def test_pagerank_gives_isolated_nodes_their_share():
    adj = adj_from_edges(3, [(0, 1)])
    pr = A.pagerank(adj)
    assert sum(pr) == pytest.approx(1.0) and pr[2] > 0 and pr[0] == pytest.approx(pr[1])


# --- Rangkorrelation, Top-k ------------------------------------------------------------------------------------------------------------------------


def test_average_ranks_with_ties():
    assert A.average_ranks([10, 20, 20, 30]) == [1.0, 2.5, 2.5, 4.0]
    assert A.average_ranks([5, 5, 5]) == [2.0, 2.0, 2.0]


def test_rank_correlation_by_hand():
    """Ohne Gleichstand: 1 - 6 * Summe d^2 / (n (n^2 - 1)) = 1 - 6 * 2 / 60 = 0,8. Mit Gleichstand: 1,5 / Wurzel(3) = 0,8660254."""
    assert A.rank_correlation([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(0.8)
    assert A.rank_correlation([1, 1, 2], [1, 2, 3]) == pytest.approx(1.5 / math.sqrt(3))
    assert A.rank_correlation([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)


def test_rank_correlation_is_undefined_for_constant_input():
    assert A.rank_correlation([2, 2, 2], [1, 2, 3]) is None
    assert A.rank_correlation([1, 2, 3], [4, 4, 4]) is None
    assert A.rank_correlation([1], [1]) is None


def test_topk_expected_averages_over_ties():
    """Werte 3, 3, 1, 1 mit Punkten 10, 20, 30, 40, k = 3: die zwei 3er (Mittel 15, zweimal = 30) plus ein Platz aus den 1ern (Mittel 35): 65 / 3."""
    assert A.topk_expected([3, 3, 1, 1], [10, 20, 30, 40], 3) == pytest.approx(65 / 3)
    assert A.topk_expected([3, 3, 1, 1], [10, 20, 30, 40], 1) == pytest.approx(15.0)
    assert A.topk_expected([5, 5, 5, 5], [10, 20, 30, 40], 2) == pytest.approx(25.0)   # alles gleich: Zufallswahl


def test_honest_oracle_selects_on_one_half_and_scores_on_the_other():
    assert A.honest_oracle([5, 5, 1], [3, 9, 7], 1) == pytest.approx(3.0)    # Gleichstand: kleinere Nummer, Bewertung 3 und nicht 9
    assert A.honest_oracle([5, 5, 1], [3, 9, 7], 2) == pytest.approx(6.0)
    assert A.honest_oracle([1, 9, 5], [0, 4, 2], 1) == pytest.approx(4.0)


# --- Ausbreitung -----------------------------------------------------------------------------------------------------------------------------------


def test_sir_extreme_probabilities(teach):
    """beta = 1, mu = 0 und beta = 1, mu = 1: die Endgröße ist die Größe der Komponente des Startknotens (9 oder 1); beta = 0: nur der Startknoten."""
    assert A.sir_final_size(teach.adj, 1.0, 0.0, 1, 0) == 9
    assert A.sir_final_size(teach.adj, 1.0, 1.0, 1, 0) == 9
    assert A.sir_final_size(teach.adj, 1.0, 0.3, 1, 5) == 1        # der einzelne Knoten steckt niemanden an
    assert A.sir_final_size(teach.adj, 0.0, 0.3, 1, 0) == 1


def test_sir_is_deterministic_per_seed(teach):
    runs = [A.sir_final_size(teach.adj, 0.3, 0.3, 123, 0) for _ in range(3)]
    assert len(set(runs)) == 1


def test_spread_power_halves_and_reliability(teach):
    """beta = 1, mu = 1: jeder Lauf ist deterministisch, die Ausbreitungskraft ist die Komponentengröße (9 für 9 Knoten, 1 für den einzelnen), beide Hälften sind gleich."""
    r = A.sir_spread_power(teach.adj, 1.0, 1.0, 4, 3)
    assert r.power == (9, 9, 9, 9, 9, 1, 9, 9, 9, 9)
    assert r.half_a == r.half_b
    assert r.reliability == pytest.approx(1.0)


def test_spread_runs_are_rounded_up_to_an_even_number(teach):
    assert A.sir_spread_power(teach.adj, 0.3, 0.3, 3, 1).runs == 4
    assert A.sir_spread_power(teach.adj, 0.3, 0.3, 4, 1).runs == 4


def test_mean_field_threshold_by_hand():
    """Pfad mit drei Knoten: Grade 1, 2, 1; <k> = 4/3, <k^2> = 2: beta_c = 0,3 * (4/3) / 2 = 0,2."""
    assert A.mean_field_threshold(adj_from_edges(3, [(0, 1), (1, 2)]), 0.3) == pytest.approx(0.2)
    assert A.mean_field_threshold(adj_from_edges(3, []), 0.3) is None


def test_max_clique_on_known_graphs():
    assert A.max_clique_size(adj_from_edges(5, [(i, j) for i in range(5) for j in range(i + 1, 5)])) == 5
    assert A.max_clique_size(adj_from_edges(5, [(i, (i + 1) % 5) for i in range(5)])) == 2     # Fünfeck
    assert A.max_clique_size(adj_from_edges(3, [])) == 1
    assert A.max_clique_size(adj_from_edges(0, [])) == 0
    assert A.max_clique_size(adj_from_edges(6, [(i, j) for i in range(6) for j in range(i + 1, 6)]), call_limit=2) is None   # Limit greift
