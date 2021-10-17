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


def castToTypeHint(func, *args, **kwargs) -> typing.Tuple[typing.Callable, list, dict]:
    castTo = typing.get_type_hints(func)
    atIdx = 0
    retArgs = []
    for arg in args:
        retArgs.append(list(castTo.values())[atIdx](arg))
        atIdx += 1
    
    retKwargs = {}
    for kwname,kwarg in kwargs.items():
        retKwargs[kwname] = list(castTo.values())[atIdx](kwarg)
        atIdx += 1

    return retArgs,retKwargs


def safeIter(itr: typing.Sequence) -> types.GeneratorType:
    '''Warning, very slow with large iterators.'''
    i = 0
    while i < len(itr):
        item = itr[i]
        yield item
        if len(itr) <= i or itr[i] is item:
            i += 1
