import re
import sqlite3
import random

import common

# 1: name, 2: file (if applicable), 3: line (if applicable), 4: type.
SYMBOL_PATTERN = re.compile(r"^(?:\$LK,\")?([\w/:\/.]+)(?:\s*\",A=\"FL:[A-Z]:([/\w\.]+),(\d+)\S+)?.*? ((?:[A-Z][a-z].*|NULL)) $")

# 1: full path.
PATH_PATTERN = re.compile(r"^\$LK,\"[A-Z]:([\w/\.-]+)")

# =============================================================================

def get_symbols(TOS_version):
    symbols = []
    with open(f"TOS_versions/{TOS_version}/Who.DD", "r", encoding="latin-1") as f:
        for line in f.readlines():
            m = re.match(SYMBOL_PATTERN, line)
            if m is not None:
                symbol = {
                    "name": m.group(1),
                    "file": m.group(2),
                    "line": m.group(3),
                    "type": m.group(4)
                }
                symbols.append(symbol)
            else:
                raise

    return symbols


def get_bare_paths(TOS_version):
    """ Return all paths on system containing a file. Infers parent dirs. """
    paths = []
    with open(f"TOS_versions/{TOS_version}/Paths.DD", "r", encoding="latin-1") as f:
        for line in f.readlines():
            file_path = re.match(PATH_PATTERN, line).group(1)
            paths.append(file_path)

            # Infer parent dirs; `FF("*");` output is only filepaths.
            parent_dir_paths = []
            splits = file_path.split("/")
            for i in range(0, len(splits)):
                parent_dir_paths.append("/".join(splits[:-i]))

            for dir_path in parent_dir_paths:
                if dir_path not in paths:
                    paths.append(dir_path)

        paths.append("/")
        return paths


def path_expand_info(path):
    extension_type_map = {
        "HC": "HolyC",
        "HH": "HolyC Header",
        "TXT": "Text",
        "GR": "Graphics",
        "DD": "DolDoc",
        "IN": "Input",
        "BMP": "Windows Bitmap",
        "BIN": "Binary",
        "CPP": "C++",
    }

    basename = path.split("/")[-1] or "/"
    is_compressed = False

    try:
        extension = basename.split(".", maxsplit=1)[1].upper()
        if extension.endswith(".Z"):
            is_compressed = True
            extension = extension[:-2]
        file_type = extension_type_map.get(extension) or extension
    except IndexError:
        file_type = "Directory"

    return {
        "full_path": path,
        "basename": basename,
        "type": file_type,
        "is_compressed": is_compressed
    }


def get_paths(TOS_version):
    return [path_expand_info(p) for p in get_bare_paths(TOS_version)]


def path_to_link(bare_path, line, TOS_version):
    path = path_expand_info(bare_path)
    if bare_path == "/":
        url_basename = ""
    elif "." in path["basename"]:
        url_basename = path["basename"].split(".")[0]+".html"
    else:
        url_basename = path["basename"]

    url_end = "/".join(path["full_path"].split("/")[:-1]+[url_basename])
    base_url = common.TOS_VERSION_BASE_URL_MAP[TOS_version]

    if line is None:
        url_line = ""
    else:
        url_line = "#l" + str(line)

    return base_url + url_end + url_line

# =============================================================================

