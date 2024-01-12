                            _____ _____ ____  ___ 
                           |_   _|_   _|    \|_  |
                             | |   | | |  |  |  _|
                             |_|   |_| |____/|___|


TTD2 is a Discord chat bot that returns information on TempleOS files,
directories and symbols.


INSTALLATION:
    - `python3.xx -m pip install appdirs cachetools discord`
    - `cd /src`
    - `python 3.xx main.py` (give it a token to use and save)
    - (restart it when it inevitably crashes)

    The bot is sandboxed with `pledge` and `unveil` when run on OpenBSD.

USAGE:
    Call with `%%` followed by a TempleOS file path, file name, directory,
    variable, function name, or any other symbol. Eg:

    >> %%::/Demo/Graphics/WallPaperFish.HC.Z
    >> %%wallpaperfish.hc.z
    >> %%DocClear
    >> %%RAX
    >> Two important functions are %%cd and %%dir.
    >> %%Adam is both a directory and a symbol.

    TTD2 will respond to the calling message with:
    - The item's type (Directory, Funct Public, Opcode, etc.)
    - The items location / definition location, with web link.


LICENSE:
    Copyright 2024 Rendello

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
