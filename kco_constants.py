"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

# --- Netztypen -----------------------------------------------------------------------------------------------------------------------------------
T_RANDOM = "Zufallsnetz"
T_POWER = "Potenzgesetz-Netz"
T_BA = "Skalenfreies Netz (BA)"
T_COMMUNITIES = "Verbünde"
T_RING = "Ring mit Abkürzungen"
T_GRID = "Gitter"
T_HUBS = "Hubs am Rand"
T_TEACH = "Lehrbeispiel (10 Knoten)"
T_PATH = "Pfad (ungünstig nummeriert)"
T_LINK = "Link-Netz von sebastianhanisch.net"

GENERATED_TYPES = (T_RANDOM, T_POWER, T_BA, T_COMMUNITIES, T_RING, T_GRID, T_HUBS)  # n und c wirken
FIXED_TYPES = (T_TEACH, T_PATH, T_LINK)                                              # Handbeispiel, Gegenbeispiel, echtes Netz
ALL_TYPES = GENERATED_TYPES + FIXED_TYPES
N_FIXED_TYPES = (T_TEACH, T_LINK)   # Größe fest (n-Regler gesperrt); beim Pfad wirkt n
C_FIXED_TYPES = FIXED_TYPES         # c wirkt nur bei den erzeugten Netzen

C_MEANING = {
    T_RANDOM: "mittlerer Grad des Zufallsnetzes",
    T_POWER: "mittlerer Grad (Gradfolge mit Potenzgesetz-Exponent 2,5, Konfigurationsmodell)",
    T_BA: "zwei Kanten je neuem Knoten, also m = c / 2 gerundet (jeder Knoten hat mindestens m Nachbarn)",
    T_COMMUNITIES: "mittlerer Grad; 80 % der Kanten bleiben im eigenen Verbund (6 Verbünde)",
    T_RING: "Nachbarn auf dem Ring (c gerade gerundet), dazu Abkürzungen mit 5 % je Ringkante",
    T_GRID: "Nachbarschaft: unter 6 vier Nachbarn, 6 bis 7 mit einer Diagonale, ab 8 mit beiden Diagonalen",
    T_HUBS: "Kernkontakte je Randknoten (c / 3 gerundet, mindestens 2); der Rest sind Blätter an 5 Hubs",
}

N_MIN, N_MAX, DEFAULT_N = 30, 250, 120   # Slider-Maximum: Layout O(n^2 * 80), Closeness/Betweenness O(n * m), Ausbreitung O(n * Läufe * n)
C_MIN, C_MAX, DEFAULT_C = 2, 12, 6
SEED_MAX, DEFAULT_SEED = 999999, 35
SWEEP_SEEDS = tuple(range(100000, 100005))  # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund

# --- Ausbreitung (SIR-Regel wie kaskaden-demo) ---------------------------------------------------------------------------------------------------
MU = 0.3                       # Genesungswahrscheinlichkeit je Zeitschritt
SIR_MAX_STEPS = 200
BETA_FACTOR_MIN, BETA_FACTOR_MAX, DEFAULT_BETA_FACTOR = 1.0, 4.0, 3.0   # Vielfaches der Mean-Field-Schwelle
RUNS_MIN, RUNS_MAX, DEFAULT_RUNS = 20, 400, 100                           # Läufe je Startknoten (gerade: zwei Hälften)
TOP_FRACTION = 0.05            # Auswahl der besten 5 % der Knoten
MEASURES = ("Grad", "Kernzahl", "Betweenness", "PageRank", "Closeness")
SPREAD_SEED = 7

# --- Schritte-Experiment (E1) ---------------------------------------------------------------------------------------------------------------------
STEP_SIZES = (100, 400, 1600)

# --- Darstellung ---------------------------------------------------------------------------------------------------------------------------------
COLOR_REMOVED = "rgba(150,150,150,0.45)"
COLOR_EDGE = "rgba(120,120,120,0.30)"
COLOR_LINE = "#4c78a8"
COLOR_NAIVE = "#c4623b"
COLOR_BUCKET = "#2F6B65"
COLOR_ORACLE = "#6b5b95"
COLOR_RANDOM = "rgba(150,150,150,0.9)"
SHELL_SCALE = "Viridis"

PRESETS = {
    "Zufallsnetz (Voreinstellung)": {"netztyp": T_RANDOM, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED},
    "Lehrbeispiel zum Schälen": {"netztyp": T_TEACH, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED},
    "Hubs am Rand": {"netztyp": T_HUBS, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED},
    "Skalenfrei: Kernzahl konstant": {"netztyp": T_BA, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED},
    "Verbünde": {"netztyp": T_COMMUNITIES, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED},
    "Gitter": {"netztyp": T_GRID, "n": DEFAULT_N, "c": 4, "seed": DEFAULT_SEED},
    "Pfad: das naive Schälen kippt": {"netztyp": T_PATH, "n": 200, "c": DEFAULT_C, "seed": DEFAULT_SEED},
    "Unser eigenes Link-Netz": {"netztyp": T_LINK, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Zufallsnetz (Voreinstellung)": "120 Knoten, im Mittel 6 Nachbarn: mehrere Schalen, der Grad sagt fast dasselbe wie die Kernzahl.",
    "Lehrbeispiel zum Schälen": "Zehn Knoten von Hand: Dreieck mit zwei Anhängern, ein vollständiger Vierer, ein einzelner Knoten. Schritt für Schritt nachvollziehbar.",
    "Hubs am Rand": "Dichter Kern, dazu fünf Hubs mit vielen Blättern am Rand: hoher Grad, aber Kernzahl 1. Das Netz ist so gebaut, dass die Kernzahl gegen den Grad gewinnt.",
    "Skalenfrei: Kernzahl konstant": "Jeder neue Knoten bringt m Kanten mit: alle Knoten liegen im m-Kern, die Kernzahl ist überall gleich und sagt nichts.",
    "Verbünde": "Sechs dichte Gruppen mit wenigen Kanten dazwischen.",
    "Gitter": "Quadratisches Gitter mit vier Nachbarn: überall Kernzahl 2.",
    "Pfad: das naive Schälen kippt": "Ein Pfad, dessen Nummerierung gegen die Durchlaufreihenfolge läuft: das naive Schälen braucht quadratisch viele Schritte, der Bucket-Algorithmus linear viele.",
    "Unser eigenes Link-Netz": "Das echte Link-Netz von sebastianhanisch.net (Schnappschuss, 350 Knoten): 49 Seiten bilden den Kern, 284 der 300 Demos haben als Kernzahl genau ihren Grad.",
}
