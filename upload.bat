set /p DUMMY=Updated version number? if so, hit ENTER to continue...
python -m pip install --upgrade build
python -m pip install --upgrade twine
python -m build
python -m twine upload --verbose --repository pypi dist/* --skip-existing
