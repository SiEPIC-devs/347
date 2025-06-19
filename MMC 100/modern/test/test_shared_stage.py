from multiprocessing import Process
from time import sleep, monotonic

from modern.config.stage_position import *
from modern.utils.shared_memory import *

from modern.hal.motors_hal import AxisType

def writer():
    shm, raw = open_shared_stage_position()
    sp = StagePosition(shared_struct=raw)
    # write into shared memory
    sp.set_positions(AxisType.X, 123.456)
    sp.set_homed(AxisType.X)
    print(f"[Writer] Wrote: X={sp.x.position:.3f}, Homed={sp.x.is_homed}")
    
    # Clean
    del sp
    del raw
    shm.close()

def reader():
    # give writer a moment
    sleep(0.1)
    shm, raw = open_shared_stage_position("stage_position")
    sp = StagePosition(shared_struct=raw)
    print(f"[Reader] Reads: X={sp.x.position:.3f}, Homed={sp.x.is_homed}")
    
    # Clean
    del sp
    del raw
    shm.close()

if __name__ == "__main__":
    # 1) Create
    shm, raw = create_shared_stage_position()
    sp = StagePosition(shared_struct=raw)
    print(f"[Main] Initial X={sp.x.position}, Homed={sp.x.is_homed}")

    # 2) Spawn writer
    pw = Process(target=writer)
    pw.start()
    pw.join()

    # 3) Spawn reader
    pr = Process(target=reader)
    pr.start()
    pr.join()

    # 4) Cleanup
    del sp
    del raw
    safe_shm_shutdown(shm)
    print("[Main] Shared memory unlinked. Test complete.")