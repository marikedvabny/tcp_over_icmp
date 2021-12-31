import logging
import select
import socket

import ToiHelper
from ToiProxy import ToiProxy

logger = logging.getLogger("TOIServer")


class ToiServer(ToiProxy):
    def __init__(self):
        self.tcp_socket, self.source, self.dest = None, None, None
        self.icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        self.sockets = [self.icmp_socket]

    def icmp_data_handler(self, sock: socket.socket = None):
        """
        Handles the received ICMP echo requests from the client, reads the data and sends it to the destination TCP
        socket. It reads the initial values from the ICMP connection to create the initial connection to the user
        defined destination.
        @param sock:        None as it is an ICMP connection
        @return:            None
        """
        packet, addr = self.icmp_socket.recvfrom(ToiHelper.ICMP_BUFFER_SIZE)
        try:
            packet = ToiHelper.ToiPacket.frompacket(packet)
        except ValueError:
            logger.info("Received Malformed ICMP Packet")
            return
        logger.info("Received ICMP packet: Type = {}, Code = {}, Checksum: {}".format(packet.type, packet.code,
                                                                                      packet.checksum))

        if packet.type == ToiHelper.ICMP_ECHO_REPLY and packet.code == ToiHelper.CODE_CONTINUE:
            # No need to handle
            return
        self.source = addr[0]
        self.dest = packet.dest
        if packet.type == ToiHelper.ICMP_ECHO_REQUEST and packet.code == ToiHelper.CODE_STOP:
            # Closing socket
            logger.info("Closing socket by client")
            if self.tcp_socket in self.sockets:  # cleaning socket from lists
                self.sockets.remove(self.tcp_socket)
            if self.tcp_socket:
                self.tcp_socket.close()
            self.tcp_socket = None
        else:
            # Handle TCP
            if not self.tcp_socket:
                self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    self.tcp_socket.connect(self.dest)
                except ConnectionRefusedError:
                    logger.info("Dest Server Closed")
                    self.tcp_socket.close()
                    self.tcp_socket = None
                    return
                self.sockets.append(self.tcp_socket)
            self.tcp_socket.send(packet.data)
            logger.info(
                "Sent TCP Packet: Dest IP = {}, Dest Port = {}, Data Size = {}".format(self.dest[0], self.dest[1],
                                                                                       packet.data_size))

    def tcp_data_handler(self, sock: socket.socket):
        """
        Handles the TCP connection to the destination server. The data received is sent over an ICMP REPLY to the
        connected client.
        @param sock:            The TCP socket the server is responsible on handling for the client
        @return:                None
        """
        try:
            packet_data = sock.recv(ToiHelper.TCP_BUFFER_SIZE)
        except OSError:
            return
        received_packet = ToiHelper.ToiPacket(ToiHelper.ICMP_ECHO_REPLY, ToiHelper.CODE_CONTINUE, packet_data,
                                              self.source, self.dest)  # Creating TOI packet object
        self.icmp_socket.sendto(received_packet.pack(),
                                (self.source, ToiHelper.DUMMY_PORT))  # DUMMY_PORT just for using this api
        logger.info("Received and sent back to client: Dest IP = {}, Dest Port = {}, Data Size = {}".format(
            sock.getpeername()[0], sock.getpeername()[1], len(packet_data)))
        if len(packet_data) == 0:
            logger.info("Closing socket by server")
            # Cleaning socket from lists
            if self.tcp_socket in self.sockets:
                self.sockets.remove(self.tcp_socket)
            if self.tcp_socket:
                self.tcp_socket.close()
            self.tcp_socket = None

    def serve(self):
        """
        The main function responsible for serving the server
        """
        logger.info("Starting Server...")
        while True:
            # Looking for new packets
            read_sockets = select.select(self.sockets, [], [])[0]
            for sock in read_sockets:
                if sock.proto == socket.IPPROTO_ICMP:
                    # Handle requests from client
                    self.icmp_data_handler()
                else:
                    # Handle Dest back to client
                    self.tcp_data_handler(sock)
