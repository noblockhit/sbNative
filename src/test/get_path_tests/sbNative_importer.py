import os, pathlib, importlib
import importlib.util

parent_path = pathlib.Path(os.getcwd()) / "src"
sbNative_parent_path = parent_path.joinpath("sbNative").joinpath("__init__.py")
sbNative_spec = importlib.util.spec_from_file_location("sbNative", sbNative_parent_path)
sbNative = importlib.util.module_from_spec(sbNative_spec)
sbNative_spec.loader.exec_module(sbNative)
