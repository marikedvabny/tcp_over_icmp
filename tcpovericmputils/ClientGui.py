import ipaddress
import tkinter as tk
import tkinter.messagebox as messagebox
from threading import Thread

from ToiPackage.ToiClient import ToiClient


class ClientGui(object):
    def __init__(self):
        self.window = tk.Tk()

        # Proxy params
        self.server_ip: tk.StringVar = None
        self.dest_ip: tk.StringVar = None
        self.dest_port: tk.IntVar = None
        self.proxy_port: tk.IntVar = None

        # UI related objects
        self.start_button: tk.Button = None
        self.stop_button: tk.Button = None
        self.dest_ip_entry: tk.Entry = None
        self.server_ip_entry: tk.Entry = None
        self.dest_port_entry: tk.Entry = None
        self.proxy_port_entry: tk.Entry = None
        self.proxy_instance = None
        self.proxy_thread: Thread = None
        self.setup_window()

    def setup_window(self):
        """
        Setup the window inteface for the user
        @return:
        """
        self.window.geometry('300x200')
        self.window.title('TCP over ICMP tunnel Client')
        self.setup_inputs()
        self.setup_buttons()

    def setup_inputs(self):
        """
        Create all the relevant input fields the user will use to configure his connection
        @return:
        """
        server_ip_label = tk.Label(self.window, text="Tunnel Server IP").grid(row=0, column=0)
        self.server_ip = tk.StringVar()
        self.server_ip_entry = tk.Entry(self.window, textvariable=self.server_ip)
        self.server_ip_entry.grid(row=0, column=1)
        dest_ip_label = tk.Label(self.window, text="Destination Server ip").grid(row=1, column=0)
        self.dest_ip = tk.StringVar()
        self.dest_ip_entry = tk.Entry(self.window, textvariable=self.dest_ip)
        self.dest_ip_entry.grid(row=1, column=1)
        dest_port_label = tk.Label(self.window, text="Destination Server port").grid(row=2, column=0)
        self.dest_port = tk.IntVar()
        self.dest_port_entry = tk.Entry(self.window, textvariable=self.dest_port)
        self.dest_port_entry.grid(row=2, column=1)
        proxy_port_label = tk.Label(self.window, text="Proxy client port").grid(row=3, column=0)
        self.proxy_port = tk.IntVar()
        self.proxy_port_entry = tk.Entry(self.window, textvariable=self.proxy_port)
        self.proxy_port_entry.grid(row=3, column=1)

    def setup_buttons(self):
        """
        Create the buttons in the user interface
        @return:
        """
        self.start_button = tk.Button(self.window, text="Start", state="active", command=self.start_proxy)
        self.start_button.grid(row=4, column=0)
        self.stop_button = tk.Button(self.window, text="Stop", state="disabled", command=self.stop_proxy)
        self.stop_button.grid(row=4, column=1)

    def check_params(self) -> bool:
        """
        Validate all the params the user entered are correct. The function will check if the entered IP is correct,
        the ports are indeed of type int and will throw an error window in case the user entered a wrong input.
        @return:        None
        """
        if not self.check_ip(self.server_ip.get()):
            self.show_error("Invalid proxy server IP entered")
            return False
        elif not self.check_ip(self.dest_ip.get()):
            self.show_error("Invalid destination IP entered")
            return False
        try:
            self.dest_port.get()
            self.proxy_port.get()
        except tk.TclError:
            self.show_error("Port must be an integer!")
            return False
        return True

    def start_proxy(self):
        """
        Creates a new thread of the ToiClient object to handle the new connection.
        @return:
        """
        if not self.check_params():
            return
        self.start_button["state"] = tk.DISABLED
        self.stop_button["state"] = tk.ACTIVE
        self.dest_port_entry["state"] = tk.DISABLED
        self.dest_ip_entry["state"] = tk.DISABLED
        self.proxy_port_entry["state"] = tk.DISABLED
        self.server_ip_entry["state"] = tk.DISABLED
        self.proxy_instance = ToiClient(proxy=self.server_ip.get(), local_host="127.0.0.1",
                                        local_port=self.proxy_port.get(),
                                        dest_host=self.dest_ip.get(), dest_port=self.dest_port.get())
        self.proxy_instance.start()

    def stop_proxy(self):
        """
        Stops the current running thread to enable the user to create and configure a new connection
        @return:
        """
        self.stop_button["state"] = tk.DISABLED
        self.start_button["state"] = tk.ACTIVE
        self.dest_port_entry["state"] = tk.NORMAL
        self.dest_ip_entry["state"] = tk.NORMAL
        self.proxy_port_entry["state"] = tk.NORMAL
        self.server_ip_entry["state"] = tk.NORMAL
        self.proxy_instance.stop()
        self.proxy_instance.join()

    def spawn_gui(self):
        self.window.mainloop()

    @staticmethod
    def show_error(error_message: str):
        messagebox.showerror("Error", error_message)

    @staticmethod
    def check_ip(ip: str):
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return False
        return True
