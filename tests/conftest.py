"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import kco_scenario as S  # noqa: E402


def adj_from_edges(n, edges):
    return S._from_edges(n, edges)


@pytest.fixture
def teach():
    """Handbeispiel (10 Knoten): Dreieck {0,1,2}, Anhänger 3 und 4, einzelner Knoten 5, vollständiger Vierer {6,7,8,9} mit Kante 2-6.
    Handrechnung der Kernzahlen: 2, 2, 2, 1, 1, 0, 3, 3, 3, 3."""
    return S.teach_instance()
