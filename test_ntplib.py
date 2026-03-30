"""Python NTP library tests."""


import datetime
import socket
import time
import unittest

import ntplib


class TestNTPLib(unittest.TestCase):
    """ Main test. """

    # Test NTP server.
    NTP_SERVER = "time.cloudflare.com"

    # Tolerance for offset/delay comparisons, in seconds.
    DELTA_TOLERANCE = 0.5


    def test_basic(self):
        """Basic tests."""
        self.assertTrue(issubclass(ntplib.NTPException, Exception))

        ntplib.NTPClient()

    def test_request(self):
        """Request tests."""
        client = ntplib.NTPClient()

        t_1 = time.time()
        info = client.request(self.NTP_SERVER)
        t_2 = time.time()

        # check response
        self.assertTrue(isinstance(info, ntplib.NTPStats))
        self.assertTrue(0 < info.version <= 4)
        self.assertTrue(isinstance(info.offset, float))
        self.assertTrue(0 <= info.stratum < 0xff)
        self.assertTrue(-0x7f <= info.precision < 0x7f)
        self.assertTrue(isinstance(info.root_delay, float))
        self.assertTrue(isinstance(info.root_dispersion, float))
        self.assertTrue(isinstance(info.delay, float))
        self.assertTrue(isinstance(info.leap, int))
        self.assertIn(info.leap, ntplib.NTP.LEAP_TABLE)
        self.assertTrue(0 <= info.poll < 0xfff)
        self.assertTrue(isinstance(info.mode, int))
        self.assertIn(info.mode, ntplib.NTP.MODE_TABLE)
        self.assertTrue(0 <= info.ref_id < 0xffffffff)
        self.assertTrue(isinstance(info.tx_time, float))
        self.assertTrue(isinstance(info.ref_time, float))
        self.assertTrue(isinstance(info.orig_time, float))
        self.assertTrue(isinstance(info.recv_time, float))
        self.assertTrue(isinstance(info.dest_time, float))

        new_info = client.request(self.NTP_SERVER)

        # check timestamps
        self.assertTrue(t_1 < info.orig_time < info.dest_time < t_2)
        self.assertTrue(info.orig_time < new_info.orig_time)
        self.assertTrue(info.recv_time < new_info.recv_time)
        self.assertTrue(info.tx_time < new_info.tx_time)
        self.assertTrue(info.dest_time < new_info.dest_time)

        # check the offset and delay
        self.assertLess(abs(new_info.offset - info.offset),
                        self.DELTA_TOLERANCE)
        self.assertLess(abs(new_info.delay - info.delay), self.DELTA_TOLERANCE)

        # try reaching a non existent server
        self.assertRaises(ntplib.NTPException,
                          client.request, "localhost", port=42)

        # try reaching a non existent server with a custom timeout
        t_before = time.time()
        self.assertRaises(ntplib.NTPException,
                          client.request, "localhost", port=42, timeout=1)
        self.assertTrue(0.7 < time.time() - t_before < 1.3)

    def test_helpers(self):
        """Helper methods tests."""
        client = ntplib.NTPClient()

        info = client.request(self.NTP_SERVER)

        # This will fail after 2036-02-07 06:28:16 UTC, but we can test it with the current time.
        self.assertEqual(int(info.tx_time), ntplib.ntp_to_system_time(
                         ntplib.system_to_ntp_time(int(info.tx_time))))

        self.assertTrue(isinstance(ntplib.leap_to_text(info.leap), str))
        self.assertTrue(isinstance(ntplib.mode_to_text(info.mode), str))
        self.assertTrue(isinstance(ntplib.stratum_to_text(info.stratum), str))
        self.assertTrue(isinstance(ntplib.ref_id_to_text(info.ref_id,
                                                         info.stratum), str))

    def test_ntp_to_system_time(self):
        """ Test for ntp_to_system_time """
        epoch = datetime.datetime.utcfromtimestamp(0)

        ntp_timestamp = -1
        self.assertRaises(AssertionError,
                          ntplib.ntp_to_system_time, ntp_timestamp)

        ntp_timestamp =          0.0 # 1900-01-01 00:00:00 UTC in NTP time
        system_timestamp = (datetime.datetime(2036, 2, 7, 6, 28, 16) - epoch).total_seconds()
        self.assertEqual(system_timestamp, ntplib.ntp_to_system_time(ntp_timestamp))

        ntp_timestamp =      63104.0 # 1900-01-01 00:00:00 UTC in NTP time
        system_timestamp = (datetime.datetime(2036, 2, 8) - epoch).total_seconds()
        self.assertEqual(system_timestamp, ntplib.ntp_to_system_time(ntp_timestamp))

        ntp_timestamp = 2147480000.0 # 1968-01-20 02:13:20 UTC in NTP time
        system_timestamp = (datetime.datetime(2104, 2, 26, 8, 41, 36) - epoch).total_seconds()
        self.assertEqual(system_timestamp, ntplib.ntp_to_system_time(ntp_timestamp))

        ntp_timestamp = 2147580000.0 # 1968-01-21 06:00:00 UTC in NTP time
        system_timestamp = (datetime.datetime(1968, 1, 21, 6, 0, 0) - epoch).total_seconds()
        self.assertEqual(system_timestamp, ntplib.ntp_to_system_time(ntp_timestamp))

        ntp_timestamp = 4294944000.0 # 2036-02-07 00:00:00 UTC in NTP time
        system_timestamp = (datetime.datetime(2036, 2, 7) - epoch).total_seconds()
        self.assertEqual(system_timestamp, ntplib.ntp_to_system_time(ntp_timestamp))

        ntp_timestamp = 4295030400.0 # 2036-02-08 00:00:00 UTC in NTP time
        self.assertRaises(AssertionError,
                          ntplib.ntp_to_system_time, ntp_timestamp)

    def test_system_to_ntp_time(self):
        """ Test for system_to_ntp_time """
        epoch = datetime.datetime.utcfromtimestamp(0)

        system_timestamp = (datetime.datetime(1900, 1, 1) - epoch).total_seconds()
        ntp_timestamp =          0.0 # 1900-01-01 00:00:00 UTC in NTP time
        self.assertEqual(ntp_timestamp, ntplib.system_to_ntp_time(system_timestamp))

        system_timestamp = (datetime.datetime(1900, 1, 1, 17, 31, 44) - epoch).total_seconds()
        ntp_timestamp =      63104.0 # 1900-01-01 17:31:44 UTC in NTP time
        self.assertEqual(ntp_timestamp, ntplib.system_to_ntp_time(system_timestamp))

        system_timestamp = (datetime.datetime(2036, 2, 7) - epoch).total_seconds()
        ntp_timestamp = 4294944000.0 # 2036-02-07 00:00:00 UTC in NTP time
        self.assertEqual(ntp_timestamp, ntplib.system_to_ntp_time(system_timestamp))

        # Note: yes, there's an ambiguity for dates beyond 2036-02-07, but it's expected
        # due to how we handle the Y2036 rollover.
        system_timestamp = (datetime.datetime(2036, 2, 8) - epoch).total_seconds()
        ntp_timestamp =      63104.0 # 2036-02-08 00:00:00 UTC in NTP time (after rollover)
        self.assertEqual(ntp_timestamp, ntplib.system_to_ntp_time(system_timestamp))

    def test_rollover(self):
        """ Test for rollover - see
            https://en.wikipedia.org/wiki/Network_Time_Protocol#Timestamps.
        """
        epoch = datetime.datetime.utcfromtimestamp(0)

        timestamp = (datetime.datetime(1968, 1, 20) - epoch).total_seconds()
        # Note: this is expected due to how we handle Y2036 rollover.
        self.assertNotEqual(
                ntplib.ntp_to_system_time(ntplib.system_to_ntp_time(timestamp)),
                timestamp)

        timestamp = (datetime.datetime(1968, 1, 21) - epoch).total_seconds()
        self.assertEqual(
                ntplib.ntp_to_system_time(ntplib.system_to_ntp_time(timestamp)),
                timestamp)

        timestamp = (datetime.datetime(2022, 8, 5, 19, 8, 42) - epoch).total_seconds()
        self.assertEqual(
                ntplib.ntp_to_system_time(ntplib.system_to_ntp_time(timestamp)),
                timestamp)

        timestamp = (datetime.datetime(2036, 2, 7) - epoch).total_seconds()
        self.assertEqual(
                ntplib.ntp_to_system_time(ntplib.system_to_ntp_time(timestamp)),
                timestamp)

        timestamp = (datetime.datetime(2036, 2, 8) - epoch).total_seconds()
        self.assertEqual(
                ntplib.ntp_to_system_time(ntplib.system_to_ntp_time(timestamp)),
                timestamp)

        timestamp = (datetime.datetime(2104, 2, 26) - epoch).total_seconds()
        self.assertEqual(
                ntplib.ntp_to_system_time(ntplib.system_to_ntp_time(timestamp)),
                timestamp)

        timestamp = (datetime.datetime(2104, 2, 27) - epoch).total_seconds()
        # Note: this is expected due to how we handle Y2036 rollover.
        self.assertNotEqual(
                ntplib.ntp_to_system_time(ntplib.system_to_ntp_time(timestamp)),
                timestamp)

    def test_address_family(self):
        """ Test support of socket address family. """
        for address_family in [socket.AF_UNSPEC, socket.AF_INET]:
            client = ntplib.NTPClient()
            info = client.request(self.NTP_SERVER, address_family=address_family)
            self.assertLessEqual(info.offset, self.DELTA_TOLERANCE)


if __name__ == "__main__":
    unittest.main()
