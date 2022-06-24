import decimal
import math
from pprint import pprint


# table:
# [ thre(i), thre(i+1), k, gain, offset ]
# where:
#   - thre(i) is THRESHOLD of the actual interval
#   - k is the constant value of actual interval (as thre(1)+ gain(1)*(thre(2)– thre(1)))
# Example: [0.1, 0.2, 0.3, 4.0, -0.5]
#   will be interpreted as
#   if 0.1<=v<0.2:
#       out = 0.3 + 4.0*(v - 0.5)
# table = [
#    [0.0, 0.1,      0.0, 1.0,  0.0],
#    [0.1, 0.2,      0.1, 2.0, -0.1],
#    [0.2, 0.3,      0.3, 3.0, -0.2],
#    [0.3, 0.4,      0.6, 4.0, -0.3],
#    [0.4, 1.0,      1.0, 0.0,  0.0]
# ]

class FertilizationStrategy:
    def set_parameters(self, thresholds, gains):
        i = 0;
        low = 0.0
        k = 0.0
        for v in thresholds:
            self.table.append([low, thresholds[i], k, gains[i], -low])
            k = round(k + gains[i] * (thresholds[i] - low), 10)
            low = thresholds[i]
            i = i + 1
        self.table.append([low, 1, 1.0, 0.0, 0.0])

    def __init__(self, is_intensive, thresholds, gains, coeffs, nplants, grainpp, nitropg, nitropkgf):
        self.table = []
        self.is_intensive = is_intensive
        self.set_parameters(thresholds, gains)

        self.max_step = 1
        for j in range(1, len(self.table)):
            d = decimal.Decimal(str(self.table[j][0]))
            if d.as_tuple().exponent < self.max_step:
                self.max_step = d.as_tuple().exponent

        self.max_step = 10 ** self.max_step

        self.table_optimized = {}
        s = 0
        index = 0
        while s < 1 + self.max_step:
            while self.table[index][1] < s:
                index += 1
            self.table_optimized[s] = [self.table[index][2], self.table[index][3], self.table[index][4]]
            s += self.max_step
            s = round(s, 10)

        self.fiso = coeffs[0]*coeffs[1]*coeffs[2]*(nplants * grainpp * nitropg / nitropkgf) * 1000

    def get_fertilization_value(self, ndvi, ndvi_mean):
        v = abs(ndvi - ndvi_mean)
        if v < 1:
            key = round(math.trunc(round(v, 10) / self.max_step) * self.max_step, 10)
            out = self.table_optimized[key][0] + self.table_optimized[key][1] * (v + self.table_optimized[key][2])

            if ndvi < ndvi_mean:
                out = 1 + out
            else:
                out = 1 - out

            out = round(self.fiso * out, 0)
        else:
            out = -1
        if not self.is_intensive:
            if out > self.fiso:
                out = self.fiso
        return out
'''
        if self.is_intensive:
            v = abs(ndvi - ndvi_mean)

            if v < 1:
                key = round(math.trunc(round(v, 10) / self.max_step) * self.max_step, 10)
                out = self.table_optimized[key][0] + self.table_optimized[key][1] * (v + self.table_optimized[key][2])

                if ndvi < ndvi_mean:
                    out = 1 + out
                else:
                    out = 1 - out

                out = round(self.fiso * out, 0)
            else:
                out = -1
        else:
            out = self.fiso

        return out
'''