def create_in_memory_database():
    con = sqlite3.connect(":memory:")
    cur = con.cursor()

    cur.executescript(
        """
        CREATE TABLE paths(
            TOS_version   TEXT NOT NULL COLLATE NOCASE,
            full_path     TEXT NOT NULL COLLATE NOCASE,
            basename      TEXT NOT NULL COLLATE NOCASE,
            type          TEXT NOT NULL COLLATE NOCASE,
            is_compressed BOOLEAN NOT NULL
        ); 
        CREATE INDEX `PATH`
        ON `paths` (`full_path` COLLATE NOCASE, `TOS_version`);

        CREATE INDEX `BASENAME`
        ON `paths` (`basename` COLLATE NOCASE, `TOS_version`);

        CREATE TABLE symbols(
            TOS_version TEXT NOT NULL COLLATE NOCASE,
            name        TEXT NOT NULL COLLATE NOCASE,
            file        TEXT COLLATE NOCASE,
            line        INTEGER,
            type        TEXT NOT NULL COLLATE NOCASE
        );
        CREATE INDEX `SYMBOL_NAME`
        ON `symbols` (`name` COLLATE NOCASE, `TOS_version`);
        """
    )

    for version in ["TinkerOS", "TempleOS_5.3"]:
        for path in get_paths(version):
            cur.execute(
                """
                INSERT INTO paths(
                    TOS_version, full_path, basename, type, is_compressed
                )
                VALUES (?, ?, ?, ?, ?) """,
                (
                    version,
                    path["full_path"],
                    path["basename"],
                    path["type"],
                    path["is_compressed"]
                )
            )

        for symbol in get_symbols(version):
            cur.execute(
                """
                INSERT INTO symbols(
                    TOS_version, name, file, line, type
                )
                VALUES (?, ?, ?, ?, ?) """,
                (
                    version,
                    symbol["name"],
                    symbol["file"],
                    symbol["line"],
                    symbol["type"]
                )
            )
        con.commit()

    return con, cur


def needle_normalize_escapes(needle):
    " Escape underscore wildcards, convert star wildcards to SQL wildcards. "
    return needle.replace("_", r"\_").replace("*", "%")


def look_up(TOS_version, needle, con, cur):
    needle_escaped = needle_normalize_escapes(needle)

    if "/" in needle:
        try:
            path_needle = re.match(common.PATH_WITHOUT_DRIVE_PATTERN, needle).group(1)
            path_needle_escaped = needle_normalize_escapes(path_needle)
        except AttributeError:
            path_needle = needle
            path_needle_escaped = needle_escaped

        cur.execute(
            r"""
            SELECT full_path, basename, type, is_compressed, TOS_version
            FROM `paths`
            WHERE (
                `full_path` = ?
                OR `full_path` LIKE ? ESCAPE '\'
                OR `full_path` LIKE ? ESCAPE '\'
            )
            AND `TOS_version` = (?)
            """,
            [path_needle, path_needle_escaped, path_needle_escaped+".%", TOS_version]
        )
    else:
        cur.execute(
            r"""
            SELECT full_path, basename, type, is_compressed, TOS_version
            FROM `paths`
            WHERE (
                `basename` = ?
                OR `basename` LIKE ? ESCAPE '\'
                OR `basename` LIKE ? ESCAPE '\'
            )
            AND `TOS_version` = (?)
            """,
            [needle, needle_escaped, needle_escaped+".%", TOS_version]
        )
    tuple_path_matches = cur.fetchall()
    path_matches = []
    for m in tuple_path_matches:
        path_matches.append(
            {
                "full_path": m[0],
                "basename": m[1],
                "type": m[2],
                "is_compressed": bool(m[3]),
                "TOS_version": m[4]
            }
        )

    cur.execute(
        r"""
        SELECT name, file, line, type, TOS_version
        FROM `symbols` WHERE (
            `name` = ?
            OR `name` LIKE ? ESCAPE '\'
        )
        AND `TOS_version` = (?) 
        """,
        [needle, needle_escaped, TOS_version]
    )
    tuple_symbol_matches = cur.fetchall()
    symbol_matches = []
    for m in tuple_symbol_matches:
        symbol_matches.append(
            {
                "name": m[0],
                "file": m[1],
                "line": m[2],
                "type": m[3],
                "TOS_version": m[4]
            }
        )

    return path_matches, symbol_matches


def get_random_symbol_or_path(TOS_version, con, cur):
    pair = random.choice(
        [
            ("name", "symbols"),
            ("basename", "paths"),
            ("full_path", "paths")
        ]
    )
    cur.execute(
        f"""
        SELECT {pair[0]} FROM {pair[1]} WHERE `TOS_version` = (?)
        ORDER BY RANDOM() LIMIT 1;
        """,
        [TOS_version]
    )
    return cur.fetchone()[0]
