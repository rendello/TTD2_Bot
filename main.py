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
        symbol = symbols.get(match.lower())
        if symbol is not None:
            await msg.channel.send(embed = symbol_embed())
        else:
            await msg.channel.send("Symbol not found")


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

    # Create dictionary of symbols. Key is lowercase name.
    with open("symbol.json", "r") as f:
        symbol_list = json.load(f)

    symbols = {}
    for s in symbol_list:
        symbols[s["symbol"].lower()] = s

    client.run(config["token"])

