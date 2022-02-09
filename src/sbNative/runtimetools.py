import sys
import os
import inspect
import pathlib
import traceback
import typing
import types


def getPath() -> pathlib.Path:
    if sys.executable.endswith("python.exe"):
        fl = inspect.stack()[1].filename
        return pathlib.Path(os.path.dirname(os.path.realpath(fl).replace("\\", "/")))
    else:
        return pathlib.Path(sys.executable.replace(sys.executable.split("\\")[-1], "").replace("\\", "/")[:-1])


def globaliseAllSubitems(destFileGlobals, packageToUnpack, forceall=False) -> None:
    for name, g in inspect.getmembers(packageToUnpack):
        if not forceall and name.startswith("_"):
            continue
        destFileGlobals[name] = g


class InterpreterError(Exception):
    pass


def execWithExcTb(cmd, globals=None, locals=None, description='source string') -> None:
    try:
        exec(cmd, globals, locals)
    except SyntaxError as e:
        errorClass = e.__class__.__name__
        detail = e.args[0]
        lineNumber = e.lineno

    except Exception as e:
        errorClass = e.__class__.__name__
        detail = e.args[0]
        cl, exc, tb = sys.exc_info()

        lineNumber = traceback.extract_tb(tb)[-1][1]
    else:
        return

    raise InterpreterError(
        f"{errorClass} at line {lineNumber} of {description}: {detail}")


def get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


class DecoratorError(Exception):
    pass


def runAndCast(func) -> typing.Tuple[typing.Callable, list, dict]:
    def wrapper(*args, **kwargs):
        castTo = dict(inspect.signature(func).parameters.items())
        for k, v in typing.get_type_hints(func).items():
            castTo[k] = v

        defaultArgs = get_default_args(func)
        neededCasts = {thint: val for thint,
                       val in castTo.items() if thint not in defaultArgs.keys()}
        optionalCasts = {thint: (val, defaultArgs[thint]) for thint, val in castTo.items(
        ) if thint in defaultArgs.keys()}

        newArgs = []
        for argVal, (argName, cls) in zip(args, neededCasts.items()):
            if not isinstance(cls, inspect.Parameter):
                argVal = cls(argVal)
            newArgs.append(argVal)

        newKwargs = {}
        for argName, (cls, default) in optionalCasts.items():
            argVal = kwargs.get(argName)
            if argVal is None:
                argVal = default
            if not isinstance(cls, inspect.Parameter):
                try:
                    argVal = cls(argVal)
                except Exception as _:
                    print("----------------------------------------")
                    traceback.print_exc()
                    print("----------------------------------------")
            newKwargs[argName] = argVal
        try:
            return func(*newArgs, **newKwargs)
        except TypeError as e:
            raise DecoratorError("runAndCast MUST BE LAST DECORATOR!") from e
    return wrapper


def safeIter(itr: typing.Sequence) -> types.GeneratorType:
    '''Warning, very slow with large iterators.'''
    i = 0
    while i < len(itr):
        item = itr[i]
        yield item
        if len(itr) <= i or itr[i] is item:
            i += 1


class bidirectionalDict:
    '''One may get the original key by the values, like in {"Richard":["Rick","Dick"]}
    Using indexing or attribute getter with "Richard", "Rick" or "Dick" here will return "Richard"
    When a value is given and whilst not contained in the dict, a KeyError will be risen.'''

    def __init__(self, **kwargs):
        self.values = kwargs

    def __getattr__(self, attr_name):
        for k, v in self.values.items():
            if attr_name in [k] + v:
                return k

        raise KeyError(f"{attr_name} does not exist in {self}")

    def __getitem__(self, key):
        return self.__getattr__(key)


