import inspect
import os
import sys
import time
import atexit
import typing
import itertools
from enum import Enum
from runtimetools import getPath
import webbrowser


global terminalStacking
terminalStacking = False

global prevLogInfo
global prevLog
global lineSplitSign

lineSplitSign = "\uF8FF"

prevLogInfo = {
    "infoName": None,
    "tracebackDepth": None,
    "end": None,
    "args": [],
    "kwargs": {},
    "fileName": None,
    "lineNumber": None
}

prevLog = ["", 1]


def switchTerminalStacking() -> bool:
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


def formatDictToEqualSigns(d):
    ret = []
    for k, v in d.items():
        if isinstance(v, dict):
            ret.append(f"{k} = {tuple(formatDictToEqualSigns(v))}")
        else:
            ret.append(f"{k} = {v}")
    return ret


def computeLineBreakIndents(args: tuple, kwargs: dict, indentStartEnd=["()", "[]", "{}"], isOverflow=False) -> list:

    args = tuple(map(str, tuple(args) + tuple(formatDictToEqualSigns(kwargs))))

    if not isOverflow:
        return "(" + f", ".join(args) + f")"

    contentStr = f"({lineSplitSign}" + \
        f", {lineSplitSign}".join(args) + f"{lineSplitSign})"
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


def __baseLoggingFunc(
        infoName: typing.Union[str, None],
        tracebackDepth: int,
        maxOccupyableWidthPortion: float,
        end: str,
        *args: object,
        **kwargs) -> None:
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
            "end": end,
            "args": args,
            "kwargs": kwargs,
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
    argStr = computeLineBreakIndents(args, kwargs)
    consoleWidth = os.get_terminal_size()[0]
    occupiedLogLength = len(argStr)

    if occupiedLogLength+len(path)+len(arrow)+len(logString)+len(end) > consoleWidth*maxOccupyableWidthPortion:
        logString += "\n"
        arrow = "\n" + arrow[1:]
        argStr = computeLineBreakIndents(args, kwargs, isOverflow=True)

    logString += f"{argStr}{end}{arrow}{path}"

    if terminalStacking:
        print(logString.split("\n")[-1], end="\r")
        prevLog = [logString, 1]
    else:
        print(logString)


def log(*args: object, depth: int = 2, **kwargs) -> None:
    '''
    Prints all the arguments given to the console and the file + line of the call.
    Supports more advanced logging when paired with the `cleanRepr` class decorator.
    '''
    __baseLoggingFunc(None, depth, .9, "", *args, **kwargs)


def ilog(info: object, *args: object, depth: int = 2, end: str = "", **kwargs) -> None:
    '''
    Prints all the arguments given to the console and the file + line of the call.
    First argument will be used to represent what is logged. Supports more advanced logging when paired with the `cleanRepr` class decorator.
    '''
    __baseLoggingFunc(info, depth, .9, end, *args, **kwargs)


def __clsRepr(cls: type) -> type:
    '''
    This is what the `__repr__` method of the class decorated with `cleanRepr` decorator is replaced with.
    Supports newlines with the logging functions.
    '''
    isLogCall = isFromCall("log")
    ret = f"{type(cls).__name__}({lineSplitSign}"

    subObjects = {**cls.__dict__, **{name: classAttr for name, classAttr in type(
        cls).__dict__.items() if not callable(classAttr) and not name.startswith("__")}}

    for k, v in subObjects.items():
        if k in cls.__excludeReprVarNames__:
            continue

        ret += f"{repr(k)} = {repr(v)}, "
        if isLogCall:
            ret += lineSplitSign

    if len(subObjects) == 0:
        return ret + ")"

    ret = ret.strip(lineSplitSign)

    remvLastChars = -1

    if len(subObjects) > 1:
        remvLastChars -= 1

    if remvLastChars == 0:
        return ret + ")"
    return ret[:remvLastChars] + f"{lineSplitSign})"


def __clsLog(self, *args) -> object:
    if len(args) == 0:
        return log(self, depth=3)
    return ilog(self, *args, depth=3)


def isFromCall(funcName: str) -> bool:
    '''
    Gets if a function with the name `funcName` is in the callstack.
    Used by `__clsRepr` to determine if it should add markers in the form of `lignSplitSign` where newlines can be added if the logging string is too long.
    '''
    funcs = [c.function for c in inspect.stack()]
    return funcName in funcs


def cleanRepr(*exclude: typing.Iterable[str]) -> type:
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


def getTerminalOutputs(func: typing.Callable, *args, **kwargs) -> typing.Tuple[str, object]:
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
    return ret, funcResult


