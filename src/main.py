""" The TTD2 Discord chat bot. """

import asyncio
import pathlib
import re
import json
import functools

import appdirs
import discord
import fuzzywuzzy.fuzz
import openbsd

import common

# ==============================================================================

async def change_status_task():
    statuses = [
        "Usage: %%<function>",
        "Example: %%Dir",
        "Usage: %%<path>",
        "Example: %%/Demo/Graphics/WallPaperFish.HC.Z",
        "Usage: %%<file>",
        "Example: %%Once.HC",
    ]
    for s in statuses:
        await client.change_presence(activity=discord.Game(s))
        await asyncio.sleep(15)


def file_name_variations(file_name):
    """ "Install.HC.Z" -> ["Install.HC.Z", "Install.HC", "Install"] """
    variations = []
    sections = file_name.split(".")
    for i in range(0, len(sections)):
        variations.append(".".join(sections[:i+1]))
    return variations


@functools.lru_cache()
def find_symbol_matches(lookup):
    clean_symbol_matches = []
    dirty_symbol_matches = []
    for symbol in common.TOS_SYMBOLS:
        lookup_lowered = lookup.lower()
        symbol_name_lowered = symbol["name"].lower()

        if lookup_lowered == symbol_name_lowered:
            clean_symbol_matches.append(symbol)
        else:
            percent_similarity = fuzzywuzzy.fuzz.ratio(
                lookup_lowered,
                symbol_name_lowered
            )
            if percent_similarity > 80:
                dirty_symbol_matches.append((symbol, percent_similarity))

    close_matches = [m[0] for m in sorted(dirty_symbol_matches, key=lambda x: x[1])]
    return clean_symbol_matches, close_matches


@functools.lru_cache()
def find_path_matches(lookup):
    clean_path_matches = []
    dirty_path_matches = []
    clean_basename_matches = []
    dirty_basename_matches = []

    for path in common.TOS_PATHS:
        lookup_lowered = lookup.lower()
        path_lowered = path.lower()

        # Full path matches.
        if lookup_lowered in file_name_variations(path_lowered):
            clean_path_matches.append(path)
        else:
            percent_similarity = fuzzywuzzy.fuzz.ratio(
                lookup_lowered,
                path_lowered
            )
            if percent_similarity > 65:
                dirty_path_matches.append((path, percent_similarity))

        # Basename matches.
        basename = path_lowered.split("/")[-1] or "/"
        if lookup_lowered in file_name_variations(basename):
            clean_basename_matches.append(path)
        else:
            percent_similarity = fuzzywuzzy.fuzz.ratio(
                lookup_lowered,
                basename
            )
            if percent_similarity > 65:
                dirty_basename_matches.append((path, percent_similarity))

    exact_matches = clean_path_matches.copy()
    for m in clean_basename_matches:
        if m not in exact_matches:
            exact_matches.append(m)

    close_matches_unsorted = list(set(dirty_path_matches + dirty_basename_matches))
    close_matches = [m[0] for m in sorted(close_matches_unsorted, key=lambda x: x[1])]

    return exact_matches, close_matches


def process_lookup(embed, lookup, show_all=False):
    exact_symbol_matches, symbol_close_matches = find_symbol_matches(lookup)
    exact_path_matches, path_close_matches = find_path_matches(lookup)

    for path in (exact_path_matches):
        embed_append_path(embed, path)

    for symbol in (exact_symbol_matches):
        embed_append_symbol(embed, symbol)

    if exact_symbol_matches == [] and exact_path_matches == []:
        embed_append_not_found(embed, lookup, symbol_close_matches, path_close_matches)

    return embed


async def process_msg(text):
    too_many_lookups = False
    lookups = []
    for i, lookup in enumerate(re.findall(common.LOOKUP_PATTERN, text)):
        if lookup not in lookups:
            if i <= common.MAX_LOOKUPS_PER_MESSAGE:
                lookups.append(lookup)
            else:
                too_many_lookups = True
                break
    if lookups == []:
        return

    embed = discord.Embed(color = 0x55FFFF)
    for lookup in lookups:
        embed = process_lookup(embed, lookup)

    if too_many_lookups:
        embed = embed_append_error(embed, "Too many lookups, trimmed output.")

    return embed


