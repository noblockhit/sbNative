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

    raise InterpreterError(f"{errorClass} at line {lineNumber} of {description}: {detail}")


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
        for k,v in typing.get_type_hints(func).items():
            castTo[k] = v

        defaultArgs = get_default_args(func)
        neededCasts = {thint:val for thint,val in castTo.items() if thint not in defaultArgs.keys()}
        optionalCasts = {thint:(val, defaultArgs[thint]) for thint,val in castTo.items() if thint in defaultArgs.keys()}
        
        newArgs = []
        for argVal,(argName, cls) in zip(args,neededCasts.items()):
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
                except Exception as e:
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


class LanguageFormatter:
    def enumerateCollection(collection, separator=", ", lastSeparator=" and "):
        if len(collection) == 1:
            return collection[0]
        return separator.join(collection[:-1]) + lastSeparator + collection[-1]