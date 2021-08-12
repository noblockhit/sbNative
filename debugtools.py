import inspect
import os
import time
import atexit

global terminalStacking
terminalStacking = False

global prevLogInfo
global prevLog

prevLogInfo = {
    "infoName":None,
    "tracebackDepth":None,
    "seperator":None,
    "end":None,
    "args":[],
    "fileName":None,
    "lineNumber":None
}

prevLog = ["", 1]

def switchTerminalStacking():
    global terminalStacking
    terminalStacking = not terminalStacking
    if not terminalStacking:
        print(f"{prevLog[0]} [{prevLog[1]}x]")
    

    def printNewlineOnTerminalStack():
        global terminalStacking
        if terminalStacking:
            print()
        
    atexit.register(printNewlineOnTerminalStack)


def __reprAndSplitArgs(args, indentStartEnd=None):
    ret = []

    currIndentLvl = 0

    if indentStartEnd:
        srt, end = indentStartEnd
        for a in args:
            lnsUnsplitted = str(a).replace(
                srt, srt + "\p").replace(end, "\p" + end)
            lines = lnsUnsplitted.split("\p")
            for l in lines:
                currIndentLvl -= l.count(end) * 4
                ret.append(" " * currIndentLvl + l)
                currIndentLvl += l.count(srt) * 4
            
    else:
        for a in args:
            ret += [str(a)]
    return ret


def __baseLoggingFunc(infoName, tracebackDepth, seperator, maxOccupyableWidthPortion, end, *args):
    global terminalStacking

    call = inspect.getframeinfo(inspect.stack()[tracebackDepth][0])
    fileName, lineNumber = call.filename, call.lineno

    if terminalStacking:
        global prevLogInfo
        global prevLog

        currLogInfo = {
            "infoName":infoName,
            "tracebackDepth":tracebackDepth,
            "seperator":seperator,
            "end":end,
            "args":args,
            "fileName":fileName,
            "lineNumber":lineNumber
        }

        if currLogInfo == prevLogInfo:
            prevLog[1] += 1
            print(f"{prevLog[0]} [{prevLog[1]}x]", end="\r")
            return

        if len(prevLog[0]):
            print(f"{prevLog[0]}")

        prevLogInfo = currLogInfo
    
    path = fileName.replace("\\", "/") + ":" + str(lineNumber)
    arrow = " --> "

    if infoName:
        logString = f"LOG ({infoName}): "
    else:
        logString = f"LOG: "

    argStrings = __reprAndSplitArgs(args)
    consoleWidth = os.get_terminal_size()[0]
    occupiedLogLength = sum([len(s)+len(seperator) for s in argStrings])-len(seperator)

    if occupiedLogLength+len(path)+len(arrow)+len(logString)+len(end) > consoleWidth*maxOccupyableWidthPortion:
        seperator = "\n"
        logString += "\n"
        arrow = "\n" + arrow[1:]
        argStrings = __reprAndSplitArgs(args, "()")
        argStrings = __reprAndSplitArgs(argStrings, "[]")

    argStr = seperator.join(argStrings).replace("\p", "")

    logString += f"{argStr}{end}{arrow}{path}"

    if terminalStacking:
        print(logString, end="\r")
        prevLog = [logString, 1]
    else:
        print(logString)


def log(*args, depth=2):
    __baseLoggingFunc(None, depth, " | ", .9, "", *args)


def ilog(info, *args, depth=2, end=""):
    __baseLoggingFunc(info, depth, " | ", .9, end, *args)


def timer(func):
    def wrapper(*args, **kwargs):
        begin = time.time()
        ret = func(*args, **kwargs)
        ilog(f"Executing `{func.__name__}` took",time.time() - begin, depth = 3, end=" seconds")
        return ret
    return wrapper

def __clsRepr(cls):
    isLogCall = isFromCall("log")
    ret = f"{type(cls).__name__}("

    subObjects = {**cls.__dict__,**{name:classAttr for name, classAttr in type(cls).__dict__.items() if not callable(classAttr) and not name.startswith("__")}}

    for k, v in subObjects.items():
        if k in cls.__excludeReprVarNames__:
            continue
        
        ret += f"{repr(k)}: {repr(v)}, "
        if isLogCall:
            ret += "\p"

    if len(subObjects) == 0:
        return ret + ")"

    ret = ret.strip("\p")

    remvLastChars = -1

    if len(subObjects) > 1:
        remvLastChars -= 1

    if remvLastChars == 0:
        return ret + ")"
    return ret[:remvLastChars] + ")"

def isFromCall(funcName):
    funcs = [c.function for c in inspect.stack()]
    return funcName in funcs


def cleanRepr(*exclude):
    def decorator(cls):
        cls.__excludeReprVarNames__ = exclude
        cls.__repr__ = __clsRepr
        return cls
    return decorator
