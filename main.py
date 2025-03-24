
## VERSION 2

# import serial
# import pynmea2
# import paho.mqtt.client as mqtt
# import time
# import re
# import json  # Import the json module

# def get_usb_port():
#     """
#     Attempts to automatically detect a USB GPS device.  This is a best-effort
#     implementation and may not work on all systems or with all GPS devices.
#     It prioritizes common patterns (/dev/ttyACM*, /dev/ttyUSB*, COM*)
#     and checks if the device is readable.

#     Returns:
#         str: The port name if a likely GPS device is found, or None otherwise.
#     """
#     import platform
#     import glob

#     system = platform.system()

#     if system == "Linux":
#         patterns = ["/dev/ttyACM*", "/dev/ttyUSB*"]
#     elif system == "Darwin":  # macOS
#         patterns = ["/dev/cu.usbmodem1401"]  #  Add cu devices
#     elif system == "Windows":
#         patterns = ["COM*"]
#     else:
#         print("Unsupported operating system:", system)
#         return None

#     for pattern in patterns:
#         for port in glob.glob(pattern):
#             try:
#                 # Try opening the port at a low baud rate (doesn't matter much here)
#                 with serial.Serial(port, baudrate=4800, timeout=1):
#                     print(f"Found potential GPS device at: {port}")
#                     return port  # Return the first one that works
#             except (serial.SerialException, OSError) as e:
#                 # print(f"Error opening {port}: {e}")  # Optional:  Verbose error
#                 pass  #  Ignore errors and try the next port

#     print("No GPS device found automatically.")
#     return None


# def on_connect(client, userdata, flags, rc):
#     """MQTT connection callback."""
#     if rc == 0:
#         print("Connected to MQTT Broker!")
#         client.subscribe("gps/location")  # Subscribe here!
#     else:
#         print(f"Failed to connect, return code {rc}")


# def parse_nmea_data(nmea_string):
#     """
#     Parses NMEA data and returns a dictionary with relevant information.
#     See previous responses for detailed docstring.
#     """
#     try:
#         msg = pynmea2.parse(nmea_string)
#         data = {}

#         if isinstance(msg, pynmea2.types.talker.RMC):
#             if msg.status == 'A':
#                 data['latitude'] = msg.latitude
#                 data['longitude'] = msg.longitude
#                 data['timestamp'] = msg.datetime.isoformat() if msg.datetime else None
#                 data['speed_over_ground'] = msg.spd_over_grnd * 1.852 if msg.spd_over_grnd else None # Handle None
#         elif isinstance(msg, pynmea2.types.talker.GGA):
#             if msg.gps_qual > 0:
#                 data['latitude'] = msg.latitude
#                 data['longitude'] = msg.longitude
#                 data['altitude'] = msg.altitude
#                 data['altitude_units'] = msg.altitude_units
#                 data['satellites'] = int(msg.num_sats)
#                 data['hdop'] = float(msg.horizontal_dil)
#                 data['fix_quality'] = msg.gps_qual
#                 if 'timestamp' not in data and msg.timestamp:
#                    data['timestamp'] = msg.timestamp.isoformat()

#         elif isinstance(msg, pynmea2.types.talker.GLL):
#               if msg.status == "A":
#                 data['latitude'] = msg.latitude
#                 data['longitude'] = msg.longitude
#                 data['timestamp'] = msg.timestamp.isoformat() if msg.timestamp else None

#         return data

#     except pynmea2.ParseError as e:
#         #print(f"Parse error: {e}") #Less Verbose
#         return {}
#     except Exception as e:
#         print(f"An unexpected error occurred during parsing: {e}")
#         return {}


# def main():
#     """Main function to read GPS data and send to MQTT."""

#     # --- Configuration ---
#     mqtt_broker = "localhost"  # Replace with your MQTT broker address
#     mqtt_port = 1883  # Default MQTT port. Change to 8883 for TLS, or the correct port for your setup
#     mqtt_topic = "gps/location"
#     usb_port = get_usb_port()  # Try automatic detection
#     # usb_port = "/dev/ttyACM0"   #  Or set manually
#     baud_rate = 9600  # Try 9600, 115200 if 4800 doesn't work

