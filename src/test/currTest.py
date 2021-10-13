from pathlib import Path
import sys

pathToAdd = Path(__file__).parent.parent

sys.path.append(str(pathToAdd))

from sbNative import runtimetools

# lst = list(range(10))

# for idx,item in enumerate(runtimetools.safeIter(lst)):
#     print(item)
#     if item == 5:
#         lst.pop(idx)

# lst2 = list(range(10))

# for idx,item in enumerate(lst2):
#     print(item)
#     if item == 5:
#         lst2.pop(idx)

lst = [1,2,3,4]

for item in lst:#runtimetools.safeIter(lst):
    print(item)
    lst.remove(item)