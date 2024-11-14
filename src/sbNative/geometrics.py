import math
import itertools
import string


class Point:
    def __init__(self, *values):
        for n, v in self.pair_axis_names_to_values(values):
            self.__setattr__(n, v)

    @staticmethod
    def pair_axis_names_to_values(values):
        if len(values) < 5:
            axis = "xyzw"
        else:
            axis = list(itertools.chain.from_iterable(
                [[prefix+suffix for prefix in string.ascii_lowercase[:-3]] for suffix in "xyz"]))
            value_axis_relation = len(values) / len(axis)
            if value_axis_relation >= 1:
                axis *= math.ceil(value_axis_relation)
                for i in range(len(axis)):
                    middle = int(i/23)
                    axis[i] = F"{axis[i][0]}{middle}{axis[i][-1]}"

        return zip(axis[:len(values)], values)
