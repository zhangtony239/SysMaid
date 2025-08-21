import logging
import wmi
import pythoncom

logger = logging.getLogger(__name__)

def stop_service(service_name):
    """
    Finds and stops a Windows service by its name.
    """
    logger.info(f"Executing stop for service '{service_name}'.")
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        
        # Find the service
        services = c.Win32_Service(Name=service_name)
        
        if not services:
            logger.warning(f"Stop command ran, but service '{service_name}' was not found.")
            return

        service = services[0]

        # Check if the service is already stopped
        if service.State == 'Stopped':
            logger.info(f"Service '{service_name}' is already stopped.")
            return

        # Stop the service
        result, = service.StopService()

        if result == 0:
            logger.info(f"Successfully sent stop command to service '{service_name}'.")
        elif result == 5:
            logger.warning(f"Service '{service_name}' is not running, so it could not be stopped.")
        else:
            logger.error(f"Failed to stop service '{service_name}'. Error code: {result}")

    except Exception as e:
        logger.error(f"A critical error occurred while trying to stop service '{service_name}': {e}", exc_info=True)
    finally:
        pythoncom.CoUninitialize()