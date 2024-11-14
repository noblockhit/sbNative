import inspect
import os
import shutil
import sys
import time
import atexit
import typing
import itertools
from enum import Enum
from runtimetools import get_path
import webbrowser


INDENT_LVL: int = 4

terminal_stacking = False


line_split_sign = "\uF8FF"

prev_log_info = {
    "info_name": None,
    "traceback_depth": None,
    "end": None,
    "args": [],
    "kwargs": {},
    "fileName": None,
    "lineNumber": None
}

prev_log = ["", 1]


def switch_terminal_stacking() -> bool:
    """
    Terminal-stacking is a feature that prevents the logging function from spamming the terminal with useless
    information.
    If the same things are logged in the same line, file, back to back and this feature is enabled, the information will
    not be printed again,
    it will rather "edit" the existing line and add `[2x]` `[3x]` `[4x]` ... `[nx]` after the location of the log.
    """
    global terminal_stacking
    terminal_stacking = not terminal_stacking
    if not terminal_stacking:
        print(f"{prev_log[0]} [{prev_log[1]}x]")

    def print_newline_on_terminal_stack():
        global terminal_stacking
        if terminal_stacking:
            print()

    atexit.register(print_newline_on_terminal_stack)
    return terminal_stacking


def format_dict_to_equal_signs(d):
    ret = []
    for k, v in d.items():
        if isinstance(v, dict):
            ret.append(f"{k} = {tuple(format_dict_to_equal_signs(v))}")
        else:
            ret.append(f"{k} = {v}")
    return ret


def compute_line_break_indents(args: tuple, kwargs: dict,
                               indent_start_end=None, is_overflow=False) -> str:
    if indent_start_end is None:
        indent_start_end = ["()", "[]", "{}"]

    args = tuple(map(str, tuple(args) + tuple(format_dict_to_equal_signs(kwargs))))

    if not is_overflow:
        return "(" + f", ".join(args) + f")"

    content_str = f"({line_split_sign}" + \
        f", {line_split_sign}".join(args) + f"{line_split_sign})"
    content_str = content_str.replace(line_split_sign, "\n")

    openers = [i[0] for i in indent_start_end]
    endings = [i[1] for i in indent_start_end]

    curr_indent = 0
    indent_stack = ""
    new_content_str = ""

    for idx, c in enumerate(content_str):
        if c in openers and len(content_str) > idx+1 and content_str[idx+1] in [line_split_sign, "\n"]:
            curr_indent += 1
            indent_stack += c

        elif (c in endings and len(indent_stack) > 0 and idx > 2 and (content_str[idx-1] in [line_split_sign, "\n"]) and
              openers[endings.index(c)] == indent_stack[-1]):
            curr_indent -= 1
            indent_stack = indent_stack[:-1]
            new_content_str = new_content_str[:-INDENT_LVL]

        new_content_str += c
        if c in [line_split_sign, "\n"]:
            new_content_str += " " * (curr_indent * INDENT_LVL)

    return new_content_str


def __base_logging_func(
        info_name: object,
        traceback_depth: int,
        max_occupied_width_portion: float,
        end: str,
        *args: object,
        **kwargs) -> None:
    """
    This is the base of the logging function,
    like `log` and `ilog` (info-log). It is almost redundant to use this,
    because the `log` and `ilog` functions will likely satisfy your needs.
    """
    global terminal_stacking

    call = inspect.getframeinfo(inspect.stack()[traceback_depth][0])
    file_name, line_number = call.filename, call.lineno

    if terminal_stacking:
        global prev_log_info
        global prev_log

        curr_log_info = {
            "info_name": info_name,
            "traceback_depth": traceback_depth,
            "end": end,
            "args": args,
            "kwargs": kwargs,
            "file_name": file_name,
            "line_number": line_number
        }

        if curr_log_info == prev_log_info:
            prev_log[1] += 1
            print(f"{prev_log[0]} [{prev_log[1]}x]", end="\r")
            return

        if len(prev_log[0]):
            print(f"{prev_log[0]}")

        prev_log_info = curr_log_info

    path = file_name.replace("\\", "/") + ":" + str(line_number)
    arrow = " --> "

    if info_name:
        log_string = f"LOG ({repr(info_name)}): "
    else:
        log_string = f"LOG: "
    arg_str = compute_line_break_indents(args, kwargs)
    console_width = shutil.get_terminal_size()[0]
    occupied_log_length = len(arg_str)

    if occupied_log_length+len(path)+len(arrow)+len(log_string)+len(end) > console_width*max_occupied_width_portion:
        log_string += "\n"
        arrow = "\n" + arrow[1:]
        arg_str = compute_line_break_indents(args, kwargs, is_overflow=True)

    log_string += f"{arg_str}{end}{arrow}{path}"

    if terminal_stacking:
        print(log_string.split("\n")[-1], end="\r")
        prev_log = [log_string, 1]
    else:
        print(log_string)


