""" The TTD2 Discord chat bot. """

import asyncio
import pathlib
import re
import json

import appdirs
import discord
import fuzzywuzzy.fuzz
import openbsd

import common

# todo: fuzzy matching.
# todo: allow multiple path segments per name.
# todo: allow reprocessing message on edit.
# todo: empty %% tokenizes message above
# todo: seperate match processing from process_msg, will help with above.
# check: odd results in sort symbol.json | uniq -cd

# todo: change how path search works:
#       - Path is first "normalized" by getting the lowercased last section
#       - /?([\w-]*)(?:\.\w+)*$
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
    print(clean_symbol_matches)
    print(dirty_symbol_matches)


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
        pass
        pass
        pass
        pass
        pass
        pass
        pass

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

    if line is not None:
        line_url_str = f"#l{line}"
        line_text_str = f", line: {line}"
    else:
        line_url_str = ""
        line_text_str = ""

    if is_web_linkable:
        url = f"https://templeos.holyc.xyz/Wb{path_parts[0]}.html"
        path_str = f"[::{path}{line_text_str}]({url}{line_url_str})"
    else:
        path_str = f"{path}{line_text_str}"

    basename = path.split("/")[-1] or "/"

    return path_type, path_str, basename


# Embeds =======================================================================
def embed_append_symbol(embed, symbol):
    if "file" not in symbol:
        path_link = "N/A"
    else:
        path = symbol["file"][2:]  # Remove drive letter, ie. "C:"
        if "." in path:
            path = path.split(".")[0] + ".html"
        url = f"https://templeos.holyc.xyz/Wb{path}#l{symbol['line']}"
        path_link = f"[{symbol['file']}, line {symbol['line']}]({url})"

    opcode_ref = ""
    if symbol["type"] == "OpCode":
        extra_fields = \
f"""
Reference: [x86 reference: {symbol['symbol']}](https://www.felixcloutier.com/x86/{symbol['symbol'].lower()})

See [::/Doc/ASM.DD.Z](https://templeos.holyc.xyz/Wb/Doc/Asm.html)
And [::/Compliler/OpCodes.DD.Z](https://templeos.holyc.xyz/Wb/Compiler/OpCodes.html)
"""

    elif symbol["type"] == "Reg":
        l = ("https://en.wikibooks.org/wiki/X86_Assembly/X86_Architecture"
        +"#General-Purpose_Registers_(GPR)_-_16-bit_naming_conventions")
        extra_fields = f"Reference: [Wikibooks: x86 Architecture]({l})"

    else:
        extra_fields = f"Definition: {path_link}"


    text = f"Type: {symbol['type']}\n{extra_fields}"

    embed.add_field(name=symbol['symbol'], value=text, inline=False)
    return embed


def embed_append_path(embed, path):
    path_type, path_str, base_name = get_TOS_path_str(path)
    text = f"Type: {path_type}\nPath: {path_str}"

    embed.add_field(name=path_name, value=text, inline=False)
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
    #client.run(config["token"])
    pass
