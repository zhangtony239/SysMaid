import os
import sys
import unittest
import time
import subprocess
from unittest.mock import MagicMock

# Add the project's 'src' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import sysmaid as maid
from sysmaid import maid as maid_module

class TestWmiEvents(unittest.TestCase):

    def setUp(self):
        """Called before each test."""
        # Clear any watchdogs from previous tests
        maid_module._watchdogs.clear()
        self.process = None

    def tearDown(self):
        """Called after each test."""
        for dog in maid_module._watchdogs:
            dog._is_running = False
            if dog._thread and dog._thread.is_alive():
                dog._thread.join(timeout=2)
        
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
            
        maid_module._watchdogs.clear()

    def test_is_running_and_is_exited_events(self):
        """
        End-to-end test for process creation and deletion events.
        """
        process_name = "winver.exe"
        
        # Create mocks for our callbacks
        running_callback = MagicMock()
        exited_callback = MagicMock()

        # Define the rules
        watcher = maid.attend(process_name)
        watcher.is_running(running_callback)
        watcher.is_exited(exited_callback)

        # Start the watchdogs manually for the test
        for dog in maid_module._watchdogs:
            dog.start()
        
        # Give a moment for the WMI event subscriptions to register
        time.sleep(3)

        # --- Test is_running ---
        print(f"\n--- Starting {process_name} to test is_running ---")
        self.process = subprocess.Popen([process_name])
        
        # Wait for the event to be processed
        # WMI events can have a delay (we poll every 2s in the query).
        # We'll wait a bit longer to be safe.
        time.sleep(4)

        running_callback.assert_called_once()
        print("--- is_running callback was successfully triggered. ---")

        # --- Test is_exited ---
        print(f"\n--- Terminating {process_name} to test is_exited ---")
        self.process.terminate()
        self.process.wait()
        self.process = None
        
        # Wait for the deletion event to be processed
        time.sleep(4)
        
        exited_callback.assert_called_once()
        print("--- is_exited callback was successfully triggered. ---")

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] {%(module)s} %(message)s')
    unittest.main()