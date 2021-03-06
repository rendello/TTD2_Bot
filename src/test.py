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
def field_compare(f1, f2):
    return f1.name == f2.name and f1.value == f2.value and f1.inline == f2.inline

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


def test_process_msg_combines_common_cases():
    for s in ("Adam", "Cd", "/", "Man", "RAX", "DocClear"):
        for i in range(1, 100):
            previous_fields = []
            result = asyncio.run(main.process_msg(f"%%{s} %%cd some text" * i))
            for f1 in result.fields:
                for f2 in previous_fields:
                    assert field_compare(f1, f2) == False
                previous_fields.append(f1)


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
