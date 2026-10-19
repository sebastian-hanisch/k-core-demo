# k-Core: Kernzahl und Schälen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-k-core-demo.streamlit.app/)** -->

Erstes Stück der **Netzwerkanalyse-Reihe** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, Wurzel des Struktur-Arms. Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt die Demo **ein** Verfahren an einem wachsenden Beispiel: die **k-Kern-Zerlegung** eines Netzes von Subunternehmern und Lieferanten (synthetisch; dazu das echte Link-Netz von sebastianhanisch.net). In der [Demo zur größten Clique](https://sebastianhanisch-max-clique-demo.streamlit.app/) war die Kernzahl nur ein Werkzeug (Kernzahl-Beschneidung, Startordnung nach Degeneracy); hier ist sie das Thema. Die Ausbreitung nutzt die SIR-Regel der [Demo zu Kaskaden und Ausbreitung](https://sebastianhanisch-kaskaden-demo.streamlit.app/), die Maße Grad, Nähe, Betweenness und PageRank kennt die [Zentralitäts-Demo](https://sebastianhanisch-centrality-demo.streamlit.app/).

Beim **Schälen** werden wiederholt alle Knoten mit weniger als *k* Nachbarn entfernt; was bleibt, ist der **k-Kern**, die **Kernzahl** eines Knotens ist das größte *k*, in dessen Kern er liegt, und die **Degeneracy** ist die größte Kernzahl. Zwei Verfahren stehen nebeneinander: das **naive Schälen** (die Definition, mit Durchläufen, die sich Schritt für Schritt abspielen lassen) und der **Bucket-Algorithmus** von Batagelj und Zaveršnik mit genau 2n + 2m Schritten.

## Kernfrage

**Wann trägt die Kernzahl Information, die der Grad nicht schon hat, und was sagt die Ausbreitung wirklich voraus?** In der Literatur gilt die Kernzahl als guter Hinweis auf die Ausbreitungskraft eines Knotens (Kitsak u. a. 2010). Die Demo prüft das an Modellnetzen und am Link-Netz dieser Website, statt es vorauszusetzen.

## Befunde und Korrekturen gegenüber dem Plan

- **Kernfrage umgestellt (Nutzerentscheidung 2026-10-19).** Der Gesamtplan fragte, ob die Kernzahl die Ausbreitung besser vorhersagt als der Grad (Kitsak u. a.). Die Vormessung (n ≈ 250) und die endgültigen Messreihen (n = 120) bestätigen das an diesen Netzen nicht; die Kernfrage lautet deshalb: *Wann trägt die Kernzahl Information, und was sagt die Ausbreitung wirklich voraus?* Das widerlegt Kitsak u. a. nicht (deren Netze waren groß und echt, ihre Ausbreitung lief anders ab, und sie untersuchten auch mehrere gleichzeitige Starter und deren Abstand), es zeigt nur, wann der Befund **nicht** auf kleine Modellnetze übergeht.
- **Vergleichswert ehrlicher.** Die Vormessung wählte ein „Orakel“ (die nach der Messung besten Knoten) in derselben Stichprobe, in der sie es bewertete; es war nach oben verzerrt. In der Demo wird die **Auswahl nach den Messläufen** auf einer Hälfte der Läufe gewählt und auf der anderen bewertet. Sie ist verrauscht und kann von einem guten Maß übertroffen werden, deshalb nennt die Demo keinen „Anteil am Orakel“ mehr.
- **Zu schwache Messung korrigiert.** Mit 40 Läufen je Startknoten war die Rangfolge der Startknoten kaum reproduzierbar (Rangkorrelation zweier Hälften 0,3 bis 0,7); die Demo misst mit 100 oder mehr Läufen und zeigt die Zuverlässigkeit neben jedem Ergebnis an.
- **Frühere Fehlaussage über das Link-Netz.** Ein Zwischenstand des Plans behauptete, jede Demo habe als Kernzahl genau ihren Grad. Der Claims-Test fand 16 Ausnahmen (284 von 300 Demos); die Zahlen unten sind die richtigen.
- **Gegenbeispiel-Generator geprüft.** Der erste Pfad mit „ungünstiger Nummerierung“ war wirkungslos, weil das Umnummerieren die Pfadreihenfolge wiederherstellte (Faktor 1,0). Ein Test stellt jetzt sicher, dass der Pfad das naive Schälen wirklich quadratisch macht.
- **Nicht in der Demo:** die in der Vormessung auch gemessene gerichtete Fassung des Link-Netzes (Ausbreitung nur entlang der Link-Richtung). Die Demo rechnet ungerichtet; Aussagen zur gerichteten Fassung stehen deshalb nicht in der Demo und nicht in dieser README.

## Modell

Einfache ungerichtete Graphen (keine Schleifen, keine Mehrfachkanten). Der **k-Kern** ist der größte Teilgraph mit Mindestgrad *k*; es gilt ω ≤ Degeneracy + 1 (eine Clique der Größe *s* liegt im (*s* − 1)-Kern). Netztypen der Demo: Zufallsnetz G(n, m), Konfigurationsmodell mit Potenzgesetz-Gradfolge (Exponent 2,5), bevorzugte Anbindung (Barabási-Albert, Start mit vollständigem Graphen auf m + 1 Knoten), sechs Verbünde (80 % der Kanten innen), Ring mit Abkürzungen, Gitter, „Hubs am Rand“ (Konstruktion), dazu Handbeispiel, Pfad-Gegenbeispiel und das echte Link-Netz (Schnappschuss, ungerichtet zusammengefasst). **Ausbreitungskraft** eines Knotens = mittlere Endgröße eines SIR-Laufs, der bei ihm beginnt (diskrete Zeit, μ = 0,3, β als Vielfaches der Mean-Field-Schwelle β_c = μ·⟨k⟩/⟨k²⟩), verglichen mit Grad, Kernzahl, Betweenness (Brandes), PageRank und Nähe über die Spearman-Rangkorrelation und die mittlere Ausbreitungskraft der besten 5 % der Knoten. Formeln: 📐-Expander der App.

## Methodik

| Baustein | Inhalt |
|---|---|
| **Naives Schälen** | Definition: für k = 1, 2, … wiederholt Knoten mit Restgrad < k entfernen; Schritte = Gradprüfungen + 2m Gradabzüge; jeder Durchlauf ist ein abspielbarer Schritt |
| **Bucket-Algorithmus** | Batagelj und Zaveršnik: Knoten nach Grad in Fächern, jede Kante zweimal geprüft; liefert nebenbei die Degeneracy-Ordnung |
| **Experiment 1** | Schritte beider Verfahren über die Netzgröße (n = 100, 400, 1 600), Median über die festen Netze |
| **Experiment 2** | Kernzahl gegen Grad über alle Netztypen bei den Reglerwerten der Seitenleiste; Cliquenschranke ω ≤ Degeneracy + 1 |
| **Experiment 3** | Ausbreitungskraft jedes Knotens als Einzelstarter gegen fünf Maße; Zuverlässigkeit = Rangkorrelation zweier Hälften der Läufe |

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Netze der Messreihen: n = 120, c = 6 (Gitter in der Tabelle von Experiment 2 mit c = 6, also mit einer Diagonale), Median über die fünf festen Netze `SWEEP_SEEDS`, wo nichts anderes steht.

| Frage | Befund |
|---|---|
| **Stimmen die Verfahren?** | ✅ Bucket-Algorithmus und naives Schälen liefern auf allen Netzen dieselben Kernzahlen; Orakel `tests/test_oracle_k_core.py`: networkx.core_number auf 68 festen Instanzen, Brute Force nach Definition (30 Netze mit bis zu 10 Knoten), neun Familien mit bekanntem Wert (Baum 1, Stern 1, Pfad 1, Kreis 2, vollständiger Graph n − 1, Gitter 2, Rad 3, Q₄ 4, Barbell 5) |
| **Wie viele Schritte braucht der Bucket-Algorithmus?** | ✅ **Genau 2n + 2m** auf allen gemessenen Netzen (`test_bucket_steps_are_exactly_2n_plus_2m_on_every_measured_network`) |
| **Wie viel teurer ist das naive Schälen?** | Bei n = 1 600 nur das **2,3-fache** auf Zufallsnetzen, das **1,5-fache** auf skalenfreien Netzen und das **1,2-fache** auf dem Gitter; im **ungünstig nummerierten Pfad** das **7,2-, 25,9- und 100,9-fache** bei n = 100, 400 und 1 600 (801 Durchläufe bei n = 1 600): der Faktor wächst dort mit n, weil jeder Durchlauf nur die zwei Enden entfernt |
| **Handbeispiel (10 Knoten)** | Kernzahlen 2, 2, 2, 1, 1, 0, 3, 3, 3, 3; 4 Schalen; Bucket 44 Schritte, naiv 82 Schritte in 8 Durchläufen; ω = 4 |
| **Auf welchen Netztypen ist die Kernzahl konstant?** | **Skalenfreies Netz (BA) und Ring mit Abkürzungen auf allen fünf Netzen**: alle Knoten liegen in einer Schale (beim BA-Modell mit m Kanten je neuem Knoten liegen alle im m-Kern, bewiesen und getestet). Dort trägt die Kernzahl keine Information. Bei Zufallsnetz, Potenzgesetz-Netz, Verbünden, Gitter und „Hubs am Rand“ gibt es mindestens zwei Schalen |
| **Wie stark folgt die Kernzahl dem Grad?** | Rangkorrelation Grad–Kernzahl (Median): Zufallsnetz **0,67**, Potenzgesetz-Netz **0,86**, Verbünde **0,62**, Gitter (mit Diagonale) **0,27**, „Hubs am Rand“ **0,86**. Beispiel Standardnetz (Seed 35): Zufallsnetz 5 Schalen, 100 von 120 Knoten im 4-Kern, nur bei 22 % der Knoten ist die Kernzahl gleich dem Grad |
| **Cliquenschranke ω ≤ Degeneracy + 1** | ✅ gilt in allen Netzen; scharf (Lücke 0) bei BA, Link-Netz (ω = 49 = 48 + 1); Lücke 1 bis 2 bei den übrigen Standardnetzen |
| **Hubs am Rand** | Alle fünf Hubs haben die **Kernzahl 1** bei einem Grad von mindestens 12; das Netz ist so gebaut, dass die Kernzahl dort gewinnt |
| **Link-Netz von sebastianhanisch.net** (Schnappschuss 2026-09-30, 350 Knoten, 2 374 Kanten) | Neun Schalen, aber eine **fast triviale Schichtung**: 49 Seiten bilden den Kern der Kernzahl 48 (ω = 49, die Seiten verlinken einander vollständig), die 404-Seite ist isoliert (Kernzahl 0); bei **284 von 300 Demos** ist die Kernzahl **genau ihr Grad** (3 bis 9), die 16 anderen sind Demos mit vielen Demo-zu-Demo-Querverlinkungen (z. B. `hill-climbing-demo`: Grad 16, Kernzahl 6). Rangkorrelation Grad–Kernzahl über alle Knoten **0,998** |
| **Sagt die Kernzahl die Ausbreitung besser voraus als der Grad?** | **Nur in den Kern-Rand-Netzen.** Rangkorrelation mit der Ausbreitungskraft, Median der fünf Netze (β = 3-fach β_c, 100 Läufe je Startknoten), Grad / Kernzahl / Nähe: Zufallsnetz 0,89 / 0,64 / 0,89; Potenzgesetz 0,83 / 0,80 / 0,83; BA 0,80 / konstant / 0,81; Verbünde 0,86 / 0,60 / 0,76; Ring 0,37 / konstant / 0,59; Gitter 0,70 / 0,22 / 0,86; Hubs am Rand 0,87 / 0,87 / 0,82. Die Kernzahl hat die höhere Rangkorrelation als der Grad in 0 von 5 Zufallsnetzen, 2 von 5 Potenzgesetz-Netzen, 0 von 5 Verbünden, 0 von 5 Gittern und 3 von 5 „Hubs am Rand“-Netzen |
| **Und bei der Auswahl der besten 5 %?** | Die besten 5 % nach Kernzahl sind im Median **schlechtere Starter als die besten 5 % nach Grad in allen Netztypen außer „Hubs am Rand“** (dort 24,4 gegen 19,7 Knoten); beim konstanten BA-Netz entspricht die Kernzahl-Auswahl der Zufallswahl |
| **Welches Maß ist am besten?** | Die höchste mediane Rangkorrelation haben: **Nähe** in 3 Netztypen (Zufallsnetz, BA, Ring), **Grad** in 2 (Potenzgesetz, Verbünde; Potenzgesetz mit 0,829 gegen 0,828 praktisch gleichauf), **Betweenness** in 1 (Gitter), **Kernzahl** in 1 (Hubs am Rand), PageRank in keinem |
| **Wie zuverlässig ist die Messung?** | Rangkorrelation zweier Hälften der Läufe im Median mindestens 0,69 in allen Netztypen außer dem **Ring mit Abkürzungen (unter 0,4)**: dort unterscheiden sich die Knoten kaum, die Rangfolge ist dort Rauschen |

## Ehrliche Grenzen

- **Ein negatives Ergebnis an Modellnetzen widerlegt keine Arbeit an großen echten Netzen.** Die Netze der Demo haben 120 Knoten, das Link-Netz 350; es ist selbst erzeugt und folgt der Navigation der Website und der Regel „jede Demo verlinkt auf Startseite und Kontakt“. Es ist kein soziales Netz.
- **Ein Starter.** Mehrere gleichzeitige Starter und ihr Abstand zueinander (der zweite Befund bei Kitsak u. a.) fehlen und gehören in die Einflussmaximierung (Stück 5 der Reihe).
- **Ausbreitungskraft = erwartete Endgröße im SIR-Modell** einschließlich kleiner Ausbrüche; β ist ein Vielfaches der Mean-Field-Schwelle, die in endlichen Netzen zu niedrig liegt. Nur ein Wert (3-fach) steckt in den README-Zahlen; die App erlaubt 1- bis 4-fach.
- **Ungerichtet, ungewichtet.** Die Link-Richtung geht verloren.
- **Die Auswahl nach den Messläufen ist selbst verrauscht** (Zuverlässigkeit steht neben jeder Messung); die Unterschiede zwischen Grad, Nähe und PageRank sind in mehreren Netztypen klein (z. B. 0,829 gegen 0,828), die Rangliste der Maße ist dort nicht belastbar.
- **Elementarschritte sind keine Laufzeit.** Ein Faktor in Schritten ist kein Faktor in Sekunden.
- **Der Schnappschuss des Link-Netzes stammt vom 2026-09-30** (300 Demos, inzwischen gibt es mehr).

## Verifikation

- **Kern:** Hand-Rechnung auf dem Handbeispiel (Kernzahlen, Schritte, Durchlauflog), Maße auf Pfad und Stern, Rangkorrelation, Top-k mit Gleichständen (`tests/test_algorithm.py`); Randfälle n = 0, 1, 2, isolierte Knoten, Gleichstände (`tests/test_edge_cases.py`).
- **Orakel** (`tests/test_oracle_k_core.py`): networkx (Kernzahlen, Cliquenzahl, Nähe, Betweenness, PageRank), Brute Force nach Definition, scipy (Rangkorrelation und Ränge mit Gleichständen), Aufzählung aller Gleichstandsauflösungen für die Top-k-Erwartung, **eingefrorene Referenzläufe aus `kaskaden-demo`** für die SIR-Regel; Schrittzahlen unabhängig neu gezählt.
- **Netze** (`tests/test_scenario.py`): jeder Netztyp liefert ein gültiges Netz mit gültigen Positionen, Determinismus je Seed, Ergebnisse unabhängig vom Hash-Seed (zwei Prozesse), Gegenbeispiel-Pfad wirklich quadratisch, Link-Netz = Schnappschuss, gesperrte Regler wirken wirklich nicht.
- **Verdikte** als reine Funktionen (`tests/test_verdicts.py`): jede Schwelle und jede genannte Zahl an handgesetzten Werten; Dezimalkomma.
- **Presets und Layout:** vollständig, gültige Werte, Standard-Preset = Standardeinstellung; Schnellstart oben, fester Kopf, aktives Preset hervorgehoben, jede Änderung eines Reglers hebt die Markierung auf (`tests/test_presets.py`, `tests/test_layout.py`).
- **Oberfläche:** AppTest (jeder Button, jeder Regler an Minimum und Maximum, alle Minima und alle Maxima zugleich, jeder Netztyp, Permalink mit Begrenzen, Abspielen, Ausbreitungsmessung mit Ungültigwerden bei geänderten Einstellungen, Link-Netz), Footer- und Laufzeit-Import-Test.
- **Claims:** jede Zahl dieser README in `tests/test_claims.py`.
- **Mutationsprüfung** (`tools/mutate_demo.py`, Zustand in `tests/mutation_state.json`) für den numerischen Kern `kco_algorithm.py`: alle 197 Mutationsstellen behandelt; 192 gefangen oder als äquivalent festgehalten (15 äquivalente, etwa Grenzen, die das Ergebnis nicht ändern), 5 führen zu Endlosschleifen (Zeitüberschreitung, zählt nicht als gefangen). Die Läufe fanden fünf Testlücken, die jetzt eigene Tests haben: der letzte Knoten in der ehrlichen Auswahl, die Reihenfolge der Schalen, die Grenzen der Graphprüfung, die Aufrufzahl der Cliquensuche (Limit, Schranke, Pivot, Reihenfolge) und die Schrittgrenze der Ausbreitung. Auswertung, Verdikte und Darstellung wurden nicht mutiert (Verdikte haben eigene Tests mit handgesetzten Werten).

## Tests

200 Tests, rund 70 Sekunden (`pytest tests/ -v`; die Ausbreitungs-Claims rechnen einen großen Teil davon).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Netz mit Schälen, Kernfrage, drei Experimente, Grenzen, Formeln |
| `data/link_netz.json` | Link-Netz von sebastianhanisch.net (Schnappschuss 2026-09-30, aus `interne-verlinkung-demo`, ungerichtet) |
| `kco_algorithm.py` | Kern: Bucket-Algorithmus, naives Schälen, Maße, SIR, Rangkorrelation, Top-k |
| `kco_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `kco_evaluation.py` | Kennzahlen, Sweeps, Verdikte (reine Funktionen) |
| `kco_layout.py` | Fester Kopf (Stylesheet) |
| `kco_presets.py` | Permalink (Begrenzen), Presets, Zufalls-Seed-Button |
| `kco_scenario.py` | Netze (Generatoren, Handbeispiel, Pfad, Link-Netz) und Anordnung für die Anzeige |
| `kco_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest, networkx, scipy (nur Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Hand-Rechnung, Orakel, Randfälle, Netze, Verdikte, Presets, Layout, AppTest, Claims, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Mehrere Starter und Abstandseffekt** (Kitsak u. a. 2010): gehören zur Einflussmaximierung.
- **Echte große Netze:** keine Lizenz- und Datenschutzfragen, keine Personendaten; die Demo bleibt bei synthetischen Netzen und dem eigenen Link-Netz.
- **Gerichtete oder gewichtete Kerne**, verteilte oder externe Verfahren zur Kernzerlegung (siehe Malliaros u. a. 2020).
- **Gemeinschaften und Dichte-Hierarchien jenseits des Kerns** (z. B. Truss, Dichte-Zerlegung): spätere Stücke der Reihe.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
