"""English and French strings, and the number formatting each language expects.

Kept in one file rather than scattered through the app so that a missing
translation is a visible gap in a table, not a stray English sentence noticed
by a French reader six screens in. A test asserts both dictionaries carry
exactly the same keys.

French typography here follows the usual rules: a narrow no-break space before
: ; ! ?, a comma as the decimal mark, and a no-break space as the thousands
separator.
"""

from __future__ import annotations

LANGUAGES = {"en": "English", "fr": "Français"}
DEFAULT_LANG = "en"

NBSP = " "        # no-break space
NNBSP = " "       # narrow no-break space, used before French punctuation

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # shell
        "title": "Terroir & Climat",
        "lede": "Growing-season water balance across {n} French departments, "
                "{y0}–{y1}. Showing {season} in {year}.",
        "lede_setup": "Growing-season water balance across the 96 French "
                      "departments, {y0}–{y1}.",
        "language": "Language",

        # sidebar
        "sidebar_season": "Season",
        "sidebar_season_help": "Months summed",
        "sidebar_year": "Year",
        "sidebar_year_help": "Season shown",
        "sidebar_dep": "Department",
        "sidebar_dep_help": "Highlighted on the map",
        "sidebar_note": "Normals are each department's own {n0}–{n1} mean for the "
                        "same months. Water balance is rainfall minus reference "
                        "evapotranspiration (ET₀) — a climatic measure, not a soil "
                        "water budget.",

        # seasons
        "season_apr_jul": "Apr – Jul (cereals)",
        "season_mar_jun": "Mar – Jun (early)",
        "season_apr_sep": "Apr – Sep (full season)",
        "season_may_aug": "May – Aug (summer crops)",
        "season_mar_sep": "Mar – Sep (widest)",

        # metrics
        "metric_national": "National median anomaly",
        "metric_below": "Departments below normal",
        "metric_below_value": "{k} of {n}",
        "metric_driest": "Driest department",
        "metric_vs_normal": "{v} mm vs normal",
        "metric_no_data": "no data",

        # verdict line
        "verdict_driest": "**{year} is the driest growing season on record** — "
                          "{k} of {n} departments below normal, a national median "
                          "of {v} mm.",
        "verdict_dry": "{year} ranks {r} driest of {total} seasons — {k} of {n} "
                       "departments below normal.",
        "verdict_wettest": "**{year} is the wettest growing season on record** — "
                           "only {k} of {n} departments below normal.",
        "verdict_wet": "{year} ranks {r} wettest of {total} seasons — {k} of {n} "
                       "departments below normal.",
        "verdict_normal": "{year} is an unremarkable season: {r} driest of {total}, "
                          "with {k} of {n} departments below normal.",

        # section headings
        "sec_map": "The country in {year}",
        "sec_dep": "{dep} in detail",
        "sec_record": "The whole record",
        "trend_label": "10-year average",

        # map
        "map_legend": "mm vs {n0}–{n1} normal · drier ← → wetter",
        "map_no_data": "no data",
        "map_detail": "{p} mm rain − {e} mm ET₀",

        # charts
        "chart_anomaly": "{dep} — vs {n0}–{n1} normal",
        "chart_lines": "{dep} — rainfall and ET₀",
        "chart_national": "National median water-balance anomaly",
        "axis_mm": "mm",
        "axis_mm_season": "mm per season",
        "series_rain": "Rainfall",
        "series_et0": "ET₀",
        "hover_vs_normal": "mm vs normal",

        # tables
        "table_driest": "**{dep} — driest seasons, {y0}–{y1}**",
        "table_wettest": "**{dep} — wettest seasons, {y0}–{y1}**",
        "table_note": "These rank the whole record, not the year on the slider. "
                      "**{year} is the {r} driest of {n} seasons in {dep}.**",
        "col_year": "Year",
        "col_wb": "P − ET₀ (mm)",
        "col_anom": "vs normal (mm)",

        # origin
        "origin_header": "Why this exists — what changed from the dissertation",
        "origin_body": """
This began as an MSc dissertation asking whether **climate variability drives
crop yield**. The dataset it relied on could not answer that question, and the
reason is worth stating plainly.

**What the dissertation had**

| | |
|---|---|
| Spatial unit | 101 **countries** |
| Rainfall | **one fixed value per country**, repeated for every year, 1990–2013 |
| Temperature | one annual mean per country |
| Within-country variation | **none** |

Rainfall had no time dimension at all: France's figure for 1995 was identical to
its figure for 1990. You cannot correlate a crop yield against a constant, so
the central question was unanswerable with that data — regardless of which model
was fitted. A tuned Random Forest still reported R² ≈ 0.97, but almost all of it
came from knowing *which country and which crop*, not from climate.

**What this project changed**

| | Dissertation | Here |
|---|---|---|
| Spatial unit | 101 countries | **96 départements** in one country |
| Rainfall | 1 value per country, fixed | **daily**, per département |
| Evapotranspiration | absent | **daily ET₀**, so water *balance* is possible |
| Baseline | none | each département's **own 1961–1990 normal** |
| Time resolution | annual | daily → monthly → any season window |
| Verifiable against | nothing | **1976**, the drought France remembers |

The point is not a better model. It is that the measurement the dissertation
needed did not exist in its data, and now it does. The 1976 drought falls out of
this pipeline without being told to — that is the check that it is built right.

**What is still missing**

Crop yields. Département-level yield data for ten crops (1900–2018) is published
and open; joining it is the next step. Until then this is the climate half: the
part that was absent, built and verifiable on its own.
""",

        # expander
        "notes_header": "What this does and does not show",
        "notes_body": """
**Water balance** here is rainfall minus FAO reference evapotranspiration,
summed over {season}. It says whether a season delivered more or less water than
the atmosphere could take from a well-watered reference grass surface — nothing
about soil type, rooting depth, drainage, irrigation or runoff. It is not a
drought index and not a soil water budget.

**Anomalies** are against each department's own {n0}–{n1} mean, so a dry year in
Finistère is measured against Finistère, not against France. Departments whose
baseline has fewer than 20 usable years are left blank rather than shown against
a shaky normal.

**Source** is the ERA5 reanalysis via Open-Meteo, on roughly a 10 km grid,
sampled at each department's area-weighted centroid. One point per department
is a real simplification: it will misrepresent the large or mountainous ones,
where conditions vary more within the department than between neighbours.

**Crop yields are not in this version.** The department-level yield data
(1900–2018, ten crops) is the next milestone; this release is the climate half,
which is the part the dissertation was missing.
""",

        # setup screen
        "setup_warning": "**Not ready yet.** {msg}",
        "setup_msg_geometry": "Boundary files are missing. Run "
                              "`python scripts/prepare_geography.py`.",
        "setup_msg_climate": "The climate table has not been built yet.",
        "setup_body": """
### One step to go

The app needs a climate table built from the Open-Meteo ERA5 archive. It is free
and needs no account, but it does need an internet connection. In a terminal,
from this folder:

```bash
python scripts/build_climate_table.py --check   # proves the connection works
python scripts/build_climate_table.py           # builds the table
```

Run the first command first — if it fails you will know immediately, and the
message will say why. Every chunk is cached as it arrives, so an interrupted
download resumes where it stopped.
""",
        "setup_geometry_ok": "Boundaries are already in place: {n} departments.",
        "error_no_seasons": "The climate table has no complete seasons for that window.",
        "pending_years": "{k} more years ({y0}–{y1}) are downloaded for only part of "
                         "the country and are hidden until every département has "
                         "them. Rerun the fetch to fill them in.",
    },

    "fr": {
        # shell
        "title": "Terroir & Climat",
        "lede": "Bilan hydrique de la saison de végétation dans {n} départements "
                "français, {y0}–{y1}. Affichage : {season} en {year}.",
        "lede_setup": "Bilan hydrique de la saison de végétation dans les 96 "
                      "départements français, {y0}–{y1}.",
        "language": "Langue",

        # sidebar
        "sidebar_season": "Saison",
        "sidebar_season_help": "Mois cumulés",
        "sidebar_year": "Année",
        "sidebar_year_help": "Saison affichée",
        "sidebar_dep": "Département",
        "sidebar_dep_help": "Mis en évidence sur la carte",
        "sidebar_note": "Les normales sont la moyenne {n0}–{n1} propre à chaque "
                        "département, sur les mêmes mois. Le bilan hydrique est la "
                        "pluie moins l'évapotranspiration de référence (ET₀) — une "
                        "mesure climatique, et non un bilan hydrique du sol.",

        # seasons
        "season_apr_jul": "Avr – Juil (céréales)",
        "season_mar_jun": "Mars – Juin (précoce)",
        "season_apr_sep": "Avr – Sept (saison complète)",
        "season_may_aug": "Mai – Août (cultures d'été)",
        "season_mar_sep": "Mars – Sept (la plus large)",

        # metrics
        "metric_national": "Anomalie médiane nationale",
        "metric_below": "Départements sous la normale",
        "metric_below_value": "{k} sur {n}",
        "metric_driest": "Département le plus sec",
        "metric_vs_normal": "{v} mm / normale",
        "metric_no_data": "pas de données",

        # verdict line
        "verdict_driest": "**{year} est la saison de végétation la plus sèche "
                          "enregistrée** — {k} départements sur {n} sous la normale, "
                          "pour une médiane nationale de {v} mm.",
        "verdict_dry": "{year} se classe {r}ᵉ saison la plus sèche sur {total} — "
                       "{k} départements sur {n} sous la normale.",
        "verdict_wettest": "**{year} est la saison de végétation la plus humide "
                           "enregistrée** — seulement {k} départements sur {n} sous "
                           "la normale.",
        "verdict_wet": "{year} se classe {r}ᵉ saison la plus humide sur {total} — "
                       "{k} départements sur {n} sous la normale.",
        "verdict_normal": "{year} est une saison ordinaire : {r}ᵉ plus sèche sur "
                          "{total}, avec {k} départements sur {n} sous la normale.",

        # section headings
        "sec_map": "La France en {year}",
        "sec_dep": "{dep} en détail",
        "sec_record": "L'ensemble de la série",
        "trend_label": "moyenne sur 10 ans",

        # map
        "map_legend": "mm / normale {n0}–{n1} · plus sec ← → plus humide",
        "map_no_data": "pas de données",
        "map_detail": "{p} mm de pluie − {e} mm d'ET₀",

        # charts
        "chart_anomaly": "{dep} — écart à la normale {n0}–{n1}",
        "chart_lines": "{dep} — pluie et ET₀ de référence",
        "chart_national": "Anomalie médiane nationale du bilan hydrique",
        "axis_mm": "mm",
        "axis_mm_season": "mm par saison",
        "series_rain": "Précipitations",
        "series_et0": "ET₀",
        "hover_vs_normal": "mm / normale",

        # tables
        "table_driest": "**{dep} — saisons les plus sèches, {y0}–{y1}**",
        "table_wettest": "**{dep} — saisons les plus humides, {y0}–{y1}**",
        "table_note": "Ce classement porte sur toute la série, pas sur l'année du "
                      "curseur. **{year} est la {r}ᵉ saison la plus sèche sur {n} "
                      "dans le département {dep}.**",
        "col_year": "Année",
        "col_wb": "P − ET₀ (mm)",
        "col_anom": "écart (mm)",

        # origin
        "origin_header": "D'où vient ce projet — ce qui a changé depuis le mémoire",
        "origin_body": """
Ce travail est né d'un mémoire de master demandant si **la variabilité climatique
influence les rendements agricoles**. Le jeu de données utilisé ne pouvait pas
répondre à cette question, et la raison mérite d'être dite clairement.

**Ce dont disposait le mémoire**

| | |
|---|---|
| Unité spatiale | 101 **pays** |
| Précipitations | **une seule valeur fixe par pays**, répétée chaque année, 1990–2013 |
| Température | une moyenne annuelle par pays |
| Variation intra-pays | **aucune** |

Les précipitations n'avaient aucune dimension temporelle : le chiffre de la
France pour 1995 était identique à celui de 1990. On ne peut pas corréler un
rendement à une constante ; la question centrale était donc sans réponse
possible avec ces données, quel que soit le modèle ajusté. Une forêt aléatoire
optimisée affichait tout de même un R² ≈ 0,97, mais l'essentiel venait de
*savoir quel pays et quelle culture*, non du climat.

**Ce que ce projet a changé**

| | Mémoire | Ici |
|---|---|---|
| Unité spatiale | 101 pays | **96 départements** d'un seul pays |
| Précipitations | 1 valeur fixe par pays | **quotidiennes**, par département |
| Évapotranspiration | absente | **ET₀ quotidienne**, donc un vrai *bilan* hydrique |
| Référence | aucune | la **normale 1961–1990 propre** à chaque département |
| Résolution temporelle | annuelle | quotidienne → mensuelle → toute fenêtre saisonnière |
| Vérifiable contre | rien | **1976**, la sécheresse dont la France se souvient |

L'objectif n'est pas un meilleur modèle. C'est que la mesure dont le mémoire
avait besoin n'existait pas dans ses données, et qu'elle existe désormais. La
sécheresse de 1976 ressort de ce pipeline sans qu'on la lui ait indiquée : c'est
la preuve qu'il est correctement construit.

**Ce qui manque encore**

Les rendements. Les données départementales de rendement pour dix cultures
(1900–2018) sont publiées et ouvertes ; les joindre est l'étape suivante. D'ici
là, ceci est la moitié climatique : celle qui manquait, construite et
vérifiable par elle-même.
""",

        # expander
        "notes_header": "Ce que cela montre, et ce que cela ne montre pas",
        "notes_body": """
**Le bilan hydrique** est ici la pluie moins l'évapotranspiration de référence
FAO, cumulée sur {season}. Il indique si une saison a apporté plus ou moins d'eau
que l'atmosphère aurait pu en prélever à une prairie de référence bien alimentée
— rien sur le type de sol, la profondeur d'enracinement, le drainage,
l'irrigation ou le ruissellement. Ce n'est ni un indice de sécheresse, ni un
bilan hydrique du sol.

**Les anomalies** sont calculées par rapport à la moyenne {n0}–{n1} propre à
chaque département : une année sèche dans le Finistère est mesurée par rapport au
Finistère, et non par rapport à la France. Les départements dont la période de
référence compte moins de 20 années exploitables sont laissés en blanc plutôt
que comparés à une normale fragile.

**La source** est la réanalyse ERA5 via Open-Meteo, sur une grille d'environ
10 km, échantillonnée au centroïde pondéré par la surface de chaque département.
Un seul point par département est une vraie simplification : elle représente mal
les départements étendus ou montagneux, où les conditions varient davantage à
l'intérieur du département qu'entre voisins.

**Les rendements agricoles ne figurent pas dans cette version.** Les données de
rendement départementales (1900–2018, dix cultures) constituent l'étape suivante ;
cette version couvre la partie climatique, celle qui manquait au mémoire.
""",

        # setup screen
        "setup_warning": "**Pas encore prêt.** {msg}",
        "setup_msg_geometry": "Les fichiers de contours sont absents. Lancez "
                              "`python scripts/prepare_geography.py`.",
        "setup_msg_climate": "La table climatique n'a pas encore été construite.",
        "setup_body": """
### Une étape reste à faire

L'application a besoin d'une table climatique construite à partir de l'archive
ERA5 d'Open-Meteo. C'est gratuit et sans compte, mais il faut une connexion
internet. Dans un terminal, depuis ce dossier :

```bash
python scripts/build_climate_table.py --check   # vérifie la connexion
python scripts/build_climate_table.py           # construit la table
```

Lancez d'abord la première commande : si elle échoue, vous le saurez tout de
suite et le message en donnera la raison. Chaque bloc est mis en cache à mesure,
donc un téléchargement interrompu reprend là où il s'est arrêté.
""",
        "setup_geometry_ok": "Les contours sont déjà en place : {n} départements.",
        "error_no_seasons": "La table climatique ne contient aucune saison complète "
                            "pour cette fenêtre.",
        "pending_years": "{k} années supplémentaires ({y0}–{y1}) ne sont téléchargées "
                         "que pour une partie du pays et restent masquées tant que "
                         "tous les départements ne les ont pas. Relancez la "
                         "récupération pour les compléter.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Look up a string, falling back to English rather than showing a raw key."""
    table = STRINGS.get(lang, STRINGS[DEFAULT_LANG])
    text = table.get(key) or STRINGS[DEFAULT_LANG].get(key, key)
    return text.format(**kwargs) if kwargs else text


def season_label(lang: str, season_key: str) -> str:
    return t(lang, f"season_{season_key}")


def num(value: float, lang: str, decimals: int = 0, signed: bool = False) -> str:
    """Format a number the way each language writes it.

    English: -1,234.5   French: −1 234,5 (no-break thousands space, decimal comma)
    """
    if value is None:
        return "—"
    spec = f"{{:+,.{decimals}f}}" if signed else f"{{:,.{decimals}f}}"
    text = spec.format(value)
    if lang == "fr":
        text = text.replace(",", "\x00").replace(".", ",").replace("\x00", NBSP)
    return text
