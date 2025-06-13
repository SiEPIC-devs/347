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

    all = [x,y,z,fr,cp] # all
    
    print(f"x: {x}") # sanity check

    print(">>> Initializing axis …")
    ok = await mgr.initialize(axes=all)
    if not ok:
        print(f"init failed")
        await mgr.disconnect_all()
    print(f"Initialized X: {ok}")

    async def home_all():
        home_x = await mgr.home_limits(x)
        if home_x:
            print(f"x lims: {mgr.config.position_limits[x]}")
        else:
            print("x failed to home")
            
        home_y = await mgr.home_limits(y)
        if home_y:
            print(f"y lims: {mgr.config.position_limits[y]}")
        else:
            print("y failed to home")

        home_z = await mgr.home_limits(z)
        if home_z:
            print(f"z lims: {mgr.config.position_limits[z]}")
        else:
            print("z failed to home")

        
        home_fr = await mgr.home_limits(fr)
        if home_fr:
            print(f"fr lims: {mgr.config.position_limits[fr]}")
        else:
            print("fr failed to home")

        home_cp = await mgr.home_limits(cp)
        if home_cp:
            print(f"fr lims: {mgr.config.position_limits[cp]}")
        else:
            print("fr failed to home")

    await home_all()

    # Print limits
    # for axis in all:
    #     print(f"{axis} limits: {mgr.config.position_limits[axis]}")
    
    # await mgr.load_params()

    x, y = await mgr.move_xy((5000,-5000), wait_for_completion=True)
    if x and y:
        print(f"success xy: {x} {y}")
    else:
        print(f"error {x} {y}")
   
    await mgr.get_all_positions()

    # disc all
    print("\n>>> Disconnecting …")
    await mgr.disconnect_all()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(demo())
