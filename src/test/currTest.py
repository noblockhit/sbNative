
from pathlib import Path
import sys
from functools import lru_cache

sys.path.append(
    r"D:\AA_CODING\python\Projects\codebases\sbNative\src\sbNative")

import runtimetools
import debugtools

# tmr = debugtools.timePlotter(debugtools.tPlotArgs.TIME, trackArgs=[0])

# @tmr.timer
# def startfib(n):
#     fib(n)

# # @lru_cache(maxsize=100)
# def fib(n):
#    if n <= 1:
#        return n
#    else:
#        return fib(n-1) + fib(n-2)

# for i in range(14,26):
#     startfib(i)

# tmr.show()


# d = runtimetools.bidirectionalDict(
#     Richard = ["Dick", "Rick"],
#     Annamarie = ["Marie", "Anna", "Ann"]
# )

# print(d.Richard, d["Richard"])
# print(d.Rick, d["Rick"])
# print(d.Dick, d["Dick"])

# print(d.Annamarie, d["Annamarie"])
# print(d.Marie, d["Marie"])
# print(d.Anna, d["Anna"])
# print(d.Ann, d["Ann"])

# myIter = [
#             ["be", "was", "were", "been"],
#             ["stay", "stood", "have stood"]
#         ]

# print(runtimetools.LanguageFormatter.enumerateCollection(myIter, recursive=True))

import os
lineSplitSign = "\uf8ff"

# somename(
#     item = somevalue
# )
#
#


def formatDictToEqualSigns(d):
    ret = []
    for k,v in d.items():
        if isinstance(v, dict):
            ret.append(f"{k} = {tuple(formatDictToEqualSigns(v))}")
        else:
            ret.append(f"{k} = {v}")
    return ret


def computeLineBreakIndents(args: tuple, kwargs: dict, indentStartEnd=["()", "[]", "{}"], isOverflow = False) -> list:
    args = tuple(args) + tuple(formatDictToEqualSigns(kwargs))
    
    if not isOverflow:
        return "(" + f", ".join(args) + f")"
    
    contentStr = f"({lineSplitSign}" + f", {lineSplitSign}".join(args) + f"{lineSplitSign})"
    contentStr = contentStr.replace(lineSplitSign, "\n")
    
    INDENTLVL = 4
    OPENERS = [i[0] for i in indentStartEnd]
    ENDERS = [i[1] for i in indentStartEnd]
    
    currIndent = 0
    indentStack = ""
    newContentStr = ""


    for idx, c in enumerate(contentStr):
        if c in OPENERS and len(contentStr) > idx+1 and contentStr[idx+1] in [lineSplitSign, "\n"]:
            currIndent += 1
            indentStack += c

        elif c in ENDERS and len(indentStack) > 0 and idx > 2 and (contentStr[idx-1] in [lineSplitSign, "\n"]) and OPENERS[ENDERS.index(c)] == indentStack[-1]:
            currIndent -= 1
            indentStack = indentStack[:-1]
            newContentStr = newContentStr[:-INDENTLVL]
        
        newContentStr += c
        if c in [lineSplitSign, "\n"]:
            newContentStr += " " * (currIndent * INDENTLVL)

    return newContentStr



print(computeLineBreakIndents(
    (
        f"somestring1that goes on afterwords",
    ),
    {
        f"something else<- with a splitsign here": f"that isa kwarg",
        f"with evenmore characters": {
            f"which occupywaay to much space": "because they are nested dicts"
        }
    }
, isOverflow = True))

# print(computeLineBreakIndents(
#     (
#         f"somestring1{lineSplitSign}that goes on afterwords",
#     ),
#     {
#         f"something else{lineSplitSign}<- with a split{lineSplitSign}sign here": f"that is{lineSplitSign}a kwarg",
#         f"with even{lineSplitSign}more characters": f"which occupy{lineSplitSign}waay to much space"
#     }
# , isOverflow = True))