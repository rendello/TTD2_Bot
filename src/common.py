
import re

EMBED_ERROR_STR = "[Error]"

# Patterns =====================================================================
PAT_LAST_PATH_SECTION_NO_EXTENSIONS = re.compile(r"/?([\w-]+)(?:\.\w+)*$")
