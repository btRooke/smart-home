from device_configurator import *
from tkinter import *
from tkinter.filedialog import *
import threading

class ConverterGUI:
    def __init__(self, master):
        self.master = master
        master.title("IoT Device Configurator")
        
        self.device_port = StringVar()
        
        self.refresh_devices_button = Button(self.master, text="Refresh Device Ports", command=self.start_refresh_connected_iot_devices)
        self.refresh_devices_button.grid(row=0, column=2, padx=10, pady=10)

        self.device_selection_dropdown = OptionMenu(self.master, self.device_port, "None")
        self.device_selection_dropdown.grid(row=0, column=1, padx=10, pady=10)

        self.device_selection_label = Label(self.master, text="Select a port: ", bg="white")
        self.device_selection_label.grid(row=0, column=0, sticky=W, padx=10, pady=10)

        self.ssid = StringVar()

        self.ssid_label = Label(self.master, text="WiFi SSID: ", bg="white")
        self.ssid_label.grid(row=1, column=0, sticky=W, padx=10, pady=10)

        self.ssid = Entry(self.master, textvariable=self.ssid)
        self.ssid.grid(row=1, column=1, columnspan=2, padx=10, pady=10)

        self.wifi_password_label = Label(self.master, text="WiFi Password: ", bg="white")
        self.wifi_password_label.grid(row=2, column=0, sticky=W, padx=10, pady=10)

        self.wifi_password = StringVar()

        self.wifi_password = Entry(self.master, textvariable=self.wifi_password)
        self.wifi_password.grid(row=2, column=1, columnspan=2, padx=10, pady=10)
        
        self.status_text = StringVar()
        
        self.status = Label(master, textvariable=self.status_text, bg="gray", bd=5)
        self.status_text.set("Status: Idle")
        self.status.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        self.apply_button = Button(self.master, text="Apply WiFi Config", command=self.start_apply_configuration_to_device)
        self.apply_button.grid(row=3, column=2, padx=10, pady=10)

        self.ip_label_label = Label(self.master, text="Device IP: ", bg="white")
        self.ip_label_label.grid(row=4, column=0, sticky=W, padx=10, pady=10)

        self.ip = StringVar()

        self.ip_label = Label(self.master, textvariable=self.ip, bg="white")
        self.ip_label.grid(row=4, column=1, columnspan=2, sticky=W, padx=10, pady=10)

        self.auth_key_label_label = Label(self.master, text="Auth Key: ", bg="white")
        self.auth_key_label_label.grid(row=5, column=0, sticky=W, padx=10, pady=10)

        self.auth_key = StringVar()

        self.auth_key_label = Label(self.master, textvariable=self.auth_key, bg="white")
        self.auth_key_label.grid(row=5, column=1, columnspan=2, sticky=W, padx=10, pady=10)

        self.refresh_details_button = Button(self.master, text="Refresh Selected Device's IP and Auth Key", command=self.start_refresh_details)
        self.refresh_details_button.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

        self.start_refresh_connected_iot_devices()

    def refresh_connected_iot_devices(self):
        try:
            self.devices_connected = get_iot_device_ports()
            
        except: # Errors caused by device being plugged in during search
            self.status_text.set("Status: Error scanning, try again")
            self.status.config(bg="red")
            return

        self.refresh_devices_connected_dropdown()
            
        self.status_text.set("Status: Refreshed")
        self.status.config(bg="green")


    def start_refresh_connected_iot_devices(self):
        threading.Thread(target=self.refresh_connected_iot_devices).start()
        self.status_text.set("Status: Looking for devices")
        self.status.config(bg="yellow")

    def refresh_devices_connected_dropdown(self):
        self.device_selection_dropdown.destroy()
        
        if not self.devices_connected:
            self.devices_connected = ["None"]
            
        self.device_selection_dropdown = OptionMenu(self.master, self.device_port, *self.devices_connected)
        self.device_selection_dropdown.grid(row=0, column=1, padx=10, pady=10)

    def refresh_details(self):
        if not self.device_port.get():
            self.status_text.set("Status: No device selected")
            self.status.config(bg="red")
            return
            
        try:
            ip, auth_key = get_ip_and_auth_key(self.device_port.get())
            
        except:
            self.status_text.set("Status: Error talking to device")
            self.status.config(bg="red")
            return

        if ip == "0.0.0.0":
            self.ip.set("Not Connected")
        else:
            self.ip.set(ip)
        
        self.auth_key.set(auth_key)
            
        self.status_text.set("Status: Refreshed")
        self.status.config(bg="green")


    def start_refresh_details(self):
        threading.Thread(target=self.refresh_details).start()
        self.status_text.set("Status: Refreshing Details")
        self.status.config(bg="yellow")
     
    def apply_configuration_to_device(self):
        ssid = self.ssid.get()
        password = self.wifi_password.get()
        port = self.device_port.get()

        if not(ssid and password and port):
            self.status_text.set("Status: Parameters not set")
            self.status.config(bg="red")
            return
        
        try:
            is_connected = connect_to_network(ssid, password, port)
            
        except:
            self.status_text.set("Status: Error applying")
            self.status.config(bg="red")
            return

        if is_connected:
            self.status_text.set("Status: Connected")
            self.status.config(bg="green")
            
        elif not is_connected:
            self.status_text.set("Status: Incorrect SSID or Password")
            self.status.config(bg="red")

        elif not is_connected:
            self.status_text.set("Status: Error applying")
            self.status.config(bg="red")


    def start_apply_configuration_to_device(self):
        threading.Thread(target=self.apply_configuration_to_device).start()
        self.status_text.set("Status: Applying to device")
        self.status.config(bg="yellow")
        
root = Tk()
gui = ConverterGUI(root)
root.geometry("355x320")
root.configure(background="white")
root.resizable(0, 0)

icon_directory = __file__.split("/")
icon_directory[-1] = "logo.ico"
icon_directory = "/".join(icon_directory)
root.iconbitmap(icon_directory)

root.mainloop()
