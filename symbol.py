#import re
#
#with open("symbols_clean") as f:
#    lines = f.readlines()
#
#for l in lines:
#    symbol = re.findall("^[\w\/]+", l)[0]
#    p = re.search(r'^[^\"]+\"\,A=\"([A-Za-z\=\:\/\.]+)\,(\d+)\"', l)
#    classification = re.findall(r"\s+([a-zA-Z ]+) $", l)[0]
#    print("{")
#    print(f'    "symbol": "{symbol}",')
#
#    if p is not None:
#        print(f'    "file": "{p.group(1)}",')
#        print(f'    "line": "{p.group(2)}",')
#    print(f'    "type": "{classification}"')
#    print("},")

import json

with open("symbol.json") as f:
    j = json.load(f)
    files = []

    #for item in j:
    #    t = item["type"]
    #    if t not in types:
    #        types.append(t)
    #print(types)

    #for item in j:
    #    try:
    #        t = item["file"]
    #        if t not in files:
    #            files.append(t)
    #    except:
    #        pass

    #for f in files:
    #    print(f)

    symbols = []
    for item in j:
        t = item["symbol"]
        if t.lower() not in symbols:
            symbols.append(t)
        else:
            print(f"NOOOOO {t} = {t.lower()}")
