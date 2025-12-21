import logging
import wmi
import pythoncom
import time

logger = logging.getLogger(__name__)

def lock_volume(drive_letter: str, timeout_seconds=30):
    """
    Locks a BitLocker-encrypted volume using WMI, with retries if the volume is in use.
    This action requires administrator privileges to run.
    """
    logger.info(f"Attempting to lock volume {drive_letter}: via WMI.")

    # Normalize drive letter: accept "D" or "D:"
    clean_letter = (drive_letter or "").strip().upper().rstrip(':')
    if len(clean_letter) != 1:
        logger.error(f"Invalid drive letter provided: '{drive_letter}'. It must be a single character (e.g., 'D').")
        return
    drive = f"{clean_letter}:"

    try:
        pythoncom.CoInitialize()
        c = wmi.WMI(namespace="root/cimv2/security/microsoftvolumeencryption")
        
        # Find the encryptable volume
        volumes = c.Win32_EncryptableVolume(DriveLetter=drive)
        
        if not volumes:
            logger.warning(f"Could not find a BitLocker volume for drive '{drive}'. The drive may not exist or is not encryptable.")
            return

        volume = volumes[0]

        start_time = time.time()
        while True:
            result = volume.Lock()
            logger.debug(f"Lock command returned: {result}")
            return_value = result[0]

            if return_value == 0:
                logger.info(f"Successfully sent lock command to volume '{drive}'.")
                return
            elif return_value == -0x7fcf0000:
                logger.info(f"Volume '{drive}' is already locked.")
                return
            elif return_value == -0x7ff8fffb:
                if time.time() - start_time < timeout_seconds:
                    logger.info(f"Volume '{drive}' is currently in use, retrying in 1 second...")
                    time.sleep(1)
                else:
                    logger.error(f"Failed to lock volume '{drive}' after {timeout_seconds} seconds as it remains in use. " \
                                 f"WMI returned error code: {hex(return_value)}")
                    return
            elif return_value == -0x7fceffff:
                logger.warning(f"Cannot lock volume {drive} because it is not protected by BitLocker.")
                return
            else:
                logger.error(f"Failed to lock volume '{drive}'. WMI returned error code: {hex(return_value)}")
                return # For other errors, no need to retry.
    
    except Exception as e:
        logger.critical(f"An unexpected critical error occurred while trying to lock volume {drive}: {e}", exc_info=True)
    finally:
        pythoncom.CoUninitialize()