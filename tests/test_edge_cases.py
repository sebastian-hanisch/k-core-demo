"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 0, 1, 2, isolierte Knoten, Gleichstände, inklusive Grenzen."""

import pytest

import kco_algorithm as A
import kco_scenario as S
from conftest import adj_from_edges


def test_empty_graph():
    adj = adj_from_edges(0, [])
    b = A.core_numbers_bucket(adj)
    assert b.core == () and b.steps == 0 and b.order == ()
    nv = A.core_numbers_naive(adj)
    assert nv.core == () and nv.steps == 0 and nv.passes == 0 and nv.log == ()
    assert A.shell_sizes(()) == {} and A.degeneracy(()) == 0 and A.clique_upper_bound(()) == 1
    assert A.max_clique_size(adj) == 0
    assert A.closeness(adj) == [] and A.betweenness(adj) == [] and A.pagerank(adj) == []
    assert A.mean_field_threshold(adj, 0.3) is None


def test_single_node():
    adj = adj_from_edges(1, [])
    b = A.core_numbers_bucket(adj)
    assert b.core == (0,) and b.steps == 2                     # 2n + 2m = 2
    nv = A.core_numbers_naive(adj)
    assert nv.core == (0,) and nv.steps == 1 and nv.passes == 1
    assert A.closeness(adj) == [0.0] and A.betweenness(adj) == [0.0] and A.pagerank(adj) == pytest.approx([1.0])
    assert A.max_clique_size(adj) == 1


def test_exactly_two_nodes_with_one_edge():
    """n = 2: der kleinste Fall mit einer Kante. Bucket 2 * 2 + 2 * 1 = 6 Schritte; naiv: k = 1 zwei Prüfungen ohne Entfernung, k = 2 zwei Prüfungen und zwei
    Nachbarschaftsdurchläufe (2 + 2 + 2 = 6 Schritte, zwei Durchläufe mit k = 1 und k = 2)."""
    adj = adj_from_edges(2, [(0, 1)])
    assert A.core_numbers_bucket(adj).core == (1, 1) and A.core_numbers_bucket(adj).steps == 6
    nv = A.core_numbers_naive(adj)
    assert nv.core == (1, 1) and nv.steps == 6 and nv.passes == 2
    assert [(e.k, e.durchlauf, e.entfernt) for e in nv.log] == [(1, 1, ()), (2, 1, (0, 1))]
    assert A.max_clique_size(adj) == 2 and A.clique_upper_bound((1, 1)) == 2
    assert A.closeness(adj) == pytest.approx([1.0, 1.0])
    assert A.mean_field_threshold(adj, 0.3) == pytest.approx(0.3)      # <k> = 1, <k^2> = 1


def test_isolated_nodes_have_core_zero_and_fall_in_the_first_pass():
    adj = adj_from_edges(5, [(0, 1)])
    nv = A.core_numbers_naive(adj)
    assert nv.core == (1, 1, 0, 0, 0)
    assert nv.log[0].entfernt == (2, 3, 4)


def test_complete_graph_has_a_single_shell():
    adj = adj_from_edges(6, [(i, j) for i in range(6) for j in range(i + 1, 6)])
    assert A.shell_sizes(A.core_numbers_bucket(adj).core) == {5: 6}
    assert A.clique_upper_bound((5,) * 6) == 6 and A.max_clique_size(adj) == 6


def test_rank_correlation_edge_cases():
    assert A.rank_correlation([], []) is None
    assert A.rank_correlation([1, 2], [1, 2]) == pytest.approx(1.0)       # genau zwei Werte reichen
    assert A.rank_correlation([1, 2, 3], [1, 2]) is None                  # ungleiche Längen


def test_topk_with_k_equal_to_n_is_the_mean_of_all_scores():
    assert A.topk_expected([1, 2, 3], [4.0, 5.0, 9.0], 3) == pytest.approx(6.0)
    assert A.topk_expected([1, 2, 3], [4.0, 5.0, 9.0], 1) == pytest.approx(9.0)


