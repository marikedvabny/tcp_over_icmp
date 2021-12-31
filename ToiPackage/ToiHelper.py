import struct
import socket

TCP_BUFFER_SIZE = 2 ** 10
ICMP_BUFFER_SIZE = 65565
ICMP_ECHO_REPLY = 0
ICMP_ECHO_REQUEST = 8
SOURCE_IP_INDEX = 8
IP_PACKET_SIZE = 20
CODE_CONTINUE = 0
CODE_STOP = 1
DUMMY_PORT = 1
CHECKSUM_ARGUMENT_INDEX = 2
IP_PACK = "BBHHHBBH4s4s"
ICMP_PACK = "!BBH4sH"


class ToiPacket(object):

    def __init__(self, type, code, data, source_ip, dest=(None, None)):
        self.type, self.code, self.data, self.source_ip, self.dest = type, code, data, source_ip, dest
        self.checksum = 0  # place holder checksum
        self.data_size = len(self.data)

    @classmethod
    def frompacket(cls, raw_packet: bytes):
        """
        Receives a raw packet data and creates a ToiPacket object for further handling
        @param raw_packet:          The raw packet received from the socket
        @return:                    ToiPacket object with the received params
        """
        ip_packet, icmp_packet = raw_packet[:IP_PACKET_SIZE], raw_packet[IP_PACKET_SIZE:]
        ip_packet = struct.unpack(IP_PACK, ip_packet)  # unpacking according to IP protocol
        source_ip = socket.inet_ntoa(ip_packet[SOURCE_IP_INDEX])  # convert ip bytes to ascii
        icmp_pack_len = struct.calcsize(ICMP_PACK)
        packet_len = len(icmp_packet) - icmp_pack_len  # checking of there is any data inside the packet

        if packet_len > 0:
            recv_icmp_data = "{}s".format(packet_len)
            data = struct.unpack(recv_icmp_data, icmp_packet[icmp_pack_len:])[0]
        else:
            data = b""

        # Parsing ICMP with TOI protocol
        type, code, checksum, dest_ip, dest_port = struct.unpack(ICMP_PACK, icmp_packet[
                                                                            :icmp_pack_len])
        dest = (socket.inet_ntoa(dest_ip), dest_port)
        return cls(type, code, data, source_ip, dest)

    def pack(self) -> bytes:
        """
        Create a bytes object of the packed ICMP packet to be sent
        @return:        The raw ICMP data to be sent
        """
        struct_pack = ICMP_PACK
        packed_arguments = [self.type, self.code, 0, socket.inet_aton(self.dest[0]), self.dest[1]]
        # check for any data in the packet
        if self.data_size:
            struct_pack += "{}s".format(self.data_size)
            packed_arguments.append(self.data)

        self.checksum = self._checksum(struct.pack(struct_pack, *packed_arguments))
        packed_arguments[CHECKSUM_ARGUMENT_INDEX] = self.checksum
        return struct.pack(struct_pack, *packed_arguments)

    @staticmethod
    def _checksum(buffer: bytes) -> int:
        """
        Calculate the checksum of the data for to create correct ICMP header.
        The calculation is based on the ICMP RFC.
        @param buffer:      The raw data for calculations
        @return:            Calculated checksum
        """
        current_checksum = 0
        count_target = (len(buffer) / 2) * 2
        current_count = 0
        while current_count < count_target - 1:
            current_checksum += buffer[current_count + 1] * 256 + buffer[current_count]
            current_checksum &= 0xffffffff
            current_count += 2
        if count_target < len(buffer):
            current_checksum += buffer[len(buffer) - 1]
            current_checksum &= 0xffffffff

        current_checksum = (current_checksum >> 16) + (current_checksum & 0xffff)
        current_checksum += (current_checksum >> 16)
        checksum = ~current_checksum
        checksum = checksum & 0xffff
        checksum = checksum >> 8 | (checksum << 8 & 0xff00)
        return checksum
