# --- Constants ---
APP_NAME = "Gambit Pairing"
APP_VERSION = "0.4" # Incremented version
SAVE_FILE_EXTENSION = ".gpf"
SAVE_FILE_FILTER = f"Gambit Pairing Files (*{SAVE_FILE_EXTENSION});;All Files (*)"
CSV_FILTER = "CSV Files (*.csv);;Text Files (*.txt)"

WIN_SCORE = 1.0
DRAW_SCORE = 0.5
LOSS_SCORE = 0.0
BYE_SCORE = 1.0

# Result types
RESULT_WHITE_WIN = "1-0"
RESULT_DRAW = "0.5-0.5"
RESULT_BLACK_WIN = "0-1"
# TODO: Add Forfeit result types and handling

# Tiebreaker Keys & Default Order
TB_MEDIAN = 'median'
TB_SOLKOFF = 'solkoff'
TB_CUMULATIVE = 'cumulative'
TB_CUMULATIVE_OPP = 'cumulative_opp'
TB_SONNENBORN_BERGER = 'sb'
TB_MOST_BLACKS = 'most_blacks'
TB_HEAD_TO_HEAD = 'h2h' # Internal comparison key

# Default display names for tiebreaks
TIEBREAK_NAMES = {
    TB_MEDIAN: "Median",
    TB_SOLKOFF: "Solkoff",
    TB_CUMULATIVE: "Cumulative",
    TB_CUMULATIVE_OPP: "Cumulative Opp",
    TB_SONNENBORN_BERGER: "Sonnenborn-Berger",
    TB_MOST_BLACKS: "Most Blacks",
}

# Default order used for sorting if not configured otherwise
DEFAULT_TIEBREAK_SORT_ORDER = [
    TB_MEDIAN,
    TB_SOLKOFF,
    TB_CUMULATIVE,
    TB_CUMULATIVE_OPP,
    TB_SONNENBORN_BERGER,
    TB_MOST_BLACKS,
]

UPDATE_URL = "https://api.github.com/repos/Lucas-C/GambitPairing/releases/latest"