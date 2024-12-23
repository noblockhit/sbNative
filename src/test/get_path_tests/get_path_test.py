from sbNative_importer import sbNative

current_path = sbNative.runtimetools.get_path()
testfile_path = current_path.joinpath("testfile.txt")
sbNative.debugtools.log(f"{current_path = }")
sbNative.debugtools.log(f"{testfile_path}")
with open(testfile_path, "r") as rf:
    content = rf.read()
    assert content == "0123456789", "Non maching data"
    sbNative.debugtools.log(f"{content = }")
