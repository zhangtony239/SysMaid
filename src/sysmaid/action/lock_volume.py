import logging
import wmi
import pythoncom

logger = logging.getLogger(__name__)

def lock_volume(drive_letter: str):
    """
    Locks a BitLocker-encrypted volume using WMI.
    This action requires administrator privileges to run.
    """
    logger.info(f"Attempting to lock volume {drive_letter}: via WMI.")

    if not drive_letter or len(drive_letter) > 1:
        logger.error(f"Invalid drive letter provided: '{drive_letter}'. It must be a single character (e.g., 'D').")
        return

    drive = f"{drive_letter.upper()}:"

    try:
        pythoncom.CoInitialize()
        c = wmi.WMI(namespace="root/cimv2/security/microsoftvolumeencryption")
        
        # Find the encryptable volume
        volumes = c.Win32_EncryptableVolume(DriveLetter=drive)
        
        if not volumes:
            logger.warning(f"Could not find a BitLocker volume for drive '{drive}'. The drive may not exist or is not encryptable.")
            return

        volume = volumes[0]
        
        # Check protection status
        protection_status = volume.GetProtectionStatus()[0]
        if protection_status == 0:
            logger.warning(f"Cannot lock volume {drive} because BitLocker protection is OFF.")
            return

        # Check lock status
        conversion_status = volume.GetConversionStatus()[0]
        if conversion_status != 1: # 1 means fully encrypted
             logger.warning(f"Cannot lock volume {drive} because it is not fully encrypted.")
             return

        # Lock the volume
        result = volume.Lock()
        return_value = result[0]

        if return_value == 0:
            logger.info(f"Successfully sent lock command to volume '{drive}'.")
        elif return_value == 0x80310031: # FVE_E_LOCKED
            logger.info(f"Volume '{drive}' is already locked.")
        elif return_value == 0x80310009: # FVE_E_NOT_ENCRYPTED
             logger.warning(f"Cannot lock volume {drive} because it is not protected by BitLocker.")
        else:
            logger.error(f"Failed to lock volume '{drive}'. WMI returned error code: {hex(return_value)}")

    except Exception as e:
        if "WBEM_E_ACCESS_DENIED" in str(e):
            logger.error(f"Failed to lock {drive}. This command requires administrator privileges.")
        else:
            logger.critical(f"An unexpected critical error occurred while trying to lock volume {drive}: {e}", exc_info=True)
    finally:
        pythoncom.CoUninitialize()