A Discord chat bot for the TempleOS Technical Discussion Server. Returns
information on a directory or symbol, with a web link to the definition or
location within TempleOS, if applicable.

INSTALLATION:
    The original TTD bot link is not public for stability reasons, but the bot
    can be self-hosted. Simply install the required packages and run `main.py`.

    The bot is sandboxed with `pledge` and `unveil` when run on OpenBSD.


USAGE:
    Call with `%%` followed by a TempleOS file path, file name, directory,
    variable, function name, or any other symbol. Eg:

    >> %%::/Demo/Graphics/WallPaperFish.HC.Z
    >> %%wallpaperfish.hc.z
    >> %%DocClear
    >> %%RAX
    >> Yeah, the function is called %%cd.
    >> %%Adam is both a directory and a symbol.

Q&A:
    Q: Where is TTD1 bot?
    A: We don't talk about TTD1 bot.

    Q: Where is the TempleOS Technical Discussion server link?
    A: There's no public link, but contact me if you want an invite. It's a small,
       moderated server where we talk about TempleOS and HolyC and related tech.

    Q: Why can't I see its messages?
    A: You need to have Discord embeds enabled in your settings.

LICENSE:
    Copyright 2021 Rendello

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