#     if usb_port is None:
#         return
#     # --- MQTT Setup ---
#     client = mqtt.Client()
#     client.on_connect = on_connect
#     # --- Add TLS/SSL Support (Optional but Recommended) ---
#     # Uncomment and configure these lines if your broker requires TLS/SSL:
#     # client.tls_set(ca_certs="path/to/ca.crt",  # Path to the CA certificate
#     #                certfile="path/to/client.crt",  # Path to your client certificate
#     #                keyfile="path/to/client.key")  # Path to your client private key
#     # mqtt_port = 8883  # Use port 8883 for MQTT over TLS

#     client.connect(mqtt_broker, mqtt_port, 60)
#     client.loop_start()

#     # --- Serial Port Setup ---
#     try:
#         ser = serial.Serial(usb_port, baud_rate, timeout=1)
#         print(f"Connected to GPS on {usb_port}")
#     except serial.SerialException as e:
#         print(f"Error opening serial port: {e}")
#         return
#     try:
#         while True:
#             try:
#                 line = ser.readline().decode('ascii', errors='replace').strip()
#                 line = re.sub(r'[^\x20-\x7E]', '', line) #remove non-printable character

#                 if line.startswith('$'):
#                     parsed_data = parse_nmea_data(line)
#                     if parsed_data:
#                         print(f"Parsed Data: {parsed_data}")
#                         # --- CRITICAL FIX: Use json.dumps() ---
#                         client.publish(mqtt_topic, json.dumps(parsed_data))

#             except UnicodeDecodeError:
#                 pass
#             except Exception as e:
#                 print(f"Error reading/processing data: {e}")
#                 time.sleep(1)

#     except KeyboardInterrupt:
#         print("Exiting...")
#     finally:
#         ser.close()
#         client.loop_stop()
#         client.disconnect()
#         print("Disconnected from MQTT Broker and Serial Port.")



# if __name__ == "__main__":
#     main()


## UPDATE SQL DATABASE WITH GPS DATA

import serial
import pynmea2
import paho.mqtt.client as mqtt
import time
import re
import json
import mysql.connector  # For MySQL interaction
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

def get_usb_port():
    """
    (Same as before, detects USB port)
    """
    import platform
    import glob

    system = platform.system()

    if system == "Linux":
        patterns = ["/dev/ttyACM*", "/dev/ttyUSB*"]
    elif system == "Darwin":
        patterns = ["/dev/tty.usbmodem1401"]
    elif system == "Windows":
        patterns = ["COM*"]
    else:
        print("Unsupported operating system:", system)
        return None

    for pattern in patterns:
        for port in glob.glob(pattern):
            try:
                with serial.Serial(port, baudrate=9600, timeout=1):
                    print(f"Found potential GPS device at: {port}")
                    return port
            except (serial.SerialException, OSError) as e:
                pass

    print("No GPS device found automatically.")
    return None

def on_connect(client, userdata, flags, rc):
    """MQTT connection callback."""
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe("gps/location")  # Subscribe here!
    else:
        print(f"Failed to connect, return code {rc}")


def parse_nmea_data(nmea_string):
    """
    (Same as before, parses NMEA data)
    """
    try:
        msg = pynmea2.parse(nmea_string)
        data = {}

        if isinstance(msg, pynmea2.types.talker.RMC):
            if msg.status == 'A':
                data['latitude'] = msg.latitude
                data['longitude'] = msg.longitude
                data['timestamp'] = msg.datetime.isoformat() if msg.datetime else None
                data['speed_over_ground'] = msg.spd_over_grnd * 1.852 if msg.spd_over_grnd else None # Handle None
        elif isinstance(msg, pynmea2.types.talker.GGA):
            if msg.gps_qual > 0:
                data['latitude'] = msg.latitude
                data['longitude'] = msg.longitude
                data['altitude'] = msg.altitude
                data['altitude_units'] = msg.altitude_units
                data['satellites'] = int(msg.num_sats)
                data['hdop'] = float(msg.horizontal_dil)
                data['fix_quality'] = msg.gps_qual
                if 'timestamp' not in data and msg.timestamp:
                   data['timestamp'] = msg.timestamp.isoformat()

        elif isinstance(msg, pynmea2.types.talker.GLL):
              if msg.status == "A":
                data['latitude'] = msg.latitude
                data['longitude'] = msg.longitude
                data['timestamp'] = msg.timestamp.isoformat() if msg.timestamp else None

        return data

    except pynmea2.ParseError as e:
        #print(f"Parse error: {e}") #Less Verbose
        return {}
    except Exception as e:
        print(f"An unexpected error occurred during parsing: {e}")
        return {}

