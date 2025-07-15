#!/usr/bin/env python3
"""
Simple smoke-test suite for SRSManager.
Requires your LDC device to be connected.
"""

import sys
import time

# Adjust these imports if your package structure differs
from LDC.config.ldc_config import LDCConfiguration
from LDC.ldc_manager import SRSManager

def reset_manager():
    """
    Instantiate a fresh manager with the default profile config.
    """
    default_cfg = LDCConfiguration()             # uses built‑in defaults
    manager = SRSManager(default_cfg, create_shm=True)
    return manager

def test_initialize_and_connect():
    m = reset_manager()
    print("→ initialize()", m.initialize())
    connected = m.connect()
    print("→ connect() returned", connected)
    print("→ is_connected()", m.is_connected())
    print("→ disconnect()", m.disconnect())
    print("→ is_connected() after disconnect", m.is_connected())
    print("-" * 60)

def test_sensor_type():
    m = reset_manager()
    m.initialize(); m.connect()
    cfg = m.get_config()
    orig = cfg.get("sensor_type")
    print("original sensor_type:", orig)

    alt = "thermocouple" if orig != "thermocouple" else "thermistor"
    print(f"→ set_sensor_type({alt})", m.set_sensor_type(alt))
    print("now sensor_type:", m.get_config().get("sensor_type"))

    # restore
    print(f"→ reset to {orig}", m.set_sensor_type(orig))
    print("restored sensor_type:", m.get_config().get("sensor_type"))
    m.disconnect()
    print("-" * 60)

def test_sensor_coeffs():
    m = reset_manager()
    m.initialize(); m.connect()
    cfg = m.get_config()
    orig = cfg.get("model_coeffs", [0.0,0.0,0.0])
    print("original model_coeffs:", orig)

    new = [c + 0.1 for c in orig]
    print(f"→ configure_sensor_coeffs({new})", m.configure_sensor_coeffs(new))
    print("now model_coeffs:", m.get_config().get("model_coeffs"))

    # restore
    print(f"→ reset to {orig}", m.configure_sensor_coeffs(orig))
    print("restored model_coeffs:", m.get_config().get("model_coeffs"))
    m.disconnect()
    print("-" * 60)

def test_pid_coeffs():
    m = reset_manager()
    m.initialize(); m.connect()
    cfg = m.get_config()
    orig = cfg.get("pid_coeffs", [0.0,0.0,0.0])
    print("original pid_coeffs:", orig)

    new = [p + 1.0 for p in orig]
    print(f"→ configure_PID_coeffs({new})", m.configure_PID_coeffs(new))
    print("now pid_coeffs:", m.get_config().get("pid_coeffs"))

    # restore
    print(f"→ reset to {orig}", m.configure_PID_coeffs(orig))
    print("restored pid_coeffs:", m.get_config().get("pid_coeffs"))
    m.disconnect()
    print("-" * 60)

def test_tec_and_temperature():
    m = reset_manager()
    m.initialize(); m.connect()

    print("→ tec_status() initially:", m.tec_status())
    print("→ tec_on()",  m.tec_on())
    print("→ tec_status() after on:", m.tec_status())
    print("→ tec_off()", m.tec_off())
    print("→ tec_status() after off:", m.tec_status())

    cur_temp = m.get_temp()
    setp = m.get_temp_setpoint()
    print("→ get_temp():", cur_temp)
    print("→ get_temp_setpoint():", setp)

    # bump setpoint by +1.0, then restore
    print("→ set_temp()", m.set_temp(setp + 1.0))
    time.sleep(0.1)  # small pause
    print("  now setpoint:", m.get_temp_setpoint())
    print("→ restore set_temp()", m.set_temp(setp))
    print("  restored setpoint:", m.get_temp_setpoint())

    m.disconnect()
    print("-" * 60)

def test_event_callbacks():
    m = reset_manager()
    called = {"count": 0}
    def cb(event):
        called["count"] += 1
        print("  callback got event:", event)

    print("→ add_event_callback(cb)")
    m.add_event_callback(cb)
    print("→ _handle_stage_event('EV1')")
    m._handle_stage_event("EV1")
    print("  called count:", called["count"])

    print("→ remove_event_callback(cb)")
    m.remove_event_callback(cb)
    called["count"] = 0
    m._handle_stage_event("EV2")
    print("  called count after removal:", called["count"])
    print("-" * 60)

def test_get_device_info():
    m = reset_manager()
    print("→ get_device_info() before connect:", m.get_device_info())

    m.initialize(); m.connect()
    print("→ get_device_info() after connect:", m.get_device_info())
    m.disconnect()
    print("-" * 60)

if __name__ == "__main__":
    print("\nTEST: initialize & connect/disconnect")
    test_initialize_and_connect()

    print("\nTEST: sensor type setter + reset")
    test_sensor_type()

    print("\nTEST: sensor coefficients setter + reset")
    test_sensor_coeffs()

    print("\nTEST: PID coefficients setter + reset")
    test_pid_coeffs()

    print("\nTEST: TEC control & temperature getters/setters")
    test_tec_and_temperature()

    print("\nTEST: event callback registration/removal")
    test_event_callbacks()

    print("\nTEST: device info summary")
    test_get_device_info()

    print("\nAll done.")
