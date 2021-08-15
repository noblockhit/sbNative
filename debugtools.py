import inspect
import os
import time
import atexit
import typing

terminalStacking = False

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


def switch_terminal_stacking():
    """
    TerminalStacking is a feature that prevents the logging function from spamming the terminal with useless
    information. If the same things are logged in the same line, file, back to back and this feature is enabled,
    the information will not be printed again, it will rather "edit" the existing line and add `[2x]` `[3x]` `[4x]`
    ... `[nx]` after the location of the log.
    """
    global terminalStacking
    terminalStacking = not terminalStacking
    if not terminalStacking:
        print(f"{prevLog[0]} [{prevLog[1]}x]")

    def print_newline_on_terminal_stack():
        # global terminalStacking
        if terminalStacking:
            print()

    atexit.register(print_newline_on_terminal_stack)
    return terminalStacking


def compute_linebreak_indents(args,
                              indent_start_end: typing.Union[str, typing.Sequence[typing.Tuple[str, str]]] = None):
    """
    Used for clean representation of e.g. Lists (indentStartEnd = "[]") if multiple lines are necessary. If
    `indentStartEnd` is `None` all the arguments will be combined to a list of newlines. IndentStartEnd must be a 2
    item sequence of single characters. Multi Character support might be supported in the future.
    """
    ret = []

    curr_indent_lvl = 0

    if indent_start_end:
        srt, end = indent_start_end
        for a in args:
            lns_not_split = str(a).replace(
                srt, srt + "\\p").replace(end, "\\p" + end).replace(end + ", ", end + ",\\p")
            lines = lns_not_split.split("\\p")
            for line in lines:
                curr_indent_lvl -= line.count(end) * 4
                ret.append(" " * curr_indent_lvl + line)
                curr_indent_lvl += line.count(srt) * 4

    else:
        for a in args:
            ret += [str(a)]
    return ret


def __base_logging_func(
        info_name: typing.Union[str, None],
        traceback_depth: int,
        separator: str,
        max_occupiable_width_portion: float,
        end: str,
        *args: object):
    """
    This is the base of the logging function,
    like `log` and `ilog` (infoLog). It is almost redundant to use this,
    because the `log` and `ilog` functions will likely satisfy your needs.
    """
    global terminalStacking

    call = inspect.getframeinfo(inspect.stack()[traceback_depth][0])
    file_name, line_number = call.filename, call.lineno

    if terminalStacking:
        global prevLogInfo
        global prevLog

        curr_log_info = {
            "infoName": info_name,
            "tracebackDepth": traceback_depth,
            "separator": separator,
            "end": end,
            "args": args,
            "file_Name": file_name,
            "lineNumber": line_number
        }

        if curr_log_info == prevLogInfo:
            prevLog[1] += 1
            print(f"{prevLog[0]} [{prevLog[1]}x]", end="\r")
            return

        if len(prevLog[0]):
            print(f"{prevLog[0]}")

        prevLogInfo = curr_log_info

    path = file_name.replace("\\", "/") + ":" + str(line_number)
    arrow = " --> "

    if info_name:
        log_string = f"LOG ({repr(info_name)}): "
    else:
        log_string = f"LOG: "

    arg_strings = compute_linebreak_indents(args)
    console_width = os.get_terminal_size()[0]
    occupied_log_length = sum([len(s) + len(separator)
                               for s in arg_strings]) - len(separator)

    if occupied_log_length + len(path) + len(arrow) + len(log_string) + len(
            end) > console_width * max_occupiable_width_portion:
        separator = "\n"
        log_string += "\n"
        arrow = "\n" + arrow[1:]
        arg_strings = compute_linebreak_indents(args, "()")
        arg_strings = compute_linebreak_indents(arg_strings, "[]")
        arg_strings = compute_linebreak_indents(arg_strings, "{}")

    arg_str = separator.join(arg_strings).replace("\\p", "")

    log_string += f"{arg_str}{end}{arrow}{path}"

    if terminalStacking:
        print(log_string.split("\n")[-1], end="\r")
        prevLog = [log_string, 1]
    else:
        print(log_string)


def log(*args: object, depth: int = 2):
    """
    Prints all the arguments given to the console and the file + line of the call.
    Supports more advanced logging when paired with the `cleanRepr` class decorator.
    """
    __base_logging_func(None, depth, " | ", .9, "", *args)


def ilog(info, *args: object, depth: int = 2, end: str = ""):
    """
    Prints all the arguments given to the console and the file + line of the call. First argument will be used to
    represent what is logged. Supports more advanced logging when paired with the `cleanRepr` class decorator.
    """
    __base_logging_func(info, depth, " | ", .9, end, *args)


def timer(func: callable):
    """
    A simple decorator for timing the execution time of a function or method. Flexes the `ilog` function.
    """

    def wrapper(*args, **kwargs):
        begin = time.time()
        ret = func(*args, **kwargs)
        ilog(f"Executing `{func.__name__}` took",
             time.time() - begin, depth=3, end=" seconds")
        return ret

    return wrapper


def __cls_repr(cls):
    """
    This is what the `__repr__` method of the class decorated with `cleanRepr` decorator is replaced with.
    Supports newlines with the logging functions.
    """
    is_log_call = is_from_call("log")
    ret = f"{type(cls).__name__}("

    sub_objects = {**cls.__dict__, **{name: classAttr for name, classAttr in type(
        cls).__dict__.items() if not callable(classAttr) and not name.startswith("__")}}

    for k, v in sub_objects.items():
        if k in cls.__excludeReprVarNames__:
            continue

        ret += f"{repr(k)}: {repr(v)}, "
        if is_log_call:
            ret += "\\p"

    if len(sub_objects) == 0:
        return ret + ")"

    ret = ret.strip("\\p")

    remove_last_chars = -1

    if len(sub_objects) > 1:
        remove_last_chars -= 1

    if remove_last_chars == 0:
        return ret + ")"
    return ret[:remove_last_chars] + ")"


def is_from_call(func_name: str):
    """
    Gets if a function with the name `funcName` is in the callstack. Used by `__clsRepr` to determine if it should
    add markers in the form of `\\p` where newlines can be added if the logging string is too long.
    """
    funcs = [c.function for c in inspect.stack()]
    return func_name in funcs


def clean_repr(*exclude: typing.Iterable[str]):
    """
    A decorator which makes the representation of your class as clean as possible. If you don't want specific
    class or instance variables to be included, you may specify them as arguments for this function.
    """

    def decorator(cls):
        cls.__excludeReprVarNames__ = exclude
        cls.__repr__ = __cls_repr
        return cls

    return decorator