def log(*args: object, depth: int = 2, **kwargs) -> None:
    """
    Prints all the arguments given to the console and the file + line of the call.
    Supports more advanced logging when paired with the `cleanRepr` class decorator.
    """
    __base_logging_func(None, depth, .9, "", *args, **kwargs)


def ilog(info: object, *args: object, depth: int = 2, end: str = "", **kwargs) -> None:
    """
    Prints all the arguments given to the console and the file + line of the call.
    First argument will be used to represent what is logged. Supports more advanced logging when paired with the
    `cleanRepr` class decorator.
    """
    __base_logging_func(info, depth, .9, end, *args, **kwargs)


class ClsWithCleanRepr:
    __excludeReprVarNames__ = None


def __cls_repr(cls: ClsWithCleanRepr) -> str:
    """
    This is what the `__repr__` method of the class decorated with `cleanRepr` decorator is replaced with.
    Supports newlines with the logging functions.
    """
    is_log_call = is_from_call("log")
    ret = f"{type(cls).__name__}({line_split_sign}"

    sub_objects = {**cls.__dict__, **{name: classAttr for name, classAttr in type(
        cls).__dict__.items() if not callable(classAttr) and not name.startswith("__")}}

    for k, v in sub_objects.items():
        if k in cls.__excludeReprVarNames__:
            continue

        ret += f"{repr(k)} = {repr(v)}, "
        if is_log_call:
            ret += line_split_sign

    if len(sub_objects) == 0:
        return ret + ")"

    ret = ret.strip(line_split_sign)

    remv_last_chars = -1

    if len(sub_objects) > 1:
        remv_last_chars -= 1

    if remv_last_chars == 0:
        return ret + ")"
    return ret[:remv_last_chars] + f"{line_split_sign})"


def __cls_log(self, *args) -> object:
    if len(args) == 0:
        return log(self, depth=3)
    return ilog(self, *args, depth=3)


def is_from_call(func_name: str) -> bool:
    """
    Gets if a function with the name `func_name` is in the callstack.
    Used by `__clsRepr` to determine if it should add markers in the form of `lignSplitSign` where newlines can be added
     if the logging string is too long.
    """
    funcs = [c.function for c in inspect.stack()]
    return func_name in funcs


def clean_repr(*exclude: typing.Iterable[str]):
    """
    A decorator which makes the representation of your class as clean as possible.
    If you don't want specific class or instance variables to be included, you may specify them as arguments for this
    function.
    """
    def decorator(cls):
        cls.__excludeReprVarNames__ = exclude
        cls.__repr__ = __cls_repr
        cls.log = __cls_log
        return cls

    return decorator


def get_terminal_outputs(func: typing.Callable, *args, **kwargs) -> typing.Tuple[str, object]:
    """Returns the terminal output content recorded while the function was running, and the result from the function in
    a tuple.
    (TerminalOutput,FunctionResult)"""
    original_stdout = sys.stdout

    with open('terminalOutputTest.temp', 'w') as f:
        sys.stdout = f
        func_result = func(*args, **kwargs)
        sys.stdout = original_stdout

    with open('terminalOutputTest.temp', 'r') as f:
        ret = f.read()

    os.remove('terminalOutputTest.temp')
    return ret, func_result


