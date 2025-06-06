import asyncio
import time

from motor_stage_manager_w_debug import StageManager, StageConfiguration
from motors_hal import AxisType, MotorEvent, MotorEventType

# Define a simple event callback that just prints everything it sees
def print_event(event: MotorEvent):
    # event.axis -> which axis (AxisType.X, etc.)
    # event.event_type -> which kind (MOVE_STARTED, MOVE_COMPLETE, etc.)
    # event.data -> dictionary of details (target_position, success flag, etc.)
    timestamp = event.timestamp
    axis = event.axis.name
    evtype = event.event_type.name
    details = event.data
    print(f"<<< [{timestamp:.3f}] {axis} -> {evtype} -> {details} \n")

async def demo():
    # 2) Build a config & the manager
    cfg = StageConfiguration(
        com_port="/dev/ttyUSB0",       
        baudrate=38400,
        timeout=0.3,
        # (all other fields use their defaults)
    )
    mgr = StageManager(cfg)

    # Add event handler
    mgr.add_event_callback(print_event)

    # Initialize just the X axis
    x = AxisType.X
    y = AxisType.Y
    z = AxisType.Z
    fr = AxisType.ROTATION_FIBER
    cp = AxisType.ROTATION_CHIP
    
    print(f"x: {x}") # sanity check

    print(">>> Initializing X …")
    ok = await mgr.initialize(axes=[x])
    if not ok:
        print(f"init failed")
        await mgr.disconnect_all()
    print(f"Initialized X: {ok}")

    await asyncio.sleep(3)

    # Register our print_event handler
    # mgr.motors[x].add_event_callback(print_event) # todo: Hmm weird syntax way of doing it

    # Home X (positive limit)
    print("\n>>> Homing X pos…")
    homed = await mgr.home_axis(x, direction=1)
    done = await mgr.wait_for_home_completion(x)
    print(f"Home X returned: {homed} status: {done}")
    

    # Home X (negative limit)
    print("\n>>> Homing X neg…")
    homed = await mgr.home_axis(x, direction=0)
    done = await mgr.wait_for_home_completion(x)
    print(f"Home X returned: {homed} status: {done}")
    

    # # Move X to 0 um (absolute)
    # print("\n>>> Moving X to 0 um (absolute) …")
    # moved = await mgr.move_single_axis(
    #     x,
    #     position=0.0,
    #     relative=False,
    #     velocity=None,         # use default from config
    #     wait_for_completion=True
    # )
    # print("move_single_axis returned:", moved)

    # await asyncio.sleep(1)
 

    # # Ask for X’s current position
    # print("\n>>> Querying X’s position …")
    # pos_obj = await mgr.get_position(x)
    # if pos_obj:
    #     print(f"X actual = {pos_obj.actual:.2f} um (theoretical = {pos_obj.theoretical:.2f} um)")
    # else:
    #     print("Could not read X position.")

    # 9) Disconnect everything
    print("\n>>> Disconnecting …")
    await mgr.disconnect_all()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(demo())
