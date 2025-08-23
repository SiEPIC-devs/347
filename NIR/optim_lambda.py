import ctypes
import numpy as np
import pyvisa
import pandas as pd
from ctypes import c_double, c_int32, c_uint32, c_char, c_char_p, POINTER, byref, create_string_buffer  # <<< added c_char, create_string_buffer
from tqdm import tqdm
import time


import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
pyvisa_logger = logging.getLogger('pyvisa')
pyvisa_logger.setLevel(logging.WARNING)



class HP816xLambdaScan:
    def __init__(self):
        # Load the HP 816x library
        self.lib = ctypes.WinDLL("C:\\Program Files\\IVI Foundation\\VISA\\Win64\\Bin\\hp816x_64.dll")  # or .lib path
        self.visa_lib = ctypes.WinDLL("visa32.dll")
        self.session = None
        self.connected = False
        self._setup_function_prototypes()
        self.instrument = None

    def _setup_function_prototypes(self):
        # hp816x_init
        self.lib.hp816x_init.argtypes = [c_char_p, c_int32, c_int32, POINTER(c_int32)]
        self.lib.hp816x_init.restype = c_int32

        # --- Error/utility functions (so we can actually read human messages)
        ViSession = c_int32  
        ViStatus  = c_int32  
        self.lib.hp816x_error_message.argtypes = [ViSession, ViStatus, POINTER(c_char)]  
        self.lib.hp816x_error_message.restype  = ViStatus  
        self.lib.hp816x_error_query.argtypes   = [ViSession, POINTER(c_int32), POINTER(c_char)]  
        self.lib.hp816x_error_query.restype    = ViStatus  
        self.lib.hp816x_errorQueryDetect.argtypes = [ViSession, c_int32]  # VI_TRUE/VI_FALSE  
        self.lib.hp816x_errorQueryDetect.restype  = ViStatus  
        self.lib.hp816x_dcl.argtypes = [ViSession]  
        self.lib.hp816x_dcl.restype  = ViStatus  
        self.lib.hp816x_reset.argtypes = [ViSession]  
        self.lib.hp816x_reset.restype  = ViStatus  
        self.lib.hp816x_registerMainframe.argtypes = [ViSession]  
        self.lib.hp816x_registerMainframe.restype  = ViStatus  

        # hp816x_prepareMfLambdaScan
        self.lib.hp816x_prepareMfLambdaScan.argtypes = [
            c_int32,    # session ViSession
            c_int32,    # unit ViInt32
            c_double,   # power ViReal64
            c_int32,    # optical output ViInt32
            c_int32,    # number of scans ViInt32
            c_int32,    # PWM channels ViInt32
            c_double,   # start wavelength ViReal64
            c_double,   # stop wavelength ViReal64
            c_double,   # step size ViReal64
            POINTER(c_uint32),  # number of datapoints ViUInt32
            POINTER(c_uint32)   # number of value arrays ViUInt32
        ]
        self.lib.hp816x_prepareMfLambdaScan.restype = c_int32

        # hp816x_executeMfLambdaScan
        self.lib.hp816x_executeMfLambdaScan.argtypes = [c_int32, POINTER(c_double)]
        self.lib.hp816x_executeMfLambdaScan.restype = c_int32

        # hp816x_getLambdaScanResult
        self.lib.hp816x_getLambdaScanResult.argtypes = [
            c_int32, c_int32, c_int32, c_double, POINTER(c_double), POINTER(c_double)
        ]
        self.lib.hp816x_getLambdaScanResult.restype = c_int32

    def _err_msg(self, status):
        if not self.session:
            return f"(no session) status={status}"
        buf = create_string_buffer(512)
        # Driver/VISA message
        self.lib.hp816x_error_message(self.session, status, buf)
        msg = buf.value.decode(errors="replace")
        # Try instrument FIFO too (if any)
        inst_code = c_int32(0)
        buf2 = create_string_buffer(512)
        if self.lib.hp816x_error_query(self.session, byref(inst_code), buf2) == 0 and inst_code.value != 0:
            msg += f" | Instrument Error {inst_code.value}: {buf2.value.decode(errors='replace')}"
        return msg

    @staticmethod
    def _round_to_pm_grid(value_nm: float, step_pm: float) -> float:
        pm = step_pm
        return round((value_nm * 1000.0) / pm) * (pm / 1000.0)

    def connect(self):
        try:
            session = c_int32()
            # self.rm = pyvisa.ResourceManager()
            visa_address = "GPIB0::20::INSTR" 
    
            queryID = 1
            result = self.lib.hp816x_init(
                visa_address.encode(), queryID, 0, byref(session)
            )
            error_msg = create_string_buffer(256)  # 256 byte buffer
            self.lib.hp816x_error_message(session.value, result, error_msg)  
            logging.debug(f"result: {result}, error: {error_msg.value.decode('utf-8')}")  

            if result == 0:
                self.session = session.value
                self.lib.hp816x_errorQueryDetect(self.session, 1)  # VI_TRUE  
                self.lib.hp816x_registerMainframe(self.session)  
                self.connected = True
                return True
        except Exception as e:
            logging.error(f"[LSC] Connection error: {e}")
            return False

    def lambda_scan(self, start_nm=1490, stop_nm=1600, step_pm=0.5,
                    power_dbm=3.0, num_scans=0, channel=1):
        if not self.session:
            raise RuntimeError("Not connected to instrument")

        # Convert to meters
        start_wl = start_nm * 1e-9
        stop_wl = stop_nm * 1e-9
        step_size = step_pm * 1e-12

        pts_est = int(((float(stop_nm) - float(start_nm)) / float(step_pm / 1000.0)) + 1.0000001)  #
        max_points_per_scan = 20001  # Machine threshold
        stitching = pts_est > max_points_per_scan  
        ##############################################################
        # Addendum
        # To obtain a higher precision, the Tunable Laser Source 
        # is set 1 nm before the Start Wavelength, this means, 
        # you have to choose a Start Wavelength 1 nm greater than 
        # the minimum possible wavelength. Also, the wavelength 
        # sweep is actually started 90 pm befo re the Start Wavelength
        #  and ends 90 pm after the Stop Wavelength, this means, you 
        # have to choose a Stop Wavelength 90 pm less than 
        # the maximum possible wavelength.
        ###############################################################

        # If stitching is not needed, fall through to original single-scan code path below.  
        if stitching:  
            # Determine number of segments and (estimated) progress count
            segments = int(np.ceil(pts_est / float(max_points_per_scan)))
            # We will define each segment by exact step count, but we must reserve points
            # for the TLS guard band: starts 90 pm before Start and ends 90 pm after Stop.
            guard_pre_pm  = 90.0
            guard_post_pm = 90.0
            guard_total_pm = guard_pre_pm + guard_post_pm
            # Convert step to nm once
            step_nm = step_pm / 1000.0  # pm -> nm

            # guard allowance, ceil plus +2 
            guard_points = int(np.ceil(guard_total_pm / step_pm)) + 2
            
            eff_points_budget = max_points_per_scan - guard_points
            if eff_points_budget < 2:
                raise RuntimeError("Step too large for guard-banded segmentation (eff_points_budget < 2).")

            bottom = start_nm  # in nm  
            wl_parts  = []  # list of wavelength chunks (nm)  
            pwr_parts = []  # list of power chunks (dBm) for the selected channel  

            # tqdm for stitchign progress  
            for seg in tqdm(range(segments), desc="Lambda Scan Stitching", unit="seg"):
                # Plan by exact step count: N_req = eff_points_budget -> span = (N_req - 1) * step
                planned_top = bottom + (eff_points_budget - 1) * step_nm
                top = min(planned_top, stop_nm)  # nm  

                # Exact boundaries 
                bottom_r = bottom  
                top_r    = top  
                print(bottom_r, top_r, step_pm)
                while True:
                    num_points_seg = c_uint32()  
                    num_arrays_seg = c_uint32()  
                    result = self.lib.hp816x_prepareMfLambdaScan(  
                        self.session, 
                        0,  # 0 hp816x_PU_DBM 1 hp816x_PU_WATT
                        power_dbm, # Set power output to a val in dBm
                        0, # 0: High power, 1: Low SSE, 2: BHR Both high power 3: BLR Both Low SSE (0 WORKS)
                        num_scans, # 0 index to 3 scans
                        2,  # PWM channels, how many to use
                        bottom_r * 1e-9, # in m  
                        top_r * 1e-9,    # in m  
                        step_pm * 1e-12, # in m  
                        byref(num_points_seg), # number of wavelength steps llscan produce
                        byref(num_arrays_seg) # number of PW Chn (allocate num of power value arrays for ll scan func)
                    )  
                    if result == 0:
                        break

                # Allocate arrays for this segment  
                points_seg = num_points_seg.value
                wavelengths_seg = (c_double * points_seg)()  
                powers_seg      = (c_double * points_seg)()  # selected channel only  

                # Execute scan (fills wavelengths)  
                result = self.lib.hp816x_executeMfLambdaScan(self.session, wavelengths_seg)  
                if result != 0:  
                    raise RuntimeError(f"Execute scan failed: {result} :: {self._err_msg(result)}")  

                # Get results for selected channel  
                result = self.lib.hp816x_getLambdaScanResult(  
                    self.session, channel, 1, -90.0, powers_seg, wavelengths_seg
                )  
                if result != 0:  
                    raise RuntimeError(f"Get results failed: {result} :: {self._err_msg(result)}")  

                # Convert this segment to numpy (nm, dBm)  
                wl_nm_seg   = np.fromiter((wavelengths_seg[i] for i in range(points_seg)), dtype=np.float64, count=points_seg) * 1e9  
                pwr_dbm_seg = np.fromiter((powers_seg[i]      for i in range(points_seg)), dtype=np.float64, count=points_seg)  

                # if the first point equals last of previous, drop it  
                if wl_parts and wl_parts[-1].size > 0 and np.isclose(wl_nm_seg[0], wl_parts[-1][-1], rtol=0, atol=1e-6):  
                    wl_nm_seg   = wl_nm_seg[1:]   
                    pwr_dbm_seg = pwr_dbm_seg[1:]  

                # Accumulate   
                wl_parts.append(wl_nm_seg)  
                pwr_parts.append(pwr_dbm_seg)  

                # Step
                bottom = top_r + step_nm  # nm

        # Determine last wavelength we actually captured
        if wl_parts and wl_parts[-1].size > 0:
            last_wl_sample = wl_parts[-1][-1]        # nm
        else:
            last_wl_sample = start_nm - (step_pm/1000.0)  # force one remainder if somehow empty

        # If we haven't reached stop_nm yet add a final segment
        if last_wl_sample < stop_nm - 1e-6:
            step_nm = step_pm / 1000.0
            rem_bottom = last_wl_sample + step_nm     
            rem_top    = stop_nm

            bottom_r = rem_bottom
            top_r    = rem_top

            while True:
                num_points_seg = c_uint32()
                num_arrays_seg = c_uint32()
                result = self.lib.hp816x_prepareMfLambdaScan(  
                        self.session, 
                        0,  # 0 hp816x_PU_DBM 1 hp816x_PU_WATT
                        power_dbm, # Set power output to a val in dBm
                        0, # 0: High power, 1: Low SSE, 2: BHR Both high power 3: BLR Both Low SSE (0 WORKS)
                        num_scans, # 0 index to 3 scans
                        2,  # PWM channels, how many to use
                        bottom_r * 1e-9, # in m  
                        top_r * 1e-9,    # in m  
                        step_pm * 1e-12, # in m  
                        byref(num_points_seg), # number of wavelength steps llscan produce
                        byref(num_arrays_seg) # number of PW Chn (allocate num of power value arrays for ll scan func)
                    )  
                if result == 0:
                    break
            points_seg = num_points_seg.value
            wavelengths_seg = (c_double * points_seg)()
            powers_seg      = (c_double * points_seg)()

            result = self.lib.hp816x_executeMfLambdaScan(self.session, wavelengths_seg)
            if result != 0:
                raise RuntimeError(f"Execute scan failed: {result} :: {self._err_msg(result)}")

            result = self.lib.hp816x_getLambdaScanResult(
                self.session, channel, 1, -90.0, powers_seg, wavelengths_seg
            )
            if result != 0:
                raise RuntimeError(f"Get results failed: {result} :: {self._err_msg(result)}")

            wl_nm_seg   = np.fromiter((wavelengths_seg[i] for i in range(points_seg)), dtype=np.float64, count=points_seg) * 1e9
            pwr_dbm_seg = np.fromiter((powers_seg[i]      for i in range(points_seg)), dtype=np.float64, count=points_seg)

            trim_idx = np.searchsorted(wl_nm_seg, last_wl_sample + 1e-6, side="left")
            if trim_idx > 0:
                wl_nm_seg   = wl_nm_seg[trim_idx:]
                pwr_dbm_seg = pwr_dbm_seg[trim_idx:]

            # Accumulate
            wl_parts.append(wl_nm_seg)
            pwr_parts.append(pwr_dbm_seg)  

            # Final concatenate   
            wl_array  = np.concatenate(wl_parts) if wl_parts else np.array([], dtype=np.float64)  
            pow_array = np.concatenate(pwr_parts) if pwr_parts else np.array([], dtype=np.float64)  

            return {
                'wavelengths_nm': wl_array,
                'powers_dbm':     pow_array,
                'num_points':     wl_array.size
            } 

        # Prepare scan
        num_points = c_uint32()
        num_arrays = c_uint32()
        
        ##########################################################
        # hp816x_prepareLambdaScan(
        #     ViSession ihandle, ViInt32 powerUnit, 
        #     ViReal64 power, ViInt32 opticalOutput, 
        #     ViInt32 numberofScans, ViInt32 PWMChannels, 
        #     ViReal64 startWavelength, ViReal64 stopWavelength, 
        #     ViReal64 stepSize, ViUInt32 numberofDatapoints, 
        #     ViUInt32 numberofChannels);
        ##########################################################
        # 81635A:
        #   Power range: +10 to -80dBm
        #   Wavelength range 800 nm – 1650 nm
        result = self.lib.hp816x_prepareMfLambdaScan(
            self.session, 
            0,  # 0 hp816x_PU_DBM 1 hp816x_PU_WATT
            power_dbm, # Set power output to a val in dBm
            0, # 0: High power, 1: Low SSE, 2: BHR Both high power 3: BLR Both Low SSE (0 WORKS)
            num_scans, # 0 index to 3 scans
            2,  # PWM channels, how many to use
            start_wl, # in m
            stop_wl, # in m
            step_size, # in m
            byref(num_points), # number of wavelength steps llscan produce
            byref(num_arrays) # number of PW Chn (allocate num of power value arrays for ll scan func)
        )
        error_msg = ctypes.create_string_buffer(256)  # 256 byte buffer
        if result != 0:
            code = self.lib.hp816x_error_message(self.session, result, error_msg)
            raise RuntimeError(
                f"Prepare scan failed: {result} errcode: {code}")  

        # # Get the values for sanity
        # paramsq = self.lib.hp816x_getLambdaScanParameters_Q()
        # if paramsq != 0:
        #     raise RuntimeError(
        #         f"Paramsq: {paramsq}: errcode: {self.lib.hp816x_error_message
        #         (self.session, paramsq, error_msg)}"
        #     )
        # else:
        #     print(paramsq)

        # Allocate arrays
        points = num_points.value
        wavelengths = (c_double * points)()
        powers = (c_double * points)()

        # Execute scan
        result = self.lib.hp816x_executeMfLambdaScan(self.session, wavelengths)
        if result != 0:
            raise RuntimeError(f"Execute scan failed: {result}")

        # Get results
        result = self.lib.hp816x_getLambdaScanResult(
            self.session, channel, 1, -90.0, powers, wavelengths
        )
        if result != 0:
            raise RuntimeError(f"Get results failed: {result}")

        # Convert to numpy arrays
        wl_array = np.array([wavelengths[i] for i in range(points)])
        pow_array = np.array([powers[i] for i in range(points)])

        return {
            'wavelengths_nm': wl_array * 1e9,
            'powers_dbm': pow_array,
            'num_points': points
        }

    def save_csv(self, data, filename):
        df = pd.DataFrame({
            'Wavelength_nm': data['wavelengths_nm'],
            'Power_dBm': data['powers_dbm']
        })
        df.to_csv(filename, index=False)

    def disconnect(self):
        if self.session:
            self.lib.hp816x_close(self.session)
            self.connected = None

def main():
    """Tester"""
    inst = HP816xLambdaScan()
    ok = inst.connect()
    if ok:
        print("success")
    else:
        inst.disconnect()
        return 

    dict = inst.lambda_scan()
    
    inst.save_csv(dict, 'test_data.csv')

    print(dict)
    inst.disconnect()

if __name__ == "__main__":
    main()
