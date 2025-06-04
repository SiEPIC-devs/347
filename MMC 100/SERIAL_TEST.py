import asyncio
import time

from motor_stage_manager_w_debug import StageManager, StageConfiguration
from motors_hal import AxisType, MotorEvent, MotorEventType

# 1) Define a simple event callback that just prints everything it sees
def print_event(event: MotorEvent):
    # event.axis -> which axis (AxisType.X, etc.)
    # event.event_type -> which kind (MOVE_STARTED, MOVE_COMPLETE, etc.)
    # event.data -> dictionary of details (target_position, success flag, etc.)
    timestamp = event.timestamp
    axis = event.axis.name
    evtype = event.event_type.name
    details = event.data
    print(f"[{timestamp:.3f}] {axis} -> {evtype} -> {details}")

async def demo():
    # 2) Build a config & the manager
    cfg = StageConfiguration(
        com_port="COM3",       # or "/dev/ttyUSB0" on Linux
        baudrate=38400,
        timeout=0.3,
        # (all other fields use their defaults)
    )
    mgr = StageManager(cfg)

    # 3) Register our print_event handler
    mgr.add_event_callback(print_event)

    # 4) Initialize just the X axis
    print(">>> Initializing X …")
    ok = await mgr.initialize([AxisType.X])
    print("Initialized X:", ok)
    if not ok:
        print("Cannot continue without a successful initialization.")
        await mgr.disconnect()
        return

    # 5) Home X (negative limit)
    print("\n>>> Homing X …")
    homed = await mgr.home_axis(AxisType.X, direction=0)
    print("Home X returned:", homed)

    # 6) Move X to +1000 μm (absolute)
    print("\n>>> Moving X to 1000 μm (absolute) …")
    moved = await mgr.move_single_axis(
        AxisType.X,
        position=1000.0,
        relative=False,
        velocity=None,         # use default from config
        wait_for_completion=True
    )
    print("move_single_axis returned:", moved)

    # 7) Now start a long relative move (e.g. +5000 μm), then stop halfway
    print("\n>>> Starting a 5000 μm relative move on X …")
    long_move = asyncio.create_task(
        mgr.move_single_axis(AxisType.X, position=5000.0, relative=True, wait_for_completion=True)
    )
    # Wait 0.2 s, then stop
    await asyncio.sleep(0.2)
    print(">>> Calling stop_axis(X) …")
    stopped = await mgr.stop_axis(AxisType.X)
    print("stop_axis returned:", stopped)

    # Wait for the long move task to finish/cleanup
    await long_move

    # 8) Ask for X’s current position
    print("\n>>> Querying X’s position …")
    pos_obj = await mgr.get_position(AxisType.X)
    if pos_obj:
        print(f"X actual = {pos_obj.actual:.2f} μm (theoretical = {pos_obj.theoretical:.2f} μm)")
    else:
        print("Could not read X position.")

    # 9) Disconnect everything
    print("\n>>> Disconnecting …")
    await mgr.disconnect()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(demo())
