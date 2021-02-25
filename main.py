import asyncio
import platform
import dataclasses
import pathlib
import json
import re

import discord
import appdirs
if platform.system() == "OpenBSD":
    import openbsd


# todo: add full and partial paths, fuzzy matching.
async def process_msg(msg):
    for match in re.findall(r"(?:^|\s)%% ?([\w:\/\.]+)", msg.content):
        if "/" in match:
            # Check against file paths.
            try:
                normalized = "/" + re.match(r"^(?:[A-Z:]:)?\/(.*?)/?$", match).group(1).lower()
            except AttributeError:
                await msg.channel.send(embed = error_embed("Invalid path"))
                continue

            path = paths.get(normalized)
            if path is not None:
                await msg.channel.send(embed = path_embed(path))
            else:
                await msg.channel.send(embed = error_embed("Path not found."))
        else:
            # Check against symbol table.
            symbol = symbols.get(match.lower())
            if symbol is not None:
                await msg.channel.send(embed = symbol_embed(symbol))
                continue
            else:
                await msg.channel.send(embed = error_embed("Symbol not found."))




# Embeds =======================================================================
def symbol_embed(symbol) -> discord.Embed:

    e = discord.Embed()
    e.color = 0x55ffff

    description = "Symbol: "
    if "file" in symbol:
        path = symbol["file"][2:]
        if "." in path:
            path = path.split(".")[0] + ".html"
        url = "https://templeos.holyc.xyz/Wb" + path + "#l" + symbol["line"]
        description += f'[{symbol["symbol"]}]({url})'
    else:
        description += f'{symbol["symbol"]}'

    description += f"\nType: {symbol['type']}"

    e.description = description
    return e


def path_embed(path) -> discord.Embed:
    e = discord.Embed()
    e.color = 0x55ffff
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
            file_type = file_type + ", compressed"
    
    else:
        url_path = path
        file_type = "Directory"


    url = "https://templeos.holyc.xyz/Wb" + url_path
    description = f'Path: [::{path}]({url})\nType: {file_type}'

    e.description = description
    return e

def error_embed(error_message) -> discord.Embed:
    return discord.Embed(description=error_message)

# Client and callbacks =========================================================

client = discord.Client()

@client.event
async def on_ready():
    # Setup unveil and pledge.
    if platform.system() == "OpenBSD":
        openbsd.pledge("stdio inet dns prot_exec")


@client.event
async def on_message(msg):
    await process_msg(msg)


if __name__ == "__main__":

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

    # Create dictionary of symbols and paths. Key is lowercase name.
    with open("symbol.json", "r") as f:
        tos_data = json.load(f)

    symbols = {}
    for s in tos_data["symbols"]:
        symbols[s["symbol"].lower()] = s

    paths = {}
    for p in tos_data["paths"]:
        paths[p.lower()] = p

    client.run(config["token"])

