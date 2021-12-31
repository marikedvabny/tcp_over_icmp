from abc import ABC, abstractmethod


class ToiProxy(ABC):
    # Abstract class for client and server instances
    @abstractmethod
    def icmp_data_handler(self, sock=None):
        pass

    @abstractmethod
    def tcp_data_handler(self, sock):
        pass

    @abstractmethod
    def serve(self):
        pass
