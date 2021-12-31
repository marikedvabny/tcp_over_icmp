import select
import socket

from ToiPackage import ToiHelper
from ToiPackage.ToiProxy import ToiProxy
from tcpovericmputils.stoppablethread import StoppableThread


class ToiClient(ToiProxy, StoppableThread):
    def __init__(self, proxy, local_host, local_port, dest_host, dest_port, **kwargs):
        super().__init__(target=self.serve, **kwargs)
        self.proxy = proxy
        self.local = (local_host, local_port)
        self.dest = (dest_host, dest_port)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind(self.local)
        self.icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        self.loop_flag = True

    def icmp_data_handler(self, sock=None):
        """
        Responsible for the handling of the ICMP data received from the server. Reads the data from the socket for
        further parsing and usage.
        @param sock:        The socket to read the data from
        @return:            None
        """
        print("Handle ICMP")
        packet, addr = sock.recvfrom(ToiHelper.ICMP_BUFFER_SIZE)
        try:
            packet = ToiHelper.ToiPacket.frompacket(packet)
        except ValueError:
            return
        # Looking for icmp reply to send back to the user
        if packet.type == ToiHelper.ICMP_ECHO_REPLY:
            try:
                self.current_tcp_socket.send(packet.data)
            except ConnectionResetError:
                print("ConnectionResetError")
                pass

    def tcp_data_handler(self, sock):
        """
        Responsible for handling with the TCP data. Reads the data from the TCP socket, encapsulates and sends the data
        over the ICMP socket.
        @param sock:        The TCP socket to read from
        @return:            Further action code
        """
        print("Handle TCP")
        packet_data = sock.recv(ToiHelper.TCP_BUFFER_SIZE)
        # determine if continue we will send more packets
        if len(packet_data) > 0:
            code = ToiHelper.CODE_CONTINUE
        else:
            code = ToiHelper.CODE_STOP
        forward_packet = ToiHelper.ToiPacket(ToiHelper.ICMP_ECHO_REQUEST, code, packet_data,
                                             self.tcp_socket.getsockname(), self.dest)  # creating TOI packet object
        # DUMMY_PORT just for using this api
        self.icmp_socket.sendto(forward_packet.pack(), (self.proxy, ToiHelper.DUMMY_PORT))
        return code

    def serve(self):
        """
        Serves the main functionality to the user. It creates a BIND socket for the user to connect to.
        """
        print("Starting Proxy...")
        while True and not self.stopped():
            self.tcp_socket.listen(2)
            self.current_tcp_socket, addr = self.tcp_socket.accept()  # Accepting new connection
            self.sockets = [self.current_tcp_socket, self.icmp_socket]
            self.loop_flag = True
            while self.loop_flag:
                read_sockets = select.select(self.sockets, [], [])[0]
                for sock in read_sockets:
                    if sock.proto == socket.IPPROTO_ICMP:  # Handle Proxy ICMP to client
                        try:
                            self.icmp_data_handler(sock)
                        except Exception as e:
                            print(e)
                    else:
                        try:
                            if self.tcp_data_handler(sock) == ToiHelper.CODE_STOP:  # Handle client tcp to proxy
                                print("Ending Connection")
                                sock.close()
                                self.loop_flag = False
                                break
                        except Exception as e:
                            print(e)

    def stop(self):
        """
        Stop trigger for the proxy thread to enable further connections.
        Closes all open sockets and stops the thread.
        """
        super().stop()
        self.loop_flag = False
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(self.local)
        self.tcp_socket.close()
