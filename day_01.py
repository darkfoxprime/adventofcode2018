
import sys

def day_01a(input_data):
    return sum(int(freq_adjust) for freq_adjust in input_data.strip().split())

def day_01b(input_data):
    frequency = 0
    seen = set()
    freq_dup = None
    while freq_dup is None:
        input_list = (int(frequency) for frequency in input_data.strip().split())
        for freq_adjust in input_list:
            frequency += freq_adjust
            if frequency in seen:
                freq_dup = frequency
                break
            seen.add(frequency)
    return freq_dup

input_data = open('day_01.input').read()

print "Day 01 a = {}".format(day_01a(input_data))
print "Day 01 b = {}".format(day_01b(input_data))