def plot_tuples(plt, tpls, title="", x_axis_name="", y_axis_name="") -> None:
    vals_old = list(zip(*tpls))

    vals = [tuple([str(i) if type(i) not in [str, int, float]
                  else i for i in row]) for row in vals_old]

    if vals != vals_old:
        print("WARNING: CASTED ITEMS IN THE TUPLE TO BE COMPREHENSIBLE TO MATPLOTLIB")
        print(vals_old)
        print("-->")
        print(vals)

    if any(type(v) not in [str, int, float] for v in itertools.chain(*vals)):
        raise TypeError(
            "Attributes in x or y which are not strings, integers or floats!")

    plt.plot(*vals)
    plt.title(title)
    plt.xlabel(x_axis_name)
    plt.ylabel(y_axis_name)


def timer(func: callable) -> typing.Callable:
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


class TPlotArgs(Enum):
    TIME = 1
    ARGS = 2


class TimePlotter:
    def __init__(self, sort_after: typing.Union[TPlotArgs, TPlotArgs], track_args: typing.Sequence[int] = None,
                 track_kwargs: typing.Sequence[str] = None, reverse=False):
        if track_args is None:
            track_args = []
        if track_kwargs is None:
            track_kwargs = []
        self.callArgsAndTimes = []
        self.sortAfter = sort_after
        self.reverse = reverse
        self.func = None
        self.trackArgs = track_args
        self.trackKwargs = track_kwargs

    def timer(self, func: callable):
        """
        A simple decorator for timing the execution time of a function or method. Uses matplotlib to show the time with
        arguments for the called function.
        """
        if self.func is None:
            self.func = func

        else:
            raise RuntimeError("You may not decorate multiple functions with the same timing instance.")

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
            args_and_kwargs = ""

            args_to_plot = tuple(a for idx, a in enumerate(
                i['args']) if idx in self.trackArgs)
            if str(args_to_plot) != "()":
                args_and_kwargs += str(args_to_plot)

            kwargs_to_plot = {name: kwa for name,
                              kwa in i['kwargs'].items() if name in self.trackKwargs}
            if str(kwargs_to_plot) != "{}":
                args_and_kwargs += str(kwargs_to_plot)

            if self.sortAfter is TPlotArgs.ARGS:
                tuples.append((args_and_kwargs, i["deltaT"]))

            elif self.sortAfter is TPlotArgs.TIME:
                tuples.append((i["deltaT"], args_and_kwargs))

            else:
                raise TypeError(
                    f"{self.sortAfter} is not an attribute of the debugtools.tPlotArgs class!")

        with open(get_path().joinpath("templates").joinpath("graphTemplate.html"), "r") as rf:
            html_template = rf.read()
            html_template = self.inject(html_template, tuples)
        self.display_graph(html_template)

    @staticmethod
    def inject(html_template, values):
        begin_idx = html_template.find("{BEGIN-TBL-ELM}")
        tbl_elm = html_template[begin_idx +
                                len("{BEGIN-TBL-ELM}"):html_template.find("{END-TBL-ELM}")]

        elements = []
        for x, y in values:
            elements.append(
                tbl_elm.replace("{XVALUE}", str(x)).replace("{YVALUE}", str(y))
            )

        html_template = html_template.replace(tbl_elm, "\n".join(elements))

        return html_template.replace("{BEGIN-TBL-ELM}", "").replace("{END-TBL-ELM}", "")

    @staticmethod
    def display_graph(html_content):
        with open(f"{str(get_path())}/temp/graphdisplay.html", 'w') as f:
            f.write(html_content)

            filename = f"file:///{str(get_path())}/temp/graphdisplay.html"
            webbrowser.get().open(filename)


if __name__ == '__main__':

    @clean_repr()
    class SecondExCls:
        withAnAttribute = "that is a string of second ex cls"

    @clean_repr()
    class ExampleClass:
        withSomeAttr = "something something"
        another1 = "something something something something something something"
        andALastOne = "something something something something something something something something"
        secondExample = SecondExCls()

    log(ExampleClass())
    log("some_str", 123, 876543, 2134566.987654, 12345, 765433, 435678, 9876543,
        3435465, 987658765, 87654329876543, 8765432897654, 1234567890, andSomeKwarg=1234)
    log("some_str", 123, 876543, andSomeKwarg=1234)
