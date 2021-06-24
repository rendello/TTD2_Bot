import re
import json

MAX_LOOKUPS_PER_MESSAGE = 9
EMBED_ERROR_STR = "[Error]"

TOS_VERSIONS = ["TempleOS_5.3", "TinkerOS"]
DEFAULT_TOS_VERSION = "TempleOS_5.3"

TOS_VERSION_BASE_URLS = {
    "TempleOS_5.3": "templeos.holyc.xyz/Wb/",
    "TinkerOS": "https://tinkeros.github.io/WbGit/"
}

# Patterns =====================================================================

# 1: TOS version (if applicable), 2: needle.
# Eg. %%(TinkerOS)Cd -> 1: "TinkerOS", 2: "Cd".
# Eg. %%DocClear -> 1: None, 2: "DocClear".
LOOKUP_PATTERN = re.compile(r"(?:^|\s)%%(?:\(([\w\.]+)\))?([\w:\/\.-]+(?<!\.))")

BASENAME_NO_EXTENSIONS_PATTERN = re.compile(r"/?([\w-]+)(?:\.\w+)*$")