class LanguageFormatter:
    '''Used to format information from a program readable structure to a more easily human readable format. All of these methods are static.'''
    @staticmethod
    def __baseECollection(collection: typing.Union[typing.Iterable, typing.Sequence, typing.Generator], separator: str = ", ", lastSeparator: str = " and "):
        if len(collection) == 1:
            return collection[0]
        return separator.join(map(lambda x: str(x), collection[:-1])) + lastSeparator + str(collection[-1])

    @staticmethod
    def enumerateCollection(collection, separator: str = ", ", lastSeparator: str = " and ", recursive=False):
        '''Takes a collection like a list, tuple or anything else with a join method and converts the contents into a human readable enumeration.'''
        if not recursive or all(isinstance(c, str) for c in collection):
            return LanguageFormatter.__baseECollection(collection, separator, lastSeparator)

        return LanguageFormatter.enumerateCollection([LanguageFormatter.enumerateCollection(c) + "\n" for c in collection])

    @staticmethod
    def toAbbrNumber(number: typing.Union[int, float], maxPrecisionAmt: int = 1, abbriviations: dict={"k": 3, "m": 6, "b": 9, "t": 12}) -> str:
        '''Takes a number, which can be an int or a float and abbriviates it into a shorter form. You may pass the maximum percice digits in and change the abbriviations for different languages or extend them. Ex: German abbriviations: `k; m; mrd; b; brd; t; trd;`. Watch out and clarify to not mix these abbriviations up!'''
        decimalAmt = len(("."+str(float(number)).split(".")[1]).replace(".0","."))-1
        number = int(number * (10**decimalAmt))

        ignoredAmt = len(str(number))-maxPrecisionAmt
        abbr,abbrSize = min(abbriviations.items(), key=lambda x: abs(x[1]-ignoredAmt+decimalAmt))
        devBy = 10**(abbrSize+decimalAmt)
        roundedNum = round(number, maxPrecisionAmt-len(str(number)))
        
        preformatedStr = str(roundedNum / devBy)
        if preformatedStr.endswith(".0") and len(preformatedStr)-2 >= maxPrecisionAmt:
            preformatedStr = preformatedStr[:-2] 
        return preformatedStr+abbr

    @staticmethod
    def AbbrNumToFloat(numStr: str, abbriviations: dict={"k": 3, "m": 6, "b": 9, "t": 12}) -> float:
        '''Takes a number (that might aswell be generated from toAbbrNumber and reverts it into the number as a float. Confirm that the abbriviations are the same!'''
        abbrsInNum = [c for c in numStr if not c.isdigit()]
        abbrsInNum.remove(".")
        number = float(numStr.replace("".join(abbrsInNum), ""))
        for abbr in abbrsInNum:
            number *= (10**abbriviations[abbr])
        return number

    @staticmethod
    def toAbbrWord(word, hard=True, rmStrings="aeiouyäöü"):
        '''When using hard, all the non important characters/strings (usually vowels) will be removed, regardless of repetition or position'''
        if hard:
            return word.translate({ord(c): None for c in rmStrings})
        if len(word) <= 4:
            return word
        
        ret = ""
        for i in range(len(word)):
            end = i+1 == len(word)
            if not end:
                rmNext = word[i+1] in rmStrings
            else:
                rmNext = False
            if word[i] in rmStrings and not rmNext and i > 0:
                continue
            
            ret += word[i]
            if rmNext and word[i] in rmStrings:
                ret += word[i+1]
                
        return ret

    @staticmethod
    def toAbbrSentence(sentence, hard=True, rmStrings="aeiouyäöü"):
        return " ".join([LanguageFormatter.toAbbrWord(word, hard, rmStrings) for word in sentence.split(" ")])

if __name__ == "__main__":
    # tests = {17_234_000_000, 17_234_000_000.5235, 1_234_567_000, 1_234_567_000.5678, 234_567_000, 234_567_000.52348}
    # for i in tests:
    #     for p in range(1, 7):
    #         print(LanguageFormatter.toAbbrNumber(i, p), end = " | ")
    #     print("---")
    print(LanguageFormatter.toAbbrSentence("Please only use this carefully, it might screw up some text and make it way too hard to read, if you are not too sure whether this is suitable, definetly disable the \"h a r d\" keyword.", hard=False))
