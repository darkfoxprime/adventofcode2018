
import sys

def process_input_data(input_data):
    return input_data.strip().split()

def part_1(input_data):
    return sum(int(freq_adjust) for freq_adjust in input_data)

def part_2(input_data):
    frequency = 0
    seen = set()
    freq_dup = None
    while freq_dup is None:
        input_list = (int(frequency) for frequency in input_data)
        for freq_adjust in input_list:
            frequency += freq_adjust
            if frequency in seen:
                freq_dup = frequency
                break
            seen.add(frequency)
    return freq_dup

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    print "sample data: part 2 = {}".format(part_2(sample_data))

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data))