def plotTuples(plt, tups, title="", xaxisName="", yaxisName="") -> None:
    valsOld = list(zip(*tups))

    vals = [tuple([str(i) if type(i) not in [str, int, float]
                  else i for i in row]) for row in valsOld]

    if vals != valsOld:
        print("WARNING: CASTED ITEMS IN THE TUPLE TO BE COMPREHENSABLE TO MATPLOTLIB")
        print(valsOld)
        print("-->")
        print(vals)

    if any(type(v) not in [str, int, float] for v in itertools.chain(*vals)):
        raise TypeError(
            "Attributes in x or y which are not strings, integers or floats!")

    plt.plot(*vals)
    plt.title(title)
    plt.xlabel(xaxisName)
    plt.ylabel(yaxisName)


def timer(func: callable) -> typing.Callable:
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


class tPlotArgs(Enum):
    TIME = 1
    ARGS = 2


class timePlotter:
    def __init__(self, sortAfter: typing.Union[tPlotArgs, tPlotArgs], trackArgs: typing.Sequence[int] = [], trackKwargs: typing.Sequence[str] = [], reverse=False):
        self.callArgsAndTimes = []
        self.sortAfter = sortAfter
        self.reverse = reverse
        self.func = None
        self.trackArgs = trackArgs
        self.trackKwargs = trackKwargs

    def timer(self, func: callable):
        '''
        A simple decorator for timing the execution time of a function or method. Uses matplotlib to show the time with arguments for the called function.
        '''
        if self.func is None:
            self.func = func

        else:
            raise RuntimeError(
                "You may not decorate multiple functions with the same timing instance.")

        def wrapper(*args, **kwargs):
            begin = time.time()
            ret = func(*args, **kwargs)

            self.callArgsAndTimes.append(
                {"deltaT": 1000 * (time.time() - begin),
                 "args": args, "kwargs": kwargs}
            )
            return ret

        return wrapper

    def show(self):
        if self.func is None:
            raise RuntimeError(
                f"A function was never called with this timePlotting instance.")

        tuples = []

        for i in self.callArgsAndTimes:
            argsAndKwargs = ""

            argsToPlot = tuple(a for idx, a in enumerate(
                i['args']) if idx in self.trackArgs)
            if str(argsToPlot) != "()":
                argsAndKwargs += str(argsToPlot)

            kwargsToPlot = {name: kwa for name,
                            kwa in i['kwargs'].items() if name in self.trackKwargs}
            if str(kwargsToPlot) != "{}":
                argsAndKwargs += str(kwargsToPlot)

            if self.sortAfter is tPlotArgs.ARGS:
                tuples.append((argsAndKwargs, i["deltaT"]))

            elif self.sortAfter is tPlotArgs.TIME:
                tuples.append((i["deltaT"], argsAndKwargs))

            else:
                raise TypeError(
                    f"{self.sortAfter} is not an attribute of the debugtools.tPlotArgs class!")

        with open(getPath().joinpath("templates").joinpath("graphTemplate.html"), "r") as rf:
            htmlTemplate = rf.read()
            htmlTemplate = self.inject(htmlTemplate, tuples)
        self.displayGraph(htmlTemplate)

    def inject(self, htmlTemplate, values):
        beginIdx = htmlTemplate.find("{BEGIN-TBL-ELM}")
        tblElm = htmlTemplate[beginIdx +
                              len("{BEGIN-TBL-ELM}"):htmlTemplate.find("{END-TBL-ELM}")]

        elements = []
        for x, y in values:
            elements.append(
                tblElm.replace("{XVALUE}", str(x)).replace("{YVALUE}", str(y))
            )

        htmlTemplate = htmlTemplate.replace(tblElm, "\n".join(elements))

        return htmlTemplate.replace("{BEGIN-TBL-ELM}", "").replace("{END-TBL-ELM}", "")

    def displayGraph(self, htmlContent):
        with open(f"{str(getPath())}/temp/graphdisplay.html", 'w') as f:
            f.write(htmlContent)

            filename = f"file:///{str(getPath())}/temp/graphdisplay.html"
            webbrowser.get().open(filename)


if __name__ == '__main__':

    @cleanRepr()
    class SecondExCls:
        withAnAttribute = "that is a string of second ex cls"

    @cleanRepr()
    class ExampleClass:
        withSomeAttr = "something something"
        another1 = "something something something something something something"
        andALastOne = "something something something something something something something something"
        secondExample = SecondExCls()

    log(ExampleClass())
    log("somestr", 123, 876543, 2134566.987654, 12345, 765433, 435678, 9876543,
        3435465, 987658765, 87654329876543, 8765432897654, 1234567890, andSomeKwarg=1234)
    log("somestr", 123, 876543, andSomeKwarg=1234)
