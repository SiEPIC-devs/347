import pyvisa
import time

rm = pyvisa.ResourceManager()

inst = rm.open_resource(
    'ASRL5::INSTR',
    baud_rate=9600,  # Manual says this doesn't matter, but 9600 is common
    timeout=5000,
    write_termination='\n',  # Commands must be terminated with CR or LF
    read_termination='\n',
)

inst.write('++mode 1')
time.sleep(0.1)
inst.write(f'++addr {2}')
time.sleep(0.1)
# Enable read-after-write (auto mode)
# This makes the controller automatically read responses after sending commands
inst.write('++auto 1')
time.sleep(0.1)

# Enable EOI assertion with last character
inst.write('++eoi 1')
time.sleep(0.1)

# Set GPIB termination characters (0 = CR+LF, 1 = CR, 2 = LF, 3 = None)
inst.write('++eos 0')  # Try CR+LF first
time.sleep(0.1)

# Set read timeout to 3 seconds
inst.write('++read_tmo_ms 3000')
time.sleep(0.1)

inst.write('*IDN?')
resp = inst.read()

print(f'AHHHH: {resp.strip()}')

resp2 = inst.query('TTRD?')
print(f'RESP2: {resp2.strip()}')

inst.write("TEON 1")

# inst.write("TEON 1")
inst.write("TEON?")
time.sleep(0.3)
resp3 = inst.read()
print(resp3.strip())

inst.write("TMDN 1")
time.sleep(0.1)