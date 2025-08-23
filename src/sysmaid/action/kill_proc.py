import logging
import subprocess

logger = logging.getLogger(__name__)

def kill_process(process_name):
    """
    Forcefully terminates a process and its entire process tree using taskkill.
    This requires administrator privileges to kill elevated/protected processes.
    """
    logger.info(f"Executing force kill for '{process_name}' using taskkill.")
    try:
        command = [
            "taskkill",
            "/F",       # Forcefully terminate
            "/T",       # Terminate process tree
            "/IM",      # Specify image name
            process_name
        ]
        
        # We use CREATE_NO_WINDOW to prevent the console from flashing.
        # capture_output=True pipes stdout/stderr, preventing them from showing up.
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False, # We will check the result manually
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # taskkill exit codes:
        # 0: Success, the process was terminated.
        # 128: The process was not found.
        # 1: Access denied (permission issue).
        if result.returncode == 0:
            logger.info(f"Successfully sent termination signal to '{process_name}'. Output: {result.stdout.strip()}")
        elif result.returncode == 128:
            logger.info(f"Kill command ran, but no active '{process_name}' processes were found.")
        elif result.returncode == 1:
            logger.error(f"Failed to kill '{process_name}': Access Denied. Ensure SysMaid is run with administrator privileges. Details: {result.stderr.strip()}")
        else:
            logger.error(f"taskkill failed for '{process_name}' with exit code {result.returncode}. Stderr: {result.stderr.strip()}")

    except FileNotFoundError:
        logger.critical("`taskkill.exe` not found. This action is only supported on Windows.")
    except Exception as e:
        logger.error(f"A critical error occurred during taskkill for '{process_name}': {e}", exc_info=True)