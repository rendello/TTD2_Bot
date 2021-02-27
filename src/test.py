# SPDX-License-Identifier: BSD-2-Clause

""" Tests to be run with pytest. Eg. `pytest test.py -v -s`

Hypothesis tests will take a long time to complete, as they are running a lot of
tests and are spinning up / tearing down async loops.
"""

import asyncio

import pytest
import hypothesis
import discord

import main

# ==============================================================================

def test_process_msg_returns_multiple_result_types():
    result = asyncio.run(main.process_msg("%%Adam"))
    assert isinstance(result, discord.Embed)
    assert len(result.fields) == 2
    assert "Directory" in result.fields[0].value
    assert "Funct Public" in result.fields[1].value


def test_process_msg_handles_root_directory():
    variations = [f"%%{char}:/" for char in ":ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    variations.append("%%/")
    variations += [v + "." for v in variations]

    for v in variations:
        result = asyncio.run(main.process_msg(v))
        assert isinstance(result, discord.Embed)
        assert len(result.fields) == 1
        assert result.fields[0].name == "/"


# Hypothesis ===================================================================

@hypothesis.given(hypothesis.strategies.text())
@hypothesis.settings(max_examples=10_000, deadline=1000)
@hypothesis.example("%%::/Demo/WallPaperFish.HC.Z")
def test_process_msg_returns_none_or_embed(s):
    result = asyncio.run(main.process_msg(s))
    if isinstance(result, discord.Embed):
        assert len(result.fields) > 0
    else:
        assert result is None
