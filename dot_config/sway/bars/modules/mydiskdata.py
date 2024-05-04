# -*- coding: utf-8 -*-
"""
Display advanced disk usage information

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds.
        (default 10)
    disk: disk or partition whose stat to check. Set to None to get global stats.
        (default None)
    format: format of the output.
        (default "{disk}: {used_percent}% ({total})")
    format_rate: format for the rates value
        (default "[\?min_length=11 {value:.1f} {unit}]")
    format_space: format for the disk space values
        (default "[\?min_length=5 {value:.1f}]")
    sector_size: size of the disk's sectors.
        (default 512)
    si_units: use SI units
        (default False)
    thresholds: thresholds to use for color changes
        *(default {'free': [(0, 'bad'), (10, 'degraded'), (100, 'good')],
        'total': [(0, "good"), (1024, 'degraded'), (1024 * 1024, 'bad')]})*
    unit: unit to use. If the unit contains a multiplier prefix, only this
        exact unit will ever be used
        (default "B/s")

Format placeholders:
    {disk} the selected disk
    {free} free space on disk in GB
    {used} used space on disk in GB
    {used_percent} used space on disk in %
    {read} reading rate
    {total} total IO rate
    {write} writing rate

format_rate placeholders:
    {unit} name of the unit
    {value} numeric value of the rate

format_space placeholders:
    {value} numeric value of the free/used space on the device

Color thresholds:
    {free} Change color based on the value of free
    {used} Change color based on the value of used_percent
    {read} Change color based on the value of read
    {total} Change color based on the value of total
    {write} Change color based on the value of write

@author guiniol
@license BSD
"""

from __future__ import division  # python2 compatibility
from time import time
import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    disk = None
    format = "{disk}: {used_percent}% ({total})"
    format_rate = "[\?min_length=11 {value:.1f} {unit}]"
    format_space = "[\?min_length=5 {value:.1f}]"
    sector_size = 512
    si_units = False
    thresholds = {
        'free': [(0, "bad"), (10, "degraded"), (100, "good")],
        'total': [(0, "good"), (1024, "degraded"), (1024 * 1024, "bad")]
    }
    unit = "B/s"

    def __init__(self, *args, **kwargs):
        """
        Format of total, up and down placeholders under self.format.
        As default, substitutes self.left_align and self.precision as %s and %s
        Placeholders:
            value - value (float)
            unit - unit (string)
        """
        self.last_interface = None
        self.last_stat = self._get_io_stats(self.disk)
        self.last_time = None

    def space_and_io(self):

        self.values = {'disk': self.disk if self.disk else 'all'}

        if '{read}' in self.format or '{write}' in self.format or '{total}' in self.format:
            # time from previous check
            ios = self._get_io_stats(self.disk)
            if self.last_time == None:
                read = 0
                write = 0
            else:
                timedelta = time() - self.last_time

                read = ios[0] - self.last_stat[0]
                write = ios[1] - self.last_stat[1]
                read /= timedelta
                write /= timedelta

            total = read + write

            # update last_ info
            self.last_stat = self._get_io_stats(self.disk)
            self.last_time = time()

            self.values['read'] = self._format_rate(read)
            self.values['total'] = self._format_rate(total)
            self.values['write'] = self._format_rate(write)
            self.py3.threshold_get_color(read, 'read')
            self.py3.threshold_get_color(total, 'total')
            self.py3.threshold_get_color(write, 'write')

        if '{free}' in self.format or '{used' in self.format:
            free, used, used_percent = self._get_free_space(self.disk)

            self.values['free'] = self.py3.safe_format(self.format_space, {'value': free})
            self.values['used'] = self.py3.safe_format(self.format_space, {'value': used})
            self.values['used_percent'] = self.py3.safe_format(self.format_space,
                                                               {'value': used_percent})
            self.py3.threshold_get_color(free, 'free')
            self.py3.threshold_get_color(used, 'used')

        return {'cached_until': self.py3.time_in(self.cache_timeout),
                'full_text': self.py3.safe_format(self.format, self.values)}

    def _get_free_space(self, disk):
        if disk and not disk.startswith('/dev/'):
            disk = '/dev/' + disk

        total = 0
        used = 0
        free = 0

        df = subprocess.check_output(['df']).decode('utf-8')
        for line in df.splitlines():
            if (disk and line.startswith(disk)) or (disk is None and line.startswith('/dev/')):
                data = line.split()
                total += int(data[1]) / 1024 / 1024
                used += int(data[2]) / 1024 / 1024
                free += int(data[3]) / 1024 / 1024

        if total == 0:
            return free, used, 'err'

        return free, used, 100 * used / total

    def _get_io_stats(self, disk):
        if disk and disk.startswith('/dev/'):
            disk = disk[5:]
        read = 0
        write = 0
        with open('/proc/diskstats', 'r') as fd:
            for line in fd:
                if disk and disk in line:
                    data = line.split()
                    read += int(data[5]) * self.sector_size
                    write += int(data[9]) * self.sector_size
                else:
                    data = line.split()
                    if data[1] == '0':
                        read += int(data[5]) * self.sector_size
                        write += int(data[9]) * self.sector_size
        return read, write

    def _format_rate(self, value):
        """
        Return formatted string
        """
        value, unit = self.py3.format_units(value, unit=self.unit, si=self.si_units)
        return self.py3.safe_format(self.format_rate, {'value': value, 'unit': unit})


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)