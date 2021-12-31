import threading
import tkinter as tk

from ToiPackage.ToiServer import ToiServer
from tcpovericmputils.ServerGui import ServerGUI


def main_server():
    root = tk.Tk()
    ServerGUI(root)

    server = ToiServer()
    thread = threading.Thread(target=server.serve, args=())
    thread.start()
    root.mainloop()
    thread.join()


if __name__ == "__main__":
    main_server()
