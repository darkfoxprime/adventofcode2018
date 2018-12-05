
import re
import sys
import itertools

def process_input_data(input_data):

    # This function: takes the input file as a single string; processes
    # it through a regular expression to populate each record with a
    # year/month/date/hour/minute, and _either_ a guard id, a tag for a
    # guard falling asleep, or a tag for a guard waking up; sorts the
    # list of records based on the timestamp; then reduces that into a
    # mapping of guard ids and the time frames when the respective guard
    # was asleep.

    # The reduction function tracks state (the sleep-time hash, the
    # current guard id, and when the current guard last fell asleep) and
    # returns the next state based on the incoming record: either the
    # same state with a new guard id, or with a new fell-asleep time, or
    # with an updated hash including a new sleeping time frame for a
    # guard.

    # The returned hash is keyed off the guard id and consists of a list
    # of (asleep,awake) pairs.

    # long regular expression to identify the parts of each record
    re_input_data = re.compile(r'''\[(?P<year>[0-9]+)-(?P<month>[0-9]+)-(?P<date>[0-9]+) (?P<hour>[0-5]?[0-9]):(?P<minute>[0-5]?[0-9])\] (?:Guard #(?P<id>[0-9]+) begins shift|(?P<asleep>falls asleep)|(?P<awake>wakes up))''')

    return reduce(

                # reduce the time-sorted list of guard records produced
                # below into a single "state", consisting of: a mapping
                # between guard ids and the list of times when they
                # were asleep, in the form (asleep,awake); the guard id
                # who most recently started their shift; and the time
                # when the guard most recently fell asleep.

                # reduce by the following conditions:
                # * if processing a guard id record, update the guard id
                #   state.
                # * if processing a 'fell asleep' record, update the
                #   time when the guard fell asleep.
                # * if processing a 'woke up' record, update the mapping
                #   dictionary with the guard id and the new list of
                #   sleeping times (consisting of the current list of
                #   sleeping times for the guard id, if it exists, plus
                #   the new sleep time from the last time the guard
                #   fell asleep and the current record time).

                lambda (asleep_times, guard_id, fell_asleep), record:
                    (asleep_times, int(record['id']), None)
                    if record['id']
                    else
                        (asleep_times, guard_id, int(record['minute']))
                        if record['hour'] == '00' and record['asleep']
                        else
                            (
                                dict(
                                    asleep_times.items()
                                    + [(
                                        guard_id,
                                        asleep_times.get(guard_id, [])
                                        + [(fell_asleep, int(record['minute']))]
                                    )]
                                ),
                                guard_id,
                                None
                            ) if record['hour'] == '00' and record['awake']
                            else
                                (asleep_times, guard_id, fell_asleep)
                ,

                # the input to the reduction is a sorted list of guard
                # records, where a single guard record is a dictionary
                # consisting of a 'year', 'month', 'date', 'hour', and
                # 'minute' timestamp, and _either_ a guard 'id', a flag
                # that the guard is now 'asleep', or a flag that the
                # guard is now 'awake'.

                # The list of records is sorted based on the timestamp
                # fields.

                sorted(
                    (
                        record.groupdict()
                        for record in
                        re_input_data.finditer(input_data)
                    )
                    ,
                    key = lambda r:
                        (
                           r['year'],
                           r['month'],
                           r['date'],
                           r['hour'],
                           r['minute']
                        )
                )
                ,

                # the initial state of the reduction is an empty mapping
                # dictionary, no current guard, and no sleeping time.

                ({},None,None)

            )[0] # return just the mapping dictionary

def part_1(input_data):
    # identify the guard who has slept the most number of minutes,
    # then identify the minute (or one of the minutes, if more than one)
    # in which the guard has slept the most number of times, and
    # finally return the product of the guard id multiplied by the minute.

    # The top level is a generator expression, just to have a way to map
    # values to variables within the expression.

    # The generator expression first identifies the guard who slept the
    # most and the time frames when that guard was asleep, using `max`
    # against the list of mappings of guard to sleep times, with a key
    # lambda to sum the duration of the timeframes when each guard in
    # question was asleep.

    # The expression then produces a sequence of minute values when the
    # guard is asleep, reduces that sequence to a hash mapping minute
    # values to counts, and finally uses `max` on the items in that
    # dictionary to identify the minute which occurred most often.

    return (
                # the return expression
                (guard * maxminute)

                # identify the guard who slept the most and the times
                # during which they were asleep.

                for (guard, sleeptimes) in [

                    # using a max function on the input data
                    # and keying off the total sum of the durations
                    # during which the guard in question was asleep.

                    max(
                        input_data.iteritems(),
                        key=lambda (key,value):
                            sum(awake-asleep for (asleep,awake) in value)
                    )

                ]

                # identify the minute during which the identified guard
                # was most often asleep.

                for (maxminute,maxcount) in [

                    # use a max function on a dictionary of how many times
                    # the guard was asleep during each minute
                    # 

                    max(
                        reduce(
                            lambda timecounts, minute:
                                dict(timecounts.items() + [(minute, timecounts.get(minute,0) + 1)])
                            ,
                            itertools.chain(*[xrange(*sleeptime) for sleeptime in sleeptimes])
                            ,
                            {}
                        ).iteritems()
                        ,
                        key = lambda (minute,count):count
                    )

                ]

            ).next()

def part_2(input_data):
    # identify the guard who has slept most often during any particular
    # minute and return the product of the guard's id and the minute most
    # often slept in.
    #
    # do this by translating each mapping of guard to sleep times first
    # to the sequence of individual minutes during which the guard was asleep
    # (no matter which day), then to a dictionary mapping minutes to the number
    # of times each minute occurred, then to the maximum such (count, minute)
    # pairing in the dictionary, then to pairings of (count, guard * minute)
    # for all guards, then to the maximum such (count, guard * minute) pairing,
    # and finally returning just the (guard * minute) portion.

    return max(
                (
                    (count, guard * minute)
                    for (guard, (count, minute)) in
                        (
                            (
                                guard,
                                max(
                                    (count, minute)
                                    for (minute,count) in
                                        reduce(
                                            lambda timecounts, minute:
                                                dict(timecounts.items() + [(minute, timecounts.get(minute,0) + 1)])
                                            ,
                                            sorted(itertools.chain(*[xrange(*sleeptime) for sleeptime in sleeptimes]))
                                            ,
                                            {}
                                        ).iteritems()
                                )
                            )
                            for (guard, sleeptimes) in input_data.iteritems()
                        )
                )
            )[1]

if __name__ == '__main__':

    sample_data = process_input_data(open(__file__.rsplit('.')[0] + '.sample').read())

    print "sample data: part 1 = {}".format(part_1(sample_data))
    print "sample data: part 2 = {}".format(part_2(sample_data))

    input_data = process_input_data(open(__file__.rsplit('.')[0] + '.input').read())

    print "real input: part 1 = {}".format(part_1(input_data))
    print "real input: part 2 = {}".format(part_2(input_data))
