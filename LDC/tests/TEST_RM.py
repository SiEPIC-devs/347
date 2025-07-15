import pyvisa
import time

# Connect to Prologix GPIB-USB Controller
rm = pyvisa.ResourceManager('@py')
print("Available resources:", rm.list_resources())

# Note: The manual states that serial port parameters don't matter for the VCP driver
# but let's use common settings. Most importantly, we need the correct command protocol.
prologix = rm.open_resource(
    'ASRL5::INSTR',
    baud_rate=9600,  # Manual says this doesn't matter, but 9600 is common
    timeout=5000,
    write_termination='\n',  # Commands must be terminated with CR or LF
    read_termination='\n',
)

def setup_prologix_controller(addr=1):
    """Configure the Prologix controller for instrument communication"""
    print(f"Configuring Prologix for GPIB address {addr}...")
    
    # Set to controller mode (1 = CONTROLLER, 0 = DEVICE)
    prologix.write('++mode 1')
    time.sleep(0.1)
    
    # Set GPIB address of the instrument
    prologix.write(f'++addr {addr}')
    time.sleep(0.1)
    
    # Enable read-after-write (auto mode)
    # This makes the controller automatically read responses after sending commands
    prologix.write('++auto 1')
    time.sleep(0.1)
    
    # Enable EOI assertion with last character
    prologix.write('++eoi 1')
    time.sleep(0.1)
    
    # Set GPIB termination characters (0 = CR+LF, 1 = CR, 2 = LF, 3 = None)
    prologix.write('++eos 0')  # Try CR+LF first
    time.sleep(0.1)
    
    # Set read timeout to 3 seconds
    prologix.write('++read_tmo_ms 3000')
    time.sleep(0.1)
    
    print("Prologix controller configured")

def test_prologix_connection():
    """Test if we can communicate with the Prologix controller itself"""
    try:
        prologix.write('++ver')
        time.sleep(0.2)
        version = prologix.read()
        print(f"Prologix version: {version}")
        return True
    except Exception as e:
        print(f"Cannot communicate with Prologix controller: {e}")
        return False

def scan_gpib_addresses():
    """Scan for GPIB devices on the bus"""
    print("\nScanning GPIB addresses...")
    found_devices = []
    addr = 2
    try:
        setup_prologix_controller(addr)
        prologix.write('*IDN?')
        time.sleep(0.5)
        response = prologix.read()
        print(f"Address {addr}: {response.strip()}")
        found_devices.append((addr, response.strip()))
    except Exception:
        print(f"Address {addr}: No response")
    
    return found_devices

def communicate_with_ldc502(gpib_addr=1):
    """Communicate with SRS LDC502 at specified GPIB address"""
    try:
        setup_prologix_controller(gpib_addr)
        
        # Test basic communication
        print(f"\nTesting LDC502 at address {gpib_addr}...")
        
        # Query instrument identification
        prologix.write('*IDN?')
        time.sleep(0.5)
        idn_response = prologix.read()
        print(f"IDN → {idn_response}")
        
        # Put instrument in remote mode
        prologix.write('REM 1')
        time.sleep(0.1)
        
        # Query temperature
        prologix.write('TTRD?')
        time.sleep(0.5)
        temp_response = prologix.read()
        print(f"Temp → {temp_response}")
        
        return True
        
    except Exception as e:
        print(f'Error communicating with LDC502: {e}')
        return False

# Main execution
try:
    # First, test if we can talk to the Prologix controller
    if test_prologix_connection():
        print("✓ Prologix controller communication OK")
        
        # Check if instrument is at default address 1
        if communicate_with_ldc502(gpib_addr=1):
            print("✓ Found LDC502 at address 1")
        else:
            print("✗ LDC502 not found at address 1, scanning...")
            devices = scan_gpib_addresses()
            
            if devices:
                print(f"\nFound {len(devices)} device(s):")
                for addr, response in devices:
                    print(f"  Address {addr}: {response}")
            else:
                print("No GPIB devices found")
                print("\nTroubleshooting tips:")
                print("1. Check GPIB address setting on LDC502 rear panel")
                print("2. Verify GPIB cable connections")
                print("3. Check if instrument is powered on")
                print("4. Try different EOS settings (++eos 1, ++eos 2, ++eos 3)")
    else:
        print("✗ Cannot communicate with Prologix controller")
        print("Check USB connection and drivers")

except Exception as e:
    print(f'Setup error: {e}')
    
finally:
    try:
        prologix.close()
        print("Connection closed")
    except:
        pass