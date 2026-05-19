import hid
import time
import pymysql
import os
import socket
import threading
from dotenv import load_dotenv

load_dotenv()

# Hardcoded USB hardware IDs
USB_VID = 0x04D8
USB_PID = 0x033F

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD") or "",
        database=os.getenv("DB_NAME"),
        autocommit=True
    )

def log_tag(epc_string, room_name, asset_status, scanner_name):
    print(f"\n>>> [{scanner_name}] PROCESSING TAG: {epc_string} -> Moved to {room_name} ({asset_status})")
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(
            "INSERT INTO scan_logs (epc, room) VALUES (%s, %s)", 
            (epc_string, room_name)
        )
        
        upsert_query = """
            INSERT INTO assets (epc, status, room, last_seen) 
            VALUES (%s, %s, %s, NOW()) 
            ON DUPLICATE KEY UPDATE status = VALUES(status);
        """
        cursor.execute(upsert_query, (epc_string, asset_status, room_name))
        
        db.close()
        print(f">>> [{scanner_name}] Database Updated Successfully.")
        
    except Exception as e:
        print(f">>> [{scanner_name}] DB ERROR: {e}")

# --- THE UNIVERSAL SCANNER THREAD WORKER ---
# Notice we added 'usb_path' as an argument here
def scanner_listener(scanner_name, mode, ip, port, usb_path, room_name, assigned_status):
    print(f">>> [{scanner_name}] Initializing {mode} connection (Zone: {room_name})...")
    
    tcp_client = None
    usb_device = None
    
    try:
        if mode == "WIFI":
            tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_client.settimeout(5.0)
            tcp_client.connect((ip, port))
            tcp_client.setblocking(False)
            print(f">>> [OK] [{scanner_name}] WIFI ONLINE ({ip}:{port})")
            
        elif mode == "USB":
            usb_device = hid.device()
            # We open by PATH now, ensuring we get a specific physical device
            usb_device.open_path(usb_path)
            usb_device.set_nonblocking(1)
            print(f">>> [OK] [{scanner_name}] USB ONLINE (Port: {usb_path.decode('utf-8')[:20]}...)")
            
        else:
            print(f">>> [FAIL] [{scanner_name}] Unknown connection mode: {mode}")
            return
            
    except Exception as e:
        print(f">>> [FAIL] [{scanner_name}] CONNECTION FAILED: {e}")
        return

    recent_tags = {}

    try:
        while True:
            hex_str = ""
            
            try:
                if mode == "WIFI":
                    data = tcp_client.recv(1024)
                    if data:
                        hex_str = data.hex().upper()
                elif mode == "USB":
                    data = usb_device.read(64)
                    if data:
                        hex_str = bytes(data).hex().upper()

            except BlockingIOError:
                pass 
            except Exception as e:
                print(f"\n>>> [ERROR] [{scanner_name}] IO ERROR: {e}")
                break

            # Parse the Hex Protocol
            if hex_str:
                if "CCFFFF20" in hex_str:
                    idx = hex_str.find("CCFFFF20")
                    if idx != -1 and len(hex_str) >= idx + 42: 
                        epc_start = idx + 18
                        epc_code = hex_str[epc_start:epc_start+24]
                        
                        current_time = time.time()
                        if epc_code not in recent_tags or (current_time - recent_tags[epc_code]) > 3:
                            log_tag(epc_code, room_name, assigned_status, scanner_name)
                            recent_tags[epc_code] = current_time
                            
            time.sleep(0.05) 
            
    finally:
        if tcp_client: tcp_client.close()
        if usb_device: usb_device.close()


# --- MAIN EXECUTION ---
print("--- DUAL-SCANNER TRACKER ONLINE ---")

# 1. Enumerate all connected identical USB scanners
connected_usb_devices = hid.enumerate(USB_VID, USB_PID)
usb_paths = [dev['path'] for dev in connected_usb_devices]
usb_assignment_index = 0

print(f">>> Found {len(usb_paths)} USB scanner(s) attached to this machine.")

threads = []

# --- 2. Configure Scanner 1 (Inside) ---
MODE_IN = os.getenv("READER_IN_MODE", "NONE").upper()
if MODE_IN in ["WIFI", "USB"]:
    IP_IN = os.getenv("READER_IN_IP", "0.0.0.0")
    PORT_IN = int(os.getenv("READER_IN_PORT", 49152))
    ROOM_IN = os.getenv("READER_IN_ROOM", "Inside")
    
    assigned_path = b''
    if MODE_IN == "USB":
        if usb_assignment_index < len(usb_paths):
            assigned_path = usb_paths[usb_assignment_index]
            usb_assignment_index += 1
        else:
            print(">>> [FAIL] [SCANNER_IN] Not enough USB scanners plugged in!")
            MODE_IN = "FAILED"
            
    if MODE_IN != "FAILED":
        t1 = threading.Thread(target=scanner_listener, args=("SCANNER_IN", MODE_IN, IP_IN, PORT_IN, assigned_path, ROOM_IN, "PRESENT"))
        t1.daemon = True
        threads.append(t1)
        t1.start()
else:
    print(">>> [SCANNER_IN] Set to NONE. Disabled.")

# --- 3. Configure Scanner 2 (Outside) ---
MODE_OUT = os.getenv("READER_OUT_MODE", "NONE").upper()
if MODE_OUT in ["WIFI", "USB"]:
    IP_OUT = os.getenv("READER_OUT_IP", "0.0.0.0")
    PORT_OUT = int(os.getenv("READER_OUT_PORT", 49152))
    ROOM_OUT = os.getenv("READER_OUT_ROOM", "Hallway")
    
    assigned_path = b''
    if MODE_OUT == "USB":
        if usb_assignment_index < len(usb_paths):
            assigned_path = usb_paths[usb_assignment_index]
            usb_assignment_index += 1
        else:
            print(">>> [FAIL] [SCANNER_OUT] Not enough USB scanners plugged in!")
            MODE_OUT = "FAILED"

    if MODE_OUT != "FAILED":
        t2 = threading.Thread(target=scanner_listener, args=("SCANNER_OUT", MODE_OUT, IP_OUT, PORT_OUT, assigned_path, ROOM_OUT, "MISSING"))
        t2.daemon = True
        threads.append(t2)
        t2.start()
else:
    print(">>> [SCANNER_OUT] Set to NONE. Disabled.")

try:
    if not threads:
        print(">>> ⚠️ WARNING: Both scanners are disabled or failed to load. Exiting...")
        exit()
        
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n>>> Shutting down tracking threads...")