def get_TOS_path_str(path, line=None):
    """ Catogorizes path by extension, then builds and returns:
        `path_type`, the full name for the type,
        `path_str`, the markdown version of the path, with link if applicable,
        `basename`, the final section of the path as seperated by "/".
    """
    is_web_linkable = False

    # "Doc/CutCorners.DD.Z" -> ("Doc/CutCorners", "DD", "Z")
    path_parts = path.split(".")
    if len(path_parts) > 1:
        main_extension = path_parts[1]

        extension_info = common.FILE_EXTENSION_MAP.get(main_extension)
        if extension_info is not None:
            path_type = extension_info["type"]
            is_web_linkable = extension_info["is_web_linkable"]
        else:
            path_type = main_extension

        if path_parts[-1] == "Z":
            path_type += " (Compressed)"
    else:
        path_type = "Directory"
        is_web_linkable = True

    if line is not None:
        line_url_str = f"#l{line}"
        line_text_str = f", line: {line}"
    else:
        line_url_str = ""
        line_text_str = ""

    if is_web_linkable:
        if path_type == "Directory":
            url = f"https://templeos.holyc.xyz/Wb{path_parts[0]}"
        else:
            url = f"https://templeos.holyc.xyz/Wb{path_parts[0]}.html"

        path_str = f"[::{path}{line_text_str}]({url}{line_url_str})"
    else:
        path_str = f"{path}{line_text_str}"

    basename = path.split("/")[-1] or "/"

    return path_type, path_str, basename


# Embeds =======================================================================
def embed_append_symbol(embed, symbol):
    if symbol.get("file") is not None:
        path_type, path_str, basename = get_TOS_path_str(symbol["file"], symbol["line"])
    else:
        path_str = "N/A"

    opcode_ref = ""
    if symbol["type"] == "OpCode":
        extra_fields = \
f"""
Reference: [x86 reference: {symbol['name']}](https://www.felixcloutier.com/x86/{symbol['name'].lower()})

See [::/Doc/ASM.DD.Z](https://templeos.holyc.xyz/Wb/Doc/Asm.html)
And [::/Compliler/OpCodes.DD.Z](https://templeos.holyc.xyz/Wb/Compiler/OpCodes.html)
"""

    elif symbol["type"] == "Reg":
        l = ("https://en.wikibooks.org/wiki/X86_Assembly/X86_Architecture"
        +"#General-Purpose_Registers_(GPR)_-_16-bit_naming_conventions")
        extra_fields = f"Reference: [Wikibooks: x86 Architecture]({l})"

    else:
        extra_fields = f"Definition: {path_str}"

    text = f"Type: {symbol['type']}\n{extra_fields}"

    embed.add_field(name=symbol['name'], value=text, inline=False)
    return embed


def embed_append_path(embed, path):
    path_type, path_str, basename = get_TOS_path_str(path)
    text = f"Type: {path_type}\nPath: {path_str}"

    embed.add_field(name=basename, value=text, inline=False)
    return embed


def embed_append_not_found(embed, lookup, symbol_close_matches, path_close_matches):
    text = f"Path or symbol not found: {lookup}\n\n"

    if symbol_close_matches != []:
        text += "Close symbol matches:\n"
        for symbol in symbol_close_matches:
            if symbol.get("file") is not None:
                _path_type, path_str, _basename = get_TOS_path_str(symbol["file"], symbol["line"])
                text += f"`{symbol['name']}`, from {path_str}\n"
            else:
                text += f"`{symbol['name']}`\n"

    if path_close_matches != []:
        text += "Close path matches:\n"
        for path in path_close_matches:
            _path_type, path_str, _basename = get_TOS_path_str(path)
            text += f"{path_str}\n"
    
    embed.add_field(name="Not found.", value=text, inline=False)
    return embed


def embed_append_error(embed, error_message):
    embed.add_field(name=common.EMBED_ERROR_STR, value=error_message, inline=False)
    return embed


# Client and callbacks =========================================================
client = discord.Client()

@client.event
async def on_ready():
    openbsd.pledge("stdio inet dns prot_exec")

    await client.loop.create_task(change_status_task())


@client.event
async def on_message(msg):
    embed = await process_msg(msg.content)
    if embed is not None:
        await msg.channel.send(embed = embed)


# ==============================================================================

# Load token from config. If not available, prompt for token and
# create config.
config_dir = pathlib.Path(appdirs.user_config_dir("TTD2_bot"))
config_file = config_dir.joinpath("config.json")

if config_file.exists():
    with open(config_file, "r") as f:
        config = json.load(f)
else:
    config = {}
    print("Config doesn't exist. Creating one. [ctrl+c to cancel]")
    config["token"] = input("Bot token: ")
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w+") as f:
        json.dump(config, f)


if __name__ == "__main__":
    client.run(config["token"])
    pass
