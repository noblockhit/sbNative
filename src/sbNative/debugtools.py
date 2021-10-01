import inspect
import os,sys
import time
import atexit
import typing

global terminalStacking
terminalStacking = False

global prevLogInfo
global prevLog

prevLogInfo = {
    "infoName": None,
    "tracebackDepth": None,
    "separator": None,
    "end": None,
    "args": [],
    "fileName": None,
    "lineNumber": None
}

prevLog = ["", 1]


def switchTerminalStacking():
    '''
    Terminalstacking is a feature that prevents the logging function from spamming the terminal with useless information.
    If the same things are logged in the same line, file, back to back and this feature is enabled, the information will not be printed again,
    it will rather "edit" the existing line and add `[2x]` `[3x]` `[4x]` ... `[nx]` after the location of the log.
    '''
    global terminalStacking
    terminalStacking = not terminalStacking
    if not terminalStacking:
        print(f"{prevLog[0]} [{prevLog[1]}x]")

    def printNewlineOnTerminalStack():
        global terminalStacking
        if terminalStacking:
            print()

    atexit.register(printNewlineOnTerminalStack)
    return terminalStacking


def computeLinebreakIndents(args: object, indentStartEnd: typing.Union[str, typing.Sequence[typing.Tuple[str, str]]] = None):
    '''
    Used for clean representation of e.g. Lists (indentStartEnd = "[]") if multiple lines are necessary.
    If `indentStartEnd` is `None` all the arguments will be combined to a list of newlines.
    IndentStartEnd must be a 2 item sequence of single characters. Multi Character support might be supported in the future.
    '''
    ret = []

    currIndentLvl = 0

    if indentStartEnd:
        srt, end = indentStartEnd
        for a in args:
            lnsUnsplitted = str(a).replace(
                srt, srt + "\p").replace(end, "\p" + end).replace(end + ", ", end + ",\p")
            lines = lnsUnsplitted.split("\p")
            for l in lines:
                currIndentLvl -= l.count(end) * 4
                ret.append(" " * currIndentLvl + l)
                currIndentLvl += l.count(srt) * 4

    else:
        for a in args:
            ret += [str(a)]
    return ret


def __baseLoggingFunc(
        infoName: typing.Union[str, None],
        tracebackDepth: int,
        separator: str,
        maxOccupyableWidthPortion: float,
        end: str,
        *args: object):
    '''
    This is the base of the logging function,
    like `log` and `ilog` (infolog). It is almost redundant to use this,
    because the `log` and `ilog` functions will likely satisfy your needs.
    '''
    global terminalStacking

    call = inspect.getframeinfo(inspect.stack()[tracebackDepth][0])
    fileName, lineNumber = call.filename, call.lineno

    if terminalStacking:
        global prevLogInfo
        global prevLog

        currLogInfo = {
            "infoName": infoName,
            "tracebackDepth": tracebackDepth,
            "separator": separator,
            "end": end,
            "args": args,
            "fileName": fileName,
            "lineNumber": lineNumber
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
        logString = f"LOG ({repr(infoName)}): "
    else:
        logString = f"LOG: "

    argStrings = computeLinebreakIndents(args)
    consoleWidth = os.get_terminal_size()[0]
    occupiedLogLength = sum([len(s)+len(separator)
                            for s in argStrings])-len(separator)

    if occupiedLogLength+len(path)+len(arrow)+len(logString)+len(end) > consoleWidth*maxOccupyableWidthPortion:
        separator = "\n"
        logString += "\n"
        arrow = "\n" + arrow[1:]
        argStrings = computeLinebreakIndents(args, "()")
        argStrings = computeLinebreakIndents(argStrings, "[]")
        argStrings = computeLinebreakIndents(argStrings, "{}")

    argStr = separator.join(argStrings).replace("\p", "")

    logString += f"{argStr}{end}{arrow}{path}"

    if terminalStacking:
        print(logString.split("\n")[-1], end="\r")
        prevLog = [logString, 1]
    else:
        print(logString)


def log(*args: object, depth: int = 2):
    '''
    Prints all the arguments given to the console and the file + line of the call.
    Supports more advanced logging when paired with the `cleanRepr` class decorator.
    '''
    __baseLoggingFunc(None, depth, " | ", .9, "", *args)


def ilog(info: object, *args: object, depth: int = 2, end: str = ""):
    '''
    Prints all the arguments given to the console and the file + line of the call.
    First argument will be used to represent what is logged. Supports more advanced logging when paired with the `cleanRepr` class decorator.
    '''
    __baseLoggingFunc(info, depth, " | ", .9, end, *args)


def timer(func: callable):
    '''
    A simple decorator for timing the execution time of a function or method. Flexes the `ilog` function.
    '''
    def wrapper(*args, **kwargs):
        begin = time.time()
        ret = func(*args, **kwargs)
        ilog(f"Executing `{func.__name__}` took",
             time.time() - begin, depth=3, end=" seconds")
        return ret

    return wrapper


def __clsRepr(cls: type):
    '''
    This is what the `__repr__` method of the class decorated with `cleanRepr` decorator is replaced with.
    Supports newlines with the logging functions.
    '''
    isLogCall = isFromCall("log")
    ret = f"{type(cls).__name__}("

    subObjects = {**cls.__dict__, **{name: classAttr for name, classAttr in type(
        cls).__dict__.items() if not callable(classAttr) and not name.startswith("__")}}

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

def __clsLog(self, *args):
    if len(args) == 0:
        return log(self, depth=3)
    return ilog(self, *args, depth=3)

def isFromCall(funcName: str):
    '''
    Gets if a function with the name `funcName` is in the callstack.
    Used by `__clsRepr` to determine if it should add markers in the form of `\\p` where newlines can be added if the logging string is too long.
    '''
    funcs = [c.function for c in inspect.stack()]
    return funcName in funcs


def cleanRepr(*exclude: typing.Iterable[str]):
    '''
    A decorator which makes the representation of your class as clean as possible.
    If you don't want specific class or instance variables to be included, you may specify them as arguments for this function.
    '''
    def decorator(cls):
        cls.__excludeReprVarNames__ = exclude
        cls.__repr__ = __clsRepr
        cls.log = __clsLog
        return cls

    return decorator


def getTerminalOutputs(func: typing.Callable, *args, **kwargs) -> typing.Tuple[str,object]:
    '''Returns the terminal output content recorded while the function was running, and the result from the function in a tuple.
    (TerminalOutput,FunctionResult)'''
    originalStdout = sys.stdout

    with open('terminalOutputTest.temp', 'w') as f:
        sys.stdout = f
        funcResult = func(*args, **kwargs)
        sys.stdout = originalStdout

    with open('terminalOutputTest.temp', 'r') as f:
        ret = f.read()

    os.remove('terminalOutputTest.temp')
    return ret,funcResult
