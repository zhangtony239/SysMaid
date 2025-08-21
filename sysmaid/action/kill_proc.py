import logging
import wmi
import pythoncom

logger = logging.getLogger(__name__)

def kill(watchdog_instance):
    process_name = watchdog_instance.process_name
    logger.info(f"Executing kill for '{process_name}'.")
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        killed_count = 0
        processes_to_kill = c.Win32_Process(name=process_name)
        
        if not processes_to_kill:
            logger.info(f"Kill command ran, but no active '{process_name}' processes were found.")
            return

        for process in processes_to_kill:
            try:
                process.Terminate()
                killed_count += 1
                logger.info(f"Sent Terminate signal to '{process_name}' (PID: {process.ProcessId}).")
            except wmi.x_wmi as e:
                logger.warning(f"Could not terminate '{process_name}' (PID: {process.ProcessId}). It may have already exited. Details: {e}")
        
        logger.info(f"Kill command finished. Terminated {killed_count} instance(s) of '{process_name}'.")
        
    except Exception as e:
        logger.error(f"A critical error occurred during WMI kill for '{process_name}': {e}", exc_info=True)
    finally:
        pythoncom.CoUninitialize()