import os
from setuptools import setup
from setuptools.command.install import install
import platform
import subprocess
import pathlib

SETTINGS = {
    "Indentation size (spaces)": 4
}


def _post_install():
    try:
        import appdirs
        import yaml

        d = pathlib.Path(appdirs.user_config_dir(NAME, AUTHOR))
        if not os.path.isdir(d):
            os.makedirs(d)

        filename = "SB_NATIVE_CONFIG.yaml"
        filepath = d.joinpath(filename)
        if filename not in os.listdir(d):
            with open(d.joinpath(filepath), "w") as stream:
                yaml.dump(SETTINGS, stream)

        if platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', str(filepath)))
        elif platform.system() == 'Windows':  # Windows
            os.startfile(str(filepath))
        else:  # linux variants
            subprocess.call(('xdg-open', str(filepath)))
    except ImportError:
        print("appdirs and PyYAML are required for this to work, skipping for now")
        return

class NewInstall(install):
    def __init__(self, *args, **kwargs):
        super(NewInstall, self).__init__(*args, **kwargs)
        _post_install()


def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


AUTHOR = "RICHARD_GALFI"
NAME = "sbNative"

setup(
    name=NAME,
    version="0.0.17-2",
    author=AUTHOR,
    author_email="richardgalfi@gmail.com",
    description="A package for all things that should be native",
    keywords="example documentation tutorial",
    url="https://pypi.org/project/sbNative/",
    install_requires=[
        "appdirs",
        "PyYAML"
    ],
    package_dir={"sbNative": "./src/sbNative"},
    packages=["sbNative"],
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    cmdclass={"install": NewInstall},
)