def update_mysql(center_id, latitude, longitude):
    """
    Updates the Latitude and Longitude in the MySQL database for a given Center_ID.

    Args:
        center_id (int): The Center_ID to update.
        latitude (float): The new latitude value.
        longitude (float): The new longitude value.
    """
    try:
        # --- Database Connection Details ---
        db_config = {
            "host": "172.16.116.110",  # Replace with your MySQL server address
            "port": "3306",  # Default MySQL port
            "user": "root",  # Replace with your MySQL username
            "password": "1234",  # Replace with your MySQL password
            "database": "stationdb",  # The name of your database
        }

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Use parameterized query to prevent SQL injection
        sql = "UPDATE CenterBase SET Latitude = %s, Longitude = %s WHERE Center_ID = %s"
        values = (latitude, longitude, center_id)

        cursor.execute(sql, values)
        connection.commit()  # Important: Commit the changes!
        print(f"Updated database for Center_ID {center_id}: Lat={latitude}, Lon={longitude}")

    except mysql.connector.Error as err:
        print(f"Error updating database: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed.")

def get_center_ids():
    """
    Retrieves all Center_IDs from the database for the dropdown menu.
    
    Returns:
        list: List of Center_IDs
    """
    try:
        db_config = {
            "host": "172.16.116.110",
            "port": "3306",
            "user": "root",
            "password": "1234",
            "database": "stationdb",
        }

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        cursor.execute("SELECT Center_ID FROM CenterBase ORDER BY Center_ID")
        center_ids = [str(row[0]) for row in cursor.fetchall()]
        
        return center_ids
    except mysql.connector.Error as err:
        print(f"Error retrieving Center_IDs: {err}")
        return ["1", "2", "3"]  # Default values in case of error
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

class GPSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GPS Data Logger")
        self.root.geometry("500x400")
        
        self.center_id = tk.StringVar(value="2")  # Default value
        self.update_interval = tk.IntVar(value=60)  # Default 60 seconds
        self.status_var = tk.StringVar(value="Ready")
        self.gps_data_var = tk.StringVar(value="No GPS data")
        self.use_mqtt = tk.BooleanVar(value=False)  # Default: MQTT disabled
        
        self.create_widgets()
        
        # GPS processing variables
        self.running = False
        self.client = None
        self.ser = None
        
        # Auto-start with Center ID 2
        self.root.after(1000, self.auto_start)
    
    def auto_start(self):
        """Automatically start GPS logging with Center ID 2"""
        self.center_id.set("2")
        self.start_gps()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Center ID selection
        ttk.Label(main_frame, text="Select Center ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Try to get center IDs from database, or use defaults
        try:
            center_ids = get_center_ids()
        except:
            center_ids = ["1", "2", "3"]
            
        center_combo = ttk.Combobox(main_frame, textvariable=self.center_id, values=center_ids)
        center_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Update interval
        ttk.Label(main_frame, text="Update Interval (seconds):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.update_interval, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # MQTT toggle
        ttk.Checkbutton(main_frame, text="Enable MQTT", variable=self.use_mqtt).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Start", command=self.start_gps).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Stop", command=self.stop_gps).pack(side=tk.LEFT, padx=5)
        
        # Status display
        status_frame = ttk.LabelFrame(main_frame, text="Status")
        status_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        ttk.Label(status_frame, textvariable=self.status_var).pack(pady=5)
        
        # GPS data display
        gps_frame = ttk.LabelFrame(main_frame, text="GPS Data")
        gps_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        self.gps_text = tk.Text(gps_frame, height=10, width=50)
        self.gps_text.pack(pady=5)
        
    def start_gps(self):
        if self.running:
            messagebox.showinfo("Already Running", "GPS logging is already running.")
            return
            
        try:
            center_id = int(self.center_id.get())
            update_interval = self.update_interval.get()
            
            if update_interval < 1:
                messagebox.showerror("Invalid Interval", "Update interval must be at least 1 second.")
                return
                
            self.status_var.set("Starting GPS logging...")
            
            # Start GPS processing in a separate thread
            import threading
            self.running = True
            self.gps_thread = threading.Thread(target=self.gps_process, args=(center_id, update_interval))
            self.gps_thread.daemon = True
            self.gps_thread.start()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values.")
    
    def stop_gps(self):
        if not self.running:
            messagebox.showinfo("Not Running", "GPS logging is not currently running.")
            return
            
        self.running = False
        self.status_var.set("Stopping GPS logging...")
        
        # Clean up resources
        if self.ser:
            self.ser.close()
            
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            
        self.status_var.set("GPS logging stopped.")
    
    def update_gps_display(self, data_str):
        # Update the GPS data display in the GUI thread
        self.root.after(0, lambda: self.gps_text.insert(tk.END, data_str + "\n"))
        self.root.after(0, lambda: self.gps_text.see(tk.END))
        
    def gps_process(self, center_id, update_interval):
        """Main function to read GPS data, send to MQTT, and update MySQL."""
        # --- Configuration ---
        mqtt_broker = "127.0.0.1"  # Replace with your MQTT broker address
        mqtt_port = 1883  # or 8883 for TLS
        mqtt_topic = "gps/location"
        usb_port = get_usb_port()
        baud_rate = 9600 # or 9600, 115200
        
        if usb_port is None:
            self.status_var.set("No GPS device found!")
            self.running = False
            return

        # --- MQTT Setup (only if enabled) ---
        if self.use_mqtt.get():
            try:
                self.client = mqtt.Client()
                self.client.on_connect = on_connect
                self.client.connect(mqtt_broker, mqtt_port, 60)
                self.client.loop_start()
                self.status_var.set("MQTT connected and GPS ready")
            except Exception as e:
                self.status_var.set(f"MQTT connection error: {e}, continuing without MQTT")
                self.client = None
        else:
            self.client = None
            self.status_var.set("Running without MQTT")

        # --- Serial Port Setup ---
        try:
            self.ser = serial.Serial(usb_port, baud_rate, timeout=1)
            self.status_var.set(f"Connected to GPS on {usb_port}")
        except serial.SerialException as e:
            self.status_var.set(f"Error opening serial port: {e}")
            self.running = False
            return

        last_update_time = datetime.now() - timedelta(seconds=update_interval) # Initialize

        try:
            while self.running:
                try:
                    line = self.ser.readline().decode('ascii', errors='replace').strip()
                    line = re.sub(r'[^\x20-\x7E]', '', line)

                    if line.startswith('$'):
                        parsed_data = parse_nmea_data(line)
                        if parsed_data:
                            data_str = f"Lat: {parsed_data.get('latitude', 'N/A')}, Lon: {parsed_data.get('longitude', 'N/A')}"
                            self.update_gps_display(data_str)
                            
                            # Publish to MQTT only if enabled and connected
                            if self.client and self.use_mqtt.get():
                                self.client.publish(mqtt_topic, json.dumps(parsed_data))

                            # --- MySQL Update Logic ---
                            now = datetime.now()
                            if now - last_update_time >= timedelta(seconds=update_interval):
                                if 'latitude' in parsed_data and 'longitude' in parsed_data:
                                    update_mysql(center_id, parsed_data['latitude'], parsed_data['longitude'])
                                    last_update_time = now #Reset Timer
                                    self.status_var.set(f"Updated database at {now.strftime('%H:%M:%S')}")
                                else:
                                    self.status_var.set("No valid lat/lon data for database update.")

                except UnicodeDecodeError:
                    pass
                except Exception as e:
                    self.status_var.set(f"Error: {e}")
                    time.sleep(1)
        finally:
            if self.ser:
                self.ser.close()
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            self.status_var.set("Disconnected")
            self.running = False       

def main():
    """Launch the GPS application."""
    root = tk.Tk()
    app = GPSApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()