
import re
import sys
import itertools

def process_input_data(input_data):
    re_input_data = re.compile(r'''\[(?P<year>[0-9]+)-(?P<month>[0-9]+)-(?P<date>[0-9]+) (?P<hour>[0-5]?[0-9]):(?P<minute>[0-5]?[0-9])\] (?:Guard #(?P<id>[0-9]+) begins shift|(?P<asleep>falls asleep)|(?P<awake>wakes up))''')
    return reduce(
                lambda (asleep_times, guard_id, fell_asleep), record:
                    (asleep_times, int(record['id']), None) if record['id']
                    else
                        (asleep_times, guard_id, int(record['minute'])) if record['hour'] == '00' and record['asleep']
                        else
                            (
                                dict(
                                    asleep_times.items()
                                    + [(
                                        guard_id,
                                        asleep_times.get(guard_id, []) + [(fell_asleep, int(record['minute']))]
                                    )]
                                ),
                                guard_id,
                                None
                            ) if record['hour'] == '00' and record['awake']
                            else
                                (asleep_times, guard_id, fell_asleep)
                ,
                sorted(
                    (
                        record.groupdict()
                        for record in
                        re_input_data.finditer(input_data)
                    )
                    ,
                    key = lambda r:(r['year'],r['month'],r['date'],r['hour'],r['minute'])
                )
                ,
                ({},None,None)
            )[0]

def day_04a(input_data):
    return (
                (guard * maxminute)
                for (guard, sleeptimes) in
                [max(input_data.iteritems(), key=lambda (key,value):sum(awake-asleep for (asleep,awake) in value))]
                for (maxminute,maxcount) in [
                    max(
                        reduce(
                            lambda timecounts, minute:
                                dict(timecounts.items() + [(minute, timecounts.get(minute,0) + 1)])
                            ,
                            sorted(itertools.chain(*[xrange(*sleeptime) for sleeptime in sleeptimes]))
                            ,
                            {}
                        ).iteritems()
                        ,
                        key = lambda (minute,count):count
                    )
                ]
            ).next()

def day_04b(input_data):
    return max(
                (
                    (guard * minute, count)
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
                ,
                key = lambda (gm,c): c
            )[0]

if __name__ == '__main__':

    input_data = process_input_data(open('day_04.sample').read())

    print "sample data: Day 04 a = {}".format(day_04a(input_data))
    print "sample data: Day 04 b = {}".format(day_04b(input_data))

    input_data = process_input_data(open('day_04.input').read())

    print "real input: Day 04 a = {}".format(day_04a(input_data))
    print "real input: Day 04 b = {}".format(day_04b(input_data))

