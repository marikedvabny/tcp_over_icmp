from unittest import TestCase

from ToiPackage import ToiHelper


class TestToiPacket(TestCase):
    def test__checksum(self):
        packet = ToiHelper.ToiPacket(0, 0, b"ABCDEFGHIJK", "1.1.1.1", ("2.2.2.2", 80))
        packet.pack()
        self.assertEqual(packet.checksum, 41292)

