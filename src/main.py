""" The TTD2 Discord chat bot. """

import asyncio
import pathlib
import re
import json

import appdirs
import cachetools
import discord
import openbsd

import common
import data

# ==============================================================================

db_con, db_cur = data.create_in_memory_database()
client = discord.Client()
recent_replies = cachetools.FIFOCache(maxsize=50)

# ==============================================================================

async def change_status_task():
    while True:
        r = data.get_random_symbol_or_path('TempleOS_5.3', db_con, db_cur)
        for s in ["%%<path or symbol>", "Eg: %%"+r]:
            await client.change_presence(activity=discord.Game(s))
            await asyncio.sleep(15)


def normalize_TOS_version(tv):
    if tv == "":
        return common.DEFAULT_TOS_VERSION

    index = [s.lower() for s in common.TOS_VERSIONS].index(tv.lower())
    if index is not None:
        return common.TOS_VERSIONS[index]


async def process_msg(text):
    # A "lookup" is a (TOS_version, needle) pair.
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
    for (TOS_version, needle) in lookups:
        try:
            TOS_version = normalize_TOS_version(TOS_version)
        except ValueError:
            embed = embed_append_error(
                embed,
                f"TOS version not found.\nValid versions: {','.join(common.TOS_VERSIONS)}"
            )
            continue

        path_matches, symbol_matches = data.look_up(TOS_version, needle, db_con, db_cur)

        if path_matches == [] and symbol_matches == []:
            embed = embed_append_not_found(embed, needle, TOS_version)
        else:
            for sm in symbol_matches:
                embed = embed_append_symbol(embed, sm, TOS_version)

            for pm in path_matches:
                embed = embed_append_path(embed, pm, TOS_version)

        if len(embed.fields) > common.MAX_FIELDS_PER_MESSAGE:
            for i in range(len(embed.fields)-common.MAX_FIELDS_PER_MESSAGE+1):
                embed.remove_field(-1)

            embed = embed_append_error(embed, "Too many results, trimmed output.")
            break
            
    if too_many_lookups:
        embed = embed_append_error(embed, "Too many needles, trimmed output.")

    return embed

# Embeds =======================================================================

def embed_append_symbol(embed, symbol, TOS_version):
    text = str()
    if TOS_version != common.DEFAULT_TOS_VERSION:
        text += f"(Version: {TOS_version})\n"
    text += f"Type: {symbol['type']}\n"

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
        if symbol["file"] is not None:
            link = data.path_to_link(symbol["file"], symbol["line"], TOS_version)
            line_str = ", line " + str(symbol["line"])
            text += f"Definition: [{symbol['file']}{line_str}]({link})\n"

    embed.add_field(name=symbol['name'], value=text, inline=False)
    return embed


def embed_append_path(embed, path, TOS_version):
    text = str()
    if TOS_version != common.DEFAULT_TOS_VERSION:
        text += f"(Version: {TOS_version})\n"

    link = data.path_to_link(path["full_path"], None, TOS_version)
    text += f"Type: {path['type']}\nPath: [{path['full_path']}]({link})"

    embed.add_field(name=path['basename'], value=text, inline=False)
    return embed


def embed_append_not_found(embed, needle, TOS_version):
    text = str()
    if TOS_version != common.DEFAULT_TOS_VERSION:
        text += f"(Version: {TOS_version})\n"
    text += f"Path or symbol not found: {needle}\n"

    embed.add_field(name="Not found.", value=text, inline=False)
    return embed


def embed_append_error(embed, error_message):
    embed.add_field(name=common.EMBED_ERROR_STR, value=error_message, inline=False)
    return embed

# ==============================================================================

@client.event
async def on_ready():
    openbsd.pledge("stdio inet dns prot_exec")
    await client.loop.create_task(change_status_task())


@client.event
async def on_message(msg):
    embed = await process_msg(msg.content)
    if embed is not None:
        reply = await msg.reply(embed = embed, mention_author=False)
        recent_replies[msg] = reply


@client.event
async def on_message_edit(old_msg, new_msg):
    embed = await process_msg(new_msg.content)
    reply = recent_replies.get(old_msg)

    if embed is not None:
        if reply is not None:
            await reply.edit(embed = embed)
        else:
            reply = await new_msg.reply(embed = embed, mention_author=False)
            recent_replies[new_msg] = reply
    else:
        if reply is not None:
            await reply.delete()
            del recent_replies[new_msg]


@client.event
async def on_message_delete(msg):
    reply = recent_replies.get(msg)
    if reply is not None:
        await reply.delete()
        del recent_replies[msg]


# ==============================================================================

if __name__ == "__main__":
    config_dir = pathlib.Path(appdirs.user_config_dir("TTD2_bot"))
    config_file = config_dir.joinpath("config.json")

    with open(config_file, "r") as f:
        config = json.load(f)

    client.run(config["token"])
