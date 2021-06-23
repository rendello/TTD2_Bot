""" The TTD2 Discord chat bot. """

import asyncio
import pathlib
import re
import json
import functools

import appdirs
import discord
import openbsd

import common
import data

# ==============================================================================

db_con, db_cur = data.create_in_memory_database()
client = discord.Client()

# ==============================================================================

async def change_status_task():
    while True:
        r = data.get_random_symbol_or_path('TempleOS_5.3', db_con, db_cur)
        for s in ["%%<path or symbol>", "Eg: %%"+r]:
            await client.change_presence(activity=discord.Game(s))
            await asyncio.sleep(15)


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
        path_matches, symbol_matches = data.look_up("TempleOS_5.3", lookup, db_con, db_cur)

        if path_matches == [] and symbol_matches == []:
            embed = embed_append_not_found(embed, lookup)
        else:
            for pm in path_matches:
                embed = embed_append_path(embed, pm)

            for sm in symbol_matches:
                embed = embed_append_symbol(embed, sm)
            

    if too_many_lookups:
        embed = embed_append_error(embed, "Too many lookups, trimmed output.")

    return embed


# Embeds =======================================================================
def embed_append_symbol(embed, symbol):

    text = f"Type: {symbol['type']}\n"

    if symbol["type"] == "OpCode":
        text += \
f"""
Reference: [x86 reference: {symbol['name']}](https://www.felixcloutier.com/x86/{symbol['name'].lower()})

See [::/Doc/ASM.DD.Z](https://templeos.holyc.xyz/Wb/Doc/Asm.html)
And [::/Compliler/OpCodes.DD.Z](https://templeos.holyc.xyz/Wb/Compiler/OpCodes.html)\n
"""
    elif symbol["type"] == "Reg":
        l = ("https://en.wikibooks.org/wiki/X86_Assembly/X86_Architecture"
        +"#General-Purpose_Registers_(GPR)_-_16-bit_naming_conventions")
        text += f"Reference: [Wikibooks: x86 Architecture]({l})\n"
    else:
        text += f"Definition: {symbol['file']}\n"

    embed.add_field(name=symbol['name'], value=text, inline=False)
    return embed


def embed_append_path(embed, path):
    text = f"Type: {path['type']}\nPath: {path['full_path']}"

    embed.add_field(name=path['basename'], value=text, inline=False)
    return embed


def embed_append_not_found(embed, needle):
    text = f"Path or symbol not found: {needle}\n\n"

    embed.add_field(name="Not found.", value=text, inline=False)
    return embed


def embed_append_error(embed, error_message):
    embed.add_field(name=common.EMBED_ERROR_STR, value=error_message, inline=False)
    return embed


# Client and callbacks =========================================================

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
