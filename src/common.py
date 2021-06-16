import re

MAX_LOOKUPS_PER_MESSAGE = 9

EMBED_ERROR_STR = "[Error]"

# Patterns =====================================================================

LOOKUP_PATTERN = re.compile(r"(?:^|\s)%%([\w:\/\.-]+(?<!\.))")
LAST_PATH_SECTION_NO_EXTENSIONS_PATTERN = re.compile(r"/?([\w-]+)(?:\.\w+)*$")

# ==============================================================================
FILE_EXTENSION_MAP = {
    "HC": {"type": "HolyC", "is_web_linkable": True},
    "TXT": {"type": "Text", "is_web_linkable": True},
    "GR": {"type": "Graphics", "is_web_linkable": True},
    "DD": {"type": "DolDoc", "is_web_linkable": True},
    "IN": {"type": "Input", "is_web_linkable": True},
    "BMP": {"type": "Windows Bitmap", "is_web_linkable": False},
    "BIN": {"type": "Binary", "is_web_linkable": False},
    "CPP": {"type": "C++", "is_web_linkable": False},
}
