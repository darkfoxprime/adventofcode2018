
sum_of_divisors = lambda value: sum(
            divisor
            for divisor in xrange(1, 1 + value)
            if value % divisor == 0
        )

part_1 = lambda: sum_of_divisors(906)
part_2 = lambda: sum_of_divisors(10551306)

print "part 1: {}".format(part_1())
print "part 2: {}".format(part_2())
