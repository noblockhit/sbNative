from sbNative_importer import sbNative

current_path = sbNative.runtimetools.get_path()
testfile_path = current_path.joinpath("testfile.txt")
print(f"{current_path = }")
print(f"{testfile_path}")
with open(testfile_path, "r") as rf:
    content = rf.read()
    assert content == "0123456789", "Non maching data"
    print(f"{content = }")
