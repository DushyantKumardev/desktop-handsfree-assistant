"""Windows System Control handler (volume percentage, media keys, screen locking)."""

import ctypes
import logging
import re
from src.automation.models import ExecutionResult

logger = logging.getLogger(__name__)

# Windows Virtual-Key Codes
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002


class SystemHandler:
    """Handles Windows master audio volume, media playback, and computer locking."""

    @classmethod
    def control(cls, command: str) -> ExecutionResult:
        """Dispatches system control requests."""
        cmd = command.lower().strip()

        try:
            # Check for exact percentage volume setting (e.g. "volume_set:45", "45%", "45", "volume 45")
            num_match = re.search(r"(\d{1,3})", cmd)
            is_volume_num = num_match and (
                "volume" in cmd or "awaz" in cmd or "sound" in cmd or "set" in cmd
                or cmd.endswith("%") or cmd.isdigit() or "volume_set" in cmd
            )

            if is_volume_num and num_match:
                percent = max(0, min(100, int(num_match.group(1))))
                success = cls._set_master_volume_percent(percent)
                return ExecutionResult(
                    success=success,
                    action="system_control",
                    message=f"Master volume set to {percent}%.",
                )

            elif "volume_up" in cmd or "up" in cmd or "badhao" in cmd:
                for _ in range(5):  # 5 steps volume up (~10%)
                    cls._send_virtual_key(VK_VOLUME_UP)
                return ExecutionResult(success=True, action="system_control", message="Volume increased.")

            elif "volume_down" in cmd or "down" in cmd or "kam" in cmd:
                for _ in range(5):  # 5 steps volume down (~10%)
                    cls._send_virtual_key(VK_VOLUME_DOWN)
                return ExecutionResult(success=True, action="system_control", message="Volume decreased.")

            elif "mute" in cmd or "chup" in cmd or "unmute" in cmd:
                cls._send_virtual_key(VK_VOLUME_MUTE)
                return ExecutionResult(success=True, action="system_control", message="Volume mute toggled.")

            elif "play" in cmd or "pause" in cmd or "roko" in cmd:
                cls._send_virtual_key(VK_MEDIA_PLAY_PAUSE)
                return ExecutionResult(success=True, action="system_control", message="Media playback toggled.")

            elif "lock" in cmd:
                ctypes.windll.user32.LockWorkStation()
                return ExecutionResult(success=True, action="system_control", message="Computer locked.")

            else:
                return ExecutionResult(
                    success=False,
                    action="system_control",
                    message=f"Unknown system control target: {command}",
                )
        except Exception as e:
            logger.error("System control execution failed: %s", e)
            return ExecutionResult(
                success=False,
                action="system_control",
                message=f"System control failed: {e}",
            )

    @classmethod
    def _set_master_volume_percent(cls, percent: int) -> bool:
        """Sets Windows master volume to an exact percentage (0-100)."""
        scalar = max(0.0, min(1.0, percent / 100.0))

        # 1. Primary method: Windows Core Audio API via COM (Zero-dependency exact scalar)
        try:
            import uuid
            from ctypes import POINTER, HRESULT, Structure, c_float, c_void_p, byref, cast, windll, WINFUNCTYPE
            from ctypes.wintypes import DWORD

            class GUID(Structure):
                _fields_ = [
                    ("Data1", DWORD),
                    ("Data2", ctypes.c_ushort),
                    ("Data3", ctypes.c_ushort),
                    ("Data4", ctypes.c_ubyte * 8),
                ]

            def make_guid(guid_str: str) -> GUID:
                u = uuid.UUID(guid_str)
                f = u.fields
                return GUID(f[0], f[1], f[2], (ctypes.c_ubyte * 8)(*u.bytes[8:]))

            CLSID_MMDeviceEnumerator = make_guid("BCDE0395-E52F-467C-8E3D-C4579291692E")
            IID_IMMDeviceEnumerator = make_guid("A95664D2-9614-4F35-A746-DE8DB63617E6")
            IID_IAudioEndpointVolume = make_guid("5CDF2C82-841E-4546-9722-0CF74078229A")

            windll.ole32.CoInitialize(None)

            pEnumerator = c_void_p()
            hr = windll.ole32.CoCreateInstance(
                byref(CLSID_MMDeviceEnumerator),
                None,
                1,  # CLSCTX_INPROC_SERVER
                byref(IID_IMMDeviceEnumerator),
                byref(pEnumerator),
            )
            if hr == 0 and pEnumerator:
                vtable_enum = cast(cast(pEnumerator, POINTER(c_void_p)).contents, POINTER(c_void_p))
                GetDefaultAudioEndpoint_proto = WINFUNCTYPE(HRESULT, c_void_p, DWORD, DWORD, POINTER(c_void_p))
                GetDefaultAudioEndpoint = GetDefaultAudioEndpoint_proto(vtable_enum[4])

                pDevice = c_void_p()
                hr = GetDefaultAudioEndpoint(pEnumerator, 0, 1, byref(pDevice))
                if hr == 0 and pDevice:
                    vtable_dev = cast(cast(pDevice, POINTER(c_void_p)).contents, POINTER(c_void_p))
                    Activate_proto = WINFUNCTYPE(HRESULT, c_void_p, POINTER(GUID), DWORD, c_void_p, POINTER(c_void_p))
                    Activate = Activate_proto(vtable_dev[3])

                    pEndpointVolume = c_void_p()
                    hr = Activate(pDevice, byref(IID_IAudioEndpointVolume), 1, None, byref(pEndpointVolume))
                    if hr == 0 and pEndpointVolume:
                        vtable_vol = cast(cast(pEndpointVolume, POINTER(c_void_p)).contents, POINTER(c_void_p))
                        SetScalar_proto = WINFUNCTYPE(HRESULT, c_void_p, c_float, c_void_p)
                        SetScalar = SetScalar_proto(vtable_vol[7])
                        res = SetScalar(pEndpointVolume, c_float(scalar), None)
                        if res == 0:
                            logger.info("Master volume set to %.2f (%d%%) via Core Audio COM API", scalar, percent)
                            return True
        except Exception as e:
            logger.debug("Core Audio COM API volume setting failed: %s. Using key event fallback.", e)

        # 2. Hardware fallback: step volume to 0%, then step up by 2% increments
        try:
            for _ in range(50):
                cls._send_virtual_key(VK_VOLUME_DOWN)
            steps = round(percent / 2)
            for _ in range(steps):
                cls._send_virtual_key(VK_VOLUME_UP)
            logger.info("Master volume set to ~%d%% via keybd_event stepping.", percent)
            return True
        except Exception as fallback_err:
            logger.error("Volume setting fallback failed: %s", fallback_err)
            return False

    @staticmethod
    def _send_virtual_key(key_code: int) -> None:
        """Sends a hardware virtual keypress and release."""
        ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(key_code, 0, KEYEVENTF_KEYUP, 0)
