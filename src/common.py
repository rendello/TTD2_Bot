import re
import json

MAX_LOOKUPS_PER_MESSAGE = 9
EMBED_ERROR_STR = "[Error]"

#with open("symbols.json") as f:
#    data = json.load(f)
#TOS_SYMBOLS = data["symbols"]
#TOS_PATHS = data["paths"]

# Patterns =====================================================================

LOOKUP_PATTERN = re.compile(r"(?:^|\s)%%([\w:\/\.-]+(?<!\.))")
BASENAME_NO_EXTENSIONS_PATTERN = re.compile(r"/?([\w-]+)(?:\.\w+)*$")

