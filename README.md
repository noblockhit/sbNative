# SbNative
An extention to python for debugging and such. Things that, well `Should Be Native`


## SbNative may be used for
  - private projects.
  - public projects (The SbNative repo must be referenced in a Readme in case the source code is available.)

DO NOT DISTRIBUTE.

ALL NON MENTIONED RIGHTS RESERVED.


## Chapter 1: debugging
All of the neccessary dependencies are located or imported in the `debugtools.py` file.

  - `switchTerminalStacking`. Terminal stacking is a method for compressing logged information into a single line if possible.
    Ex: 
    ```python
    from sbNative.debugtools import log


    for _ in range(10):
        log("this module should be native!")
    ```
    leads to this result when not using terminal stacking:
    ```
    LOG: this module should be native! --> c:FILEPATH.py:5
    LOG: this module should be native! --> c:FILEPATH.py:5
    LOG: this module should be native! --> c:FILEPATH.py:5
    LOG: this module should be native! --> c:FILEPATH.py:5
    LOG: this module should be native! --> c:FILEPATH.py:5
    LOG: this module should be native! --> c:FILEPATH.py:5
    LOG: this module should be native! --> c:FILEPATH.py:5
    LOG: this module should be native! --> c:FILEPATH.py:5
    LOG: this module should be native! --> c:FILEPATH.py:5
    LOG: this module should be native! --> c:FILEPATH.py:5
    ```

    which obviously is not very clean...
    Instead, doing this:
    ```python
    from sbNative.debugtools import log,switchTerminalStacking


    switchTerminalStacking()

    for _ in range(10):
        log("this module should be native!")
    ```

    leads to an arguably cleaner output:
    ```
    LOG: this module should be native! --> c:FILEPATH.py:7 [10x]
    ```

  - `log`. Prints all the arguments given to
    the console and the file + line of the call.
    Supports more advanced logging when paired with the `cleanRepr` class decorator.
    As shown above, it also claryfies that a value has been logged. The reason for the file and line are to find it and edit/remove the logging call quickly. In many editors, (also VSCODE) you may CTRL+LEFTCLICK the line and it will redirect you to the file and corresponding line of the log call.
    Ex: 
    ```
    LOG: this module should be native! --> c:/---/Desktop/test1.py:6
    ```
    The depth parameter controls how far the lookup into the callstack watches for the filename and number after the `-->`. This is a feature for functions written by you, to redirect the user or yourself to the line your function was called at. Incrementing goes further into the callstack. Default: 2.
  
  - `ilog`. "Info Log". Behaves largely like `log`
    First argument will be used to represent what is being logged.

  - `isFromCall`. Gets if a function with the name `funcName` is in the callstack.
    Used by `__clsRepr` to determine if it should add markers in the form of `lignSplitSign` where newlines can be added if the logging string is too long.

  - `cleanRepr`. A decorator which makes the representation of your class as clean as possible. If you don't want specific class or instance variables to be included, you may specify thier name as arguments for this function.

  - `getTerminalOutputs`. Returns the terminal output content recorded while the function was running, and the result from the function in a tuple.
    (TerminalOutput,FunctionResult)
    <span style="color:red">***WARNING: THIS FUNCTION ALLOCATES THE RESULT TO YOUR DRIVE AND NOT MEMORY. PRINTING MAY BE VERY SLOW, DO NOT EVER USE IN PRODUCTION WITH HIGH WORKLOADS.***</span>

  - `timer`. A simple decorator for timing the
    execution time of a function or method.
    Brags about the `ilog` function. (:
  
  - `tPlotArgs` Enums or "Flags" to sort after the execution times of the functions or the arguments passed to the function.

  - `timePlotter` Works the same way as the `timer` decorator, tho it returns an object and the decorator is the function `timePlotter.time`.
  The major difference is the ability to plot the times on a matplotlib graph. You can sort the time or arguments with the Enums from `tPlotArgs`.
  The reverse kwarg may only reverse the x axis.
  The arguments or keyarguments that are supposed to be displayed on the plot have to be passed into the `trackArgs`/`trackKwargs` parameters. For args, these have to be the indicies of the argument, for kwargs the name of the keyword-argument.
  Decorate the function to be tracked with the `timer` method, and plot them with the `show` one.
  You may not use the same instance on multiple functions, otherwise, an error will be raised.

## Chapter 2: runtime utilities
All of the neccessary dependencies are located or imported in the `runtimetools.py` file.

  - `getPath` Retrieves the path of the file it has been called in. Returns a `Path` object from the built-in `pathlib` module.

  - `globaliseAllSubitems` Adds all the subitems of a module or folder containing a `__init__.py` file to the global scope, do not ever use this function if you are not desperate, the IDE wont recognise its behaviour.

  - `execWithExcTb` Extends the built-in `exec` function, tho shows the exceptions when one is raised, with the appropriate format.

  - `castToTypeHint` <span style="color:red">***NOT IMPLEMENTED COMPLETELY YET.***</span>

  - `safeIter` Allows iteration and removal of items inside the iterable simultaneously.