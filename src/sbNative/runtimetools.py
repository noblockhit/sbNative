import sys
import os
import inspect
import pathlib
import traceback
import typing
import types


def get_path() -> pathlib.Path:
    if sys.executable.endswith("python.exe"):
        fl = inspect.stack()[1].filename
        return pathlib.Path(os.path.dirname(os.path.realpath(fl).replace("\\", "/")))
    else:
        return pathlib.Path(sys.executable.replace(sys.executable.split("\\")[-1], "").replace("\\", "/")[:-1])


def globalise_all_sub_items(dest_file_globals, package_to_unpack, force_all=False) -> None:
    for name, g in inspect.getmembers(package_to_unpack):
        if not force_all and name.startswith("_"):
            continue
        dest_file_globals[name] = g


class InterpreterError(Exception):
    pass


def exec_with_exc_tb(cmd, globs=None, locs=None, description='source string') -> None:
    try:
        exec(cmd, globs, locs)
    except SyntaxError as e:
        error_class = e.__class__.__name__
        detail = e.args[0]
        line_number = e.lineno

    except Exception as e:
        error_class = e.__class__.__name__
        detail = e.args[0]
        cl, exc, tb = sys.exc_info()

        line_number = traceback.extract_tb(tb)[-1][1]
    else:
        return

    raise InterpreterError(
        f"{error_class} at line {line_number} of {description}: {detail}")


def get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


class DecoratorError(Exception):
    pass


def run_and_cast(func) -> typing.Callable:
    def wrapper(*args, **kwargs):
        cast_to = dict(inspect.signature(func).parameters.items())
        for k, v in typing.get_type_hints(func).items():
            cast_to[k] = v

        default_args = get_default_args(func)
        needed_casts = {type_hint: val for type_hint,
                        val in cast_to.items() if type_hint not in default_args.keys()}
        optional_casts = {type_hint: (val, default_args[type_hint]) for type_hint, val in cast_to.items(
        ) if type_hint in default_args.keys()}

        new_args = []
        for arg_val, (argName, cls) in zip(args, needed_casts.items()):
            if not isinstance(cls, inspect.Parameter):
                arg_val = cls(arg_val)
            new_args.append(arg_val)

        new_kwargs = {}
        for argName, (cls, default) in optional_casts.items():
            arg_val = kwargs.get(argName)
            if arg_val is None:
                arg_val = default
            if not isinstance(cls, inspect.Parameter):
                try:
                    arg_val = cls(arg_val)
                except Exception as _:
                    print("----------------------------------------")
                    traceback.print_exc()
                    print("----------------------------------------")
            new_kwargs[argName] = arg_val
        try:
            return func(*new_args, **new_kwargs)
        except TypeError as e:
            raise DecoratorError("runAndCast MUST BE LAST DECORATOR!") from e

    return wrapper


def safe_iter(itr: typing.Sequence) -> types.GeneratorType:
    """Warning, very slow with large iterators."""
    i = 0
    while i < len(itr):
        item = itr[i]
        yield item
        if len(itr) <= i or itr[i] is item:
            i += 1


