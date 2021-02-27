# SPDX-License-Identifier: BSD-2-Clause

""" The TTD2 Discord chat bot. """

import asyncio
import platform
import pathlib
import json
import re

import discord
import appdirs
if platform.system() == "OpenBSD":
    import openbsd

# todo: fuzzy matching.
# todo: allow multiple path segments per name.
# todo: allow reprocessing message on edit.

# ==============================================================================
async def process_msg(text):
    embed = None

    matches = re.findall(r"(?:^|\s)%%([\w:\/\.]+)", text)
    if matches == []:
        return None

    embed = discord.Embed(color = 0x55FFFF)
    for match in matches:

        if match.endswith("."):
            match = match[:-1]  # Could be part of regex.

        something_found = False

        # Check against absolute file paths.
        potential = re.match(r"^(?:[A-Z:]:)?\/(.*?)/?$", match)
        if potential is not None:
            normalized = "/" + potential.group(1).lower()

            path = paths.get(normalized)
            if path is not None:
                embed = embed_append_path(embed, path)
                something_found = True

        # Check against last segments of file paths,
        # ie. `Doc` and `WallPaperFish.HC.Z`.
        if "/" not in match:
            path = paths.get(match.lower())
            if path is not None:
                embed = embed_append_path(embed, path)
                something_found = True

        # Check against symbol table.
        symbol = symbols.get(match.lower())
        if symbol is not None:
            embed = embed_append_symbol(embed, symbol)
            something_found = True

        if not something_found:
            embed = embed_append_error(embed, f"Symbol, path, or path segment not found: {match}")

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

    text = f"Type: {symbol['type']}\nDefinition: {path_link}"

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
    e.add_field(name="[Error]", value=error_message, inline=False)
    return e


# Client and callbacks =========================================================
client = discord.Client()

@client.event
async def on_ready():
    if platform.system() == "OpenBSD":
        openbsd.pledge("stdio inet dns prot_exec")


@client.event
async def on_message(msg):
    embed = await process_msg(msg.content)
    if embed is not None:
        await msg.channel.send(embed = embed)


# ==============================================================================

# Load token from config. If not available, prompt for token and
# create config.
config_dir = pathlib.Path(appdirs.user_config_dir("TTD_bot"))
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

    last_segment = p.split("/")[-1]
    if last_segment != "":
        paths[last_segment.lower()] = p

if __name__ == "__main__":
    client.run(config["token"])

