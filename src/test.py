""" Tests to be run with pytest. Eg. `pytest test.py -v -s`

Hypothesis tests will take a long time to complete, as they are running a lot of
tests and are spinning up / tearing down async loops.
"""

import asyncio
import re

import pytest
import hypothesis
import discord

import main
import common

# ==============================================================================
def field_compare(f1, f2):
    return f1.name == f2.name and f1.value == f2.value and f1.inline == f2.inline

# ==============================================================================


def test_process_msg_returns_multiple_result_types():
    result = asyncio.run(main.process_msg("%%Adam"))
    assert isinstance(result, discord.Embed)
    assert len(result.fields) == 2
    assert "Funct Public" in result.fields[1].value
    assert "Directory" in result.fields[0].value


def test_process_msg_handles_root_directory():
    variations = [f"%%{char}:/" for char in ":ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    variations.append("%%/")
    variations += [v + "." for v in variations]

    for v in variations:
        result = asyncio.run(main.process_msg(v))
        assert isinstance(result, discord.Embed)
        assert len(result.fields) == 1
        assert result.fields[0].name == "/"


# This would fail on cases that have the same output but are called
# differently, ie. "/" and "C:/". This should be fixed.
def test_process_msg_combines_common_cases():
    for s in ("Adam", "Cd", "/", "Man", "RAX", "DocClear"):
        for i in range(1, 100):
            previous_fields = []
            result = asyncio.run(main.process_msg(f"%%{s} %%cd some text" * i))
            for f1 in result.fields:
                for f2 in previous_fields:
                    assert field_compare(f1, f2) == False
                previous_fields.append(f1)


def test_process_msg_finds_files_with_incomplete_extensions():
    variations = ["charter", "charter.dd", "charter.dd.z"]

    previous_results = []
    for v in variations:
        result = asyncio.run(main.process_msg(f"%%{v}"))
        for previous_result in previous_results:
            assert (len(result) == len(previous_result)
                and field_compare(result.fields[0], previous_result.fields[0]))
        previous_results.append(result)


#def test_process_msg_returns_result_for_all_complete_paths():
#    with open("symbols.json") as f:
#        for path in json.load(f)["paths"]:
#            if path == "/":
#                continue
#            r = asyncio.run(main.process_msg(f"Some text %%{path} ..."))
#            field_names = [f.name for f in r.fields]
#            found = False
#            for name in field_names:
#                m = common.BASENAME_NO_EXTENSIONS_PATTERN.match(name)
#                assert(m is not None)
#                if m.group(0) == name:
#                    found = True
#            assert found == True
#
#
#def test_process_msg_returns_result_for_all_symbols():
#    with open("symbols.json") as f:
#        for s in json.load(f)["symbols"]:
#            print(s)
#            r = asyncio.run(main.process_msg(f"Some text %%{s['name']} ..."))
#            field_names = [f.name for f in r.fields]
#            assert s["name"] in field_names


# Hypothesis ===================================================================

@hypothesis.given(hypothesis.strategies.text())
@hypothesis.settings(max_examples=10_000, deadline=1000)
@hypothesis.example("%%::/Demo/WallPaperFish.HC.Z")
@hypothesis.example("%%(TinkerOS)c")
def test_hypothesis_process_msg_returns_none_or_embed(s):
    result = asyncio.run(main.process_msg(s))
    if isinstance(result, discord.Embed):
        assert len(result.fields) > 0
    else:
        assert result is None
