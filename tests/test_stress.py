import os
import sys
# Add the project's 'src' directory to the Python path to allow imports from it.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import unittest
from unittest.mock import patch, MagicMock, call

# We need to mock 'sysmaid' and its dependencies BEFORE they are imported by the code under test.
# So, we create fake modules in sys.modules.
import sys
sys.modules['wmi'] = MagicMock()
sys.modules['win32gui'] = MagicMock()
sys.modules['win32process'] = MagicMock()
sys.modules['pythoncom'] = MagicMock()

# Now we can safely import the package to be tested
import sysmaid as maid
# We also need to import the 'maid' module specifically to access its internal '_watchdogs' list for testing.
from sysmaid import maid as maid_module

# We will patch the action functions directly on the imported package
maid.kill_process = MagicMock()
maid.stop_service = MagicMock()


class StressTest(unittest.TestCase):
    
    def setUp(self):
        """
        This method is called before each test.
        It sets up the mock environment.
        """
        # Reset mocks and maid's internal state for test isolation
        maid.kill_process.reset_mock()
        maid.stop_service.reset_mock()
        
        # VERY IMPORTANT: Clear the global watchdog list in the maid module
        maid_module._watchdogs.clear()

        # Shared state for mocks to read from. This simulates the OS state.
        self.mock_os_state = {
            'processes': {},  # 'proc_name': {'pid': pid}
            'windows': {}     # 'hwnd': pid
        }

        # Configure the mocks
        self.configure_mocks()

    def tearDown(self):
        """
        This method is called after each test.
        It stops all watchdog threads to prevent them from running into the next test.
        """
        for dog in maid_module._watchdogs:
            dog._is_running = False
            if dog._thread and dog._thread.is_alive():
                dog._thread.join(timeout=2) # Give threads a moment to die
        maid_module._watchdogs.clear() # Final cleanup

    def mock_wmi_constructor(self):
        """Mocks `wmi.WMI()`"""
        mock_wmi_instance = MagicMock()
        
        def mock_win32_process(name):
            if name in self.mock_os_state['processes']:
                pid = self.mock_os_state['processes'][name]['pid']
                mock_process = MagicMock()
                mock_process.ProcessId = pid
                return [mock_process]
            return []
            
        mock_wmi_instance.Win32_Process = mock_win32_process
        return mock_wmi_instance

    def mock_enum_windows(self, callback, _):
        """Mocks `win32gui.EnumWindows`"""
        for hwnd, pid in self.mock_os_state['windows'].items():
            # Mock the functions called by the real callback
            sys.modules['win32gui'].IsWindowVisible.return_value = True
            sys.modules['win32gui'].GetWindowText.return_value = "Mock Window"
            sys.modules['win32process'].GetWindowThreadProcessId.return_value = (0, pid)
            callback(hwnd, None)

    def configure_mocks(self):
        """Apply all mock configurations."""
        sys.modules['wmi'].WMI.side_effect = self.mock_wmi_constructor
        sys.modules['win32gui'].EnumWindows.side_effect = self.mock_enum_windows
        sys.modules['pythoncom'].CoInitialize.return_value = None
        sys.modules['pythoncom'].CoUninitialize.return_value = None


    @patch('sysmaid.maid.BaseWatchdog.start')
    def test_1000_rules_triggered_simultaneously(self, mock_watchdog_start):
        """
        Stress test: 1000 has_no_window rules are defined.
        The test bypasses threading by patching Watchdog.start and manually
        calling check_state to verify the core logic in a fast, deterministic way.
        """
        num_rules = 1000
        mock_watchdog_start.return_value = None # Ensure start() does nothing

        # 1. Setup the initial state
        for i in range(num_rules):
            proc_name = f'proc_{i}.exe'
            pid = 1000 + i
            hwnd = 5000 + i
            self.mock_os_state['processes'][proc_name] = {'pid': pid}
            self.mock_os_state['windows'][hwnd] = pid

        # 2. Define the 1000 rules
        for i in range(num_rules):
            proc_name = f'proc_{i}.exe'
            action_func = lambda name=proc_name: maid.kill_process(name)
            watcher = maid.attend(proc_name)
            watcher.has_no_window(action_func)

        # 3. Setup for manual checking
        c = self.mock_wmi_constructor()
        
        # 4. Initial state check: verify no actions are triggered
        pids_with_windows = set(self.mock_os_state['windows'].values())
        for dog in maid_module._watchdogs:
            dog.c = c  # Manually set the mocked WMI connection
            dog.check_process_state(pids_with_windows)
        maid.kill_process.assert_not_called()

        # 5. The "simultaneous" event: all windows disappear
        print("\n--- All windows are disappearing now! ---")
        self.mock_os_state['windows'].clear()
        pids_with_windows.clear()

        # 6. Manually simulate the 3 checks for the GRACE_PERIOD
        print("--- Manually simulating 3 watchdog checks... ---")
        for i in range(3):
            print(f"Check {i+1}...")
            for dog in maid_module._watchdogs:
                dog.check_process_state(pids_with_windows)

        # 7. Assert that all 1000 actions have been called
        self.assertEqual(maid.kill_process.call_count, num_rules)
        expected_calls = [call(f'proc_{i}.exe') for i in range(num_rules)]
        maid.kill_process.assert_has_calls(expected_calls, any_order=True)

        print(f"--- Stress test successful! {maid.kill_process.call_count} actions were triggered. ---")
    @patch('sysmaid.maid.HardwareWatchdog.start')
    def test_cpu_is_too_busy_triggers_action(self, mock_start):
        """
        Tests that the is_too_busy condition for CPU triggers an action correctly,
        using the new WMI implementation.
        """
        mock_start.return_value = None
        action_mock = MagicMock()

        # 1. Setup Mock WMI
        mock_wmi_connection = self.mock_wmi_constructor()
        
        # We need a mock processor object for WMI to return
        mock_processor = MagicMock()
        
        # We will control the CPU load by changing this list
        mock_cpu_loads = [mock_processor]
        
        # Point the mock WMI connection to our controllable list
        mock_wmi_connection.Win32_Processor = lambda: mock_cpu_loads
        

        # 2. Define the rule
        # Check if CPU is over 90% for 2 consecutive checks
        watcher = maid.attend('cpu')
        watcher.is_too_busy(over=90, duration=2)(action_mock)

        # 3. Manually trigger checks
        dog = maid_module._watchdogs[-1]
        dog.c = mock_wmi_connection # Manually inject the mocked WMI connection

        # Check 1: CPU load is high (95%)
        mock_processor.LoadPercentage = 95
        dog.check_state()
        action_mock.assert_not_called() # Duration not met yet
        self.assertFalse(dog._is_busy)

        # Check 2: CPU load is still high (98%), duration is now met
        mock_processor.LoadPercentage = 98
        dog.check_state()
        action_mock.assert_called_once() # Action should fire
        self.assertTrue(dog._is_busy)     # State should be busy

        # Check 3: CPU load is still high (99%), should not re-trigger immediately
        action_mock.reset_mock()
        mock_processor.LoadPercentage = 99
        dog.check_state()
        action_mock.assert_not_called() # Should not fire again yet
        self.assertTrue(dog._is_busy)

        # Check 4: CPU load drops (50%)
        mock_processor.LoadPercentage = 50
        dog.check_state()
        self.assertFalse(dog._is_busy) # Busy state should reset
        action_mock.assert_not_called()

        # Check 5 & 6: CPU load goes back up, should fire again
        mock_processor.LoadPercentage = 92
        dog.check_state() # History: [False, True]
        mock_processor.LoadPercentage = 93
        dog.check_state() # History: [True, True] -> Fire!
        action_mock.assert_called_once()
        self.assertTrue(dog._is_busy)


if __name__ == '__main__':
    # Configure logging to see output from maid
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    unittest.main()