def test_ties_in_the_peeling_follow_ascending_node_numbers():
    """Der naive Durchlauf geht die Knoten in aufsteigender Nummer durch: ein Pfad 0-1-2 entfernt in k = 2 erst 0, dann (Grad gesunken) 1 im selben Durchlauf, 2 zuletzt."""
    adj = adj_from_edges(3, [(0, 1), (1, 2)])
    nv = A.core_numbers_naive(adj)
    assert nv.core == (1, 1, 1)
    assert nv.log[-1].k == 2 and nv.log[-1].entfernt == (0, 1, 2)


def test_spread_power_of_an_edgeless_graph_is_one_everywhere():
    adj = adj_from_edges(4, [])
    r = A.sir_spread_power(adj, 0.5, 0.3, 4, 1)
    assert r.power == (1.0, 1.0, 1.0, 1.0)
    assert r.reliability is None                  # alle gleich: Rangkorrelation nicht definiert


def test_honest_oracle_can_pick_the_last_node():
    """Mutationsfund: die Auswahl darf den letzten Knoten nicht übergehen (Bewertung auf der Gegenhälfte: 5, nicht 0)."""
    assert A.honest_oracle([1, 2, 9], [0, 0, 5], 1) == pytest.approx(5.0)


def test_shell_sizes_are_listed_in_ascending_core_number():
    """Mutationsfund: die Reihenfolge der Schalen bestimmt die Reihenfolge der Tabelle in der App, nicht nur den Inhalt des Dictionaries."""
    assert list(A.shell_sizes((3, 1, 2, 1, 0, 3))) == [0, 1, 2, 3]


def test_check_graph_rejects_neighbour_indices_outside_the_range():
    """Mutationsfund: Nachbar == n (zu groß) und Nachbar -1 (negativ, würde als letzter Knoten gelesen) sind ungültig, beide als ValueError."""
    for bad in (((2,), ()), ((-1,), (0,)), ((-1, 1), (0,))):     # der dritte Fall ist mit negativem Index scheinbar symmetrisch
        with pytest.raises(ValueError):
            A.check_graph(bad)


def test_clique_search_call_counts_are_pinned_on_small_graphs():
    """Aufrufzahl der Cliquensuche (Bron-Kerbosch mit Pivot): kleinstes Limit, bei dem das Ergebnis noch kommt. K3 von Hand: vier Aufrufe (Wurzel, Pivot 0, Pivot 1,
    Pivot 2, Blatt). Die übrigen Zahlen sind gepinnt: sie fangen Änderungen an Limit-Grenze, Schranke, Pivotwahl und Reihenfolge, die das Ergebnis nicht ändern."""
    pinned = {
        "K3": (adj_from_edges(3, [(0, 1), (0, 2), (1, 2)]), 3, 4),
        "Dreieck mit Anhänger": (adj_from_edges(4, [(0, 1), (1, 2), (0, 2), (2, 3)]), 3, 5),
        "Fünfeck": (adj_from_edges(5, [(i, (i + 1) % 5) for i in range(5)]), 2, 8),
        "Handbeispiel": (S.teach_instance().adj, 4, 14),                 # die Reihenfolge der Verzweigung ändert hier die Aufrufzahl (14 gegen 13)
    }
    for name, (adj, omega, calls) in pinned.items():
        assert A.max_clique_size(adj, call_limit=calls) == omega, name
        assert A.max_clique_size(adj, call_limit=calls - 1) is None, name


def test_sir_stops_after_max_steps():
    """Mutationsfund: Pfad mit fünf Knoten, beta = 1, mu = 0, Start an einem Ende: je Schritt kommt ein Knoten dazu; die Schrittgrenze gilt inklusive."""
    adj = adj_from_edges(5, [(0, 1), (1, 2), (2, 3), (3, 4)])
    assert A.sir_final_size(adj, 1.0, 0.0, 1, 0, max_steps=4) == 5
    assert A.sir_final_size(adj, 1.0, 0.0, 1, 0, max_steps=3) == 4
    assert A.sir_final_size(adj, 1.0, 0.0, 1, 0, max_steps=0) == 1