class BiDirectionalDict:
    """One may get the original key by the values, like in {"Richard":["Rick","Dick"]}
    Using indexing or attribute getter with "Richard", "Rick" or "Dick" here will return "Richard"
    When a value is given and whilst not contained in the dict, a KeyError will be risen."""

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
    """Used to format information from a program readable structure to a more easily human-readable format. All of these
     methods are static."""

    @staticmethod
    def __base_e_collection(collection: typing.Union[typing.Iterable, typing.Sequence, typing.Generator],
                            separator: str = ", ", last_separator: str = " and "):
        if len(collection) == 1:
            return collection[0]
        return separator.join(map(lambda x: str(x), collection[:-1])) + last_separator + str(collection[-1])

    @staticmethod
    def enumerate_collection(collection, separator: str = ", ", last_separator: str = " and ", recursive=False):
        """Takes a collection like a list, tuple or anything else with a join method and converts the contents into a
        human-readable enumeration."""
        if not recursive or all(isinstance(c, str) for c in collection):
            return LanguageFormatter.__base_e_collection(collection, separator, last_separator)

        return LanguageFormatter.enumerate_collection(
            [LanguageFormatter.enumerate_collection(c) + "\n" for c in collection])

    @staticmethod
    def to_abbr_number(number: typing.Union[int, float], max_precision_amt: int = 1, abbreviations: dict = None) -> str:
        if abbreviations is None:
            abbreviations = {"k": 3, "m": 6, "b": 9, "t": 12}
        """Takes a number, which can be an int or a float and abbreviates it into a shorter form. You may pass the
        maximum precise digits in and change the abbreviations for different languages or extend them. Ex: German
        abbreviations: `k; m; mrd; b; brd; t; trd;`. Watch out and clarify to not mix these abbreviations up!"""
        decimal_amt = len(("." + str(float(number)).split(".")[1]).replace(".0", ".")) - 1
        number = int(number * (10 ** decimal_amt))

        ignored_amt = len(str(number)) - max_precision_amt
        abbr, abbr_size = min(abbreviations.items(), key=lambda x: abs(x[1] - ignored_amt + decimal_amt))
        dev_by = 10 ** (abbr_size + decimal_amt)
        rounded_num = round(number, max_precision_amt - len(str(number)))

        pre_formated_str = str(rounded_num / dev_by)
        if pre_formated_str.endswith(".0") and len(pre_formated_str) - 2 >= max_precision_amt:
            pre_formated_str = pre_formated_str[:-2]
        return pre_formated_str + abbr

    @staticmethod
    def abbr_num_to_float(num_str: str, abbreviations: dict = None) -> float:
        """Takes a number (that might as well be generated from toAbbrNumber) and reverts it into the number as a float.
        Confirm that the abbreviations are the same!"""
        if abbreviations is None:
            abbreviations = {"k": 3, "m": 6, "b": 9, "t": 12}
        abbrs_in_num = [c for c in num_str if not c.isdigit()]
        abbrs_in_num.remove(".")
        number = float(num_str.replace("".join(abbrs_in_num), ""))
        for abbr in abbrs_in_num:
            number *= (10 ** abbreviations[abbr])
        return number

    @staticmethod
    def to_abbr_word(word, hard=True, rm_strings="aeiouyäöü"):
        """When using hard, all the non-important characters/strings (usually vowels) will be removed, regardless of
        repetition or position"""
        if hard:
            return word.translate({ord(c): None for c in rm_strings})
        if len(word) <= 4:
            return word

        ret = ""
        for i in range(len(word)):
            end = i + 1 == len(word)
            if not end:
                rm_next = word[i + 1] in rm_strings
            else:
                rm_next = False
            if word[i] in rm_strings and not rm_next and i > 0:
                continue

            ret += word[i]
            if rm_next and word[i] in rm_strings:
                ret += word[i + 1]

        return ret

    @staticmethod
    def to_abbr_sentence(sentence, hard=True, rm_strings="aeiouyäöü"):
        return " ".join([LanguageFormatter.to_abbr_word(word, hard, rm_strings) for word in sentence.split(" ")])


if __name__ == "__main__":
    # tests = {17_234_000_000, 17_234_000_000.5235, 1_234_567_000, 1_234_567_000.5678, 234_567_000, 234_567_000.52348}
    # for i in tests:
    #     for p in range(1, 7):
    #         print(LanguageFormatter.toAbbrNumber(i, p), end = " | ")
    #     print("---")
    print(LanguageFormatter.to_abbr_sentence(
        "Please only use this carefully, it might screw up some text and make it way too hard to read, if you are not "
        "too sure whether this is suitable, definitely disable the \"h a r d\" keyword.",
        hard=False))
