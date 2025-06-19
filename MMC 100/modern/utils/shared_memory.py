import ctypes
from multiprocessing import shared_memory, Process
from time import monotonic

from modern.config.stage_position import StagePosition, StagePositionStruct

"""
Helper functions to share stage position memory w the manager
"""

def create_shared_stage_position() ->  tuple[shared_memory.SharedMemory, StagePositionStruct]:
    """
    Create shared-memory block

    TODO:
        Add functionality to support multiple stages "factory" style
    """
    # Create shared mem
    size = ctypes.sizeof(StagePositionStruct)
    shm = shared_memory.SharedMemory(name="stage_position",create=True,size=size)

    # Map shm to struct instance
    view = StagePositionStruct.from_buffer(shm.buf)
    view.__init__()
    return shm, view

def open_shared_stage_position(name: str = "stage_position") -> tuple[shared_memory.SharedMemory, StagePositionStruct]:
    """
    Attach to an existing shared mem block, to be used in child processes or GUI
    """
    shm = shared_memory.SharedMemory(name=name)
    view = StagePositionStruct.from_buffer(shm.buf)
    return shm, view

def safe_shm_shutdown(shm: shared_memory.SharedMemory) -> None:
    shm.close()
    shm.unlink()
