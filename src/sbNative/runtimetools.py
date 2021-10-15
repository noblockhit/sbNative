import sys
import os
import inspect
import pathlib
import traceback
import typing


def getPath():
    if sys.executable.endswith("python.exe"):
        fl = inspect.stack()[1].filename
        return pathlib.Path(os.path.dirname(os.path.realpath(fl).replace("\\", "/")))
    else:
        return pathlib.Path(sys.executable.replace(sys.executable.split("\\")[-1], "").replace("\\", "/")[:-1])


def globaliseAllSubitems(destFileGlobals, packageToUnpack, forceall=False):
    for name, g in inspect.getmembers(packageToUnpack):
        if not forceall and name.startswith("_"):
            continue
        destFileGlobals[name] = g


class InterpreterError(Exception):
    pass


def execWithExcTb(cmd, globals=None, locals=None, description='source string'):
    try:
        exec(cmd, globals, locals)
    except SyntaxError as err:
        error_class = err.__class__.__name__
        detail = err.args[0]
        line_number = err.lineno
    except Exception as err:
        error_class = err.__class__.__name__
        detail = err.args[0]
        cl, exc, tb = sys.exc_info()
        line_number = traceback.extract_tb(tb)[-1][1]
    else:
        return
    raise InterpreterError("%s at line %d of %s: %s" %
                           (error_class, line_number, description, detail))



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