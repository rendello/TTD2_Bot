""" The TTD2 Discord chat bot. """

import asyncio
import pathlib
import platform
import re
import json

import appdirs
import discord

try:
    from openbsd import pledge, unveil
except ModuleNotFoundError:
    def pledge(*args):
        pass

    def unveil(*args):
        pass

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


async def process_msg(text):
    embed = None
    too_many_calls = False

    # Get list of ordered, unique, normalized matches.
    text = text.lower()
    matches = re.findall(r"(?:^|\s)%%([\w:\/\.-]+)", text)
    if matches == []:
        return None

    unique_matches = []
    for m in matches:
        if m not in unique_matches:
            unique_matches.append(m)

    if len(unique_matches) > 9:
        unique_matches = unique_matches[:9]
        too_many_calls = True

    embed = discord.Embed(color = 0x55FFFF)

    for match in unique_matches:
        if match.endswith("."):
            match = match[:-1]  # Could be part of regex.

        something_found = False
        absolute_path_found = False

        # Check against absolute file paths.
        potential = re.match(r"^(?:[a-z:]:)?\/(.*?)/?$", match)
        if potential is not None:
            normalized = "/" + potential.group(1)

            path = paths.get(normalized)
            if path is not None:
                embed = embed_append_path(embed, path)
                something_found = True
                absolute_path_found = True

        # Check against last segments of file paths,
        # ie. `Doc` and `WallPaperFish.HC.Z`.
        if not absolute_path_found:
            path = paths.get(match)
            if path is not None:
                embed = embed_append_path(embed, path)
                something_found = True

        # Check against symbol table.
        symbol = symbols.get(match)
        if symbol is not None:
            embed = embed_append_symbol(embed, symbol)
            something_found = True

        if not something_found:
            embed = embed_append_error(embed, f"Symbol, path, or path segment not found: {match}")

    if too_many_calls:
        embed = embed_append_error(embed, "Too many calls, trimmed output.")

    return embed


# Embeds =======================================================================
def embed_append_symbol(e: discord.Embed, symbol) -> discord.Embed:
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

    e.add_field(name=symbol['symbol'], value=text, inline=False)
    return e


def embed_append_path(e: discord.Embed, path) -> discord.Embed:
    file_types = {
        "HC": "HolyC",
        "TXT": "Text",
        "GRA": "Graphics",
        "BMP": "Windows Bitmap",
        "DD": "DolDoc",
        "IN": "Input",
        "BIN": "Binary",
        "CPP": "C++",
    }

    file_name_parts = path.split(".")
    if len(file_name_parts) > 1:
        url_path = file_name_parts[0] + ".html"

        file_type = file_types.get(file_name_parts[1])
        if file_type is None:
            file_type = file_name_parts[1]

        if file_name_parts[-1] == "Z":
            file_type = f"{file_type} (Compressed)"
    
    else:
        url_path = path
        file_type = "Directory"


    url = "https://templeos.holyc.xyz/Wb" + url_path
    text = f"Type: {file_type}\nPath: [::{path}]({url})"

    path_name = path.split("/")[-1] or "/"
    e.add_field(name=path_name, value=text, inline=False)
    return e


def embed_append_error(e: discord.Embed, error_message) -> discord.Embed:
    e.add_field(name=common.EMBED_ERROR_STR, value=error_message, inline=False)
    return e


# Client and callbacks =========================================================
client = discord.Client()

@client.event
async def on_ready():
    if platform.system() == "OpenBSD":
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

with open("symbol.json", "r") as f:
    tos_data = json.load(f)

# Make map of symbols. Keys are lowercased symbols.
symbols = {}
for s in tos_data["symbols"]:
    symbols[s["symbol"].lower()] = s

# Make map of full paths, for each value, the keys are:
#   - the lowercased path,
#   - The lowercased last segment of the path.
paths = {}
for p in tos_data["paths"]:
    paths[p.lower()] = p

    last_segment = p.split("/")[-1].lower()
    if last_segment != "":
        paths[last_segment] = p

        # ie. charter.dd.z == charter.dd == charter
        splits = last_segment.split(".")
        for i in range(0, len(splits)):
            paths[".".join(splits[:-i])] = p


if __name__ == "__main__":
    client.run(config["token"])
