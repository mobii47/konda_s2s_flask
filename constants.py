SL = "en"
SLS_LIST = ["en", "es", "fr", "it", "de", "pt"]
TLS_LIST = ["en", "fr", "es", "pt", "de", "ja", "it"]

LANG_MAP = {"en-US": "en",
            "en-AU": "en",
            "en-CA": "en",
            "en-GB": "en",
            "en-IN": "en",
            "en-NZ": "en",
            "es-ES": "es",
            "es-MX": "es",
            "fr-FR": "fr",
            "fr-FR": "fr",
            "pt-PT": "pt",
            "pt-BR": "pt",
            "de-DE": "de",
            "it-IT": "it",
            "ja-JP": "ja",
            }
VOICE_SPEED_DEFAULT = 20

CHARS_PER_SECOND_THRESHOLD = {
    "en": 25,
    "es": 30,
    "fr": 28,
    "pt": 25,
    "de": 30,
    "ja": 20,
    "it": 25, 
}
DEFAULT_VOICES_SPEED = {
    "en": 20,
    "es": 20,
    "fr": 20,
    "pt": 20,
    "de": 20,
    "ja": 20,
    "it": 20,
}
DURATION_COEFFICIENTS = {
    "en": .060,
    "es": .064,
    "fr": .063,
    "pt": .066,
    "de": .073,
    "ja": .060,
    "it": .060,
}
DEFAULT_VOICES_NAME = {
    "en": {"male": "en-US-AIGenerate1Neural", "female": "en-US-AmberNeural"},
    "es": {"male": "es-ES-AlvaroNeural", "female": "es-ES-AbrilNeural"},
    "fr": {"male": "fr-FR-AlainNeural", "female": "fr-FR-BrigitteNeural"},
    "pt": {"male": "pt-BR-FabioNeural", "female": "pt-BR-FranciscaNeural"},
    "de": {"male": "de-AT-JonasNeural", "female": "de-AT-IngridNeural"},
    "ja": {"male": "ja-JP-DaichiNeural", "female": "ja-JP-AoiNeural"},
    "it": {"male": "it-IT-LisandroNeural", "female": "it-IT-IrmaNeural"},
}
VOICE_STYLE = "General"
USE_TIMING_MATRIX = True
SAMPLING_RATE = 1
USE_REWRITING = False
