# SysMaid [![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fzhangtony239%2FSysMaid.svg?type=shield&issueType=security)](https://app.fossa.com/projects/git%2Bgithub.com%2Fzhangtony239%2FSysMaid?ref=badge_shield&issueType=security)
[简体中文](https://github.com/zhangtony239/SysMaid/blob/main/README.md)

**SysMaid** is a high-level `win32 api` abstraction layer for Windows, allowing users to discover and optimize the system's background environment by writing simple Python scripts. It acts like a uBlock Origin for process management, designed to address the background resource abuse by "must-use software" and aims to become the most comprehensive AutoRun ecosystem on Windows.
<br /><br />

#### Downloaded file disappeared?

Due to SysMaid's behavior involving system-level process monitoring and operations, some antivirus software (like Windows Defender) may misreport it as a potential threat. To ensure the program runs correctly, it is strongly recommended to add your script, the packaged `.exe` file, or its directory to your antivirus software's whitelist.

## Core Features

*   **Concise Rule Definition**: Intuitively define monitoring rules using Python decorators.
*   **Process and Service Monitoring**: Easily monitor the status of specified processes, such as whether a window exists or if a process has exited.
*   **Automated Actions**: Automatically execute actions when conditions are met, such as killing a process, stopping a service, or locking an encrypted volume.
*   **Extensibility**: Easily add new conditions and actions to meet more complex needs.


## Quick Start

### Installation

```bash
pip install sysmaid
```

### Usage

Create a Python file (e.g., `my_rules.py`) and add your rules:

```python
import sysmaid as maid

if __name__ == "__main__":
    # Rule 1: Kill Canva.exe if it's running without a window
    Canva = maid.attend('Canva.exe')
    @Canva.has_no_window
    def _():
        maid.kill_process('Canva.exe')

    # Rule 2: Stop the related service when GameViewer.exe exits
    GameViewer = maid.attend('GameViewer.exe')
    @GameViewer.is_exited
    def _():
        maid.stop_service('GameViewerService')

    # Rule 3: Kill CrossDeviceResume.exe when it is running
    CrossDeviceResume = maid.attend('CrossDeviceResume.exe')
    @CrossDeviceResume.is_running
    def _():
        maid.kill_process('CrossDeviceResume.exe')

    # Rule 4: When Macrium Reflect completes a backup, automatically lock the backup drive (D:) and close the backup program
    # (Requires BitLocker to be enabled on drive D:)
    Screen = maid.attend('Screen')
    @Screen.has_windows_look_like('MacriumSuccess.png')
    def _():
        maid.lock_volume('D')
        maid.kill_process('Reflect.exe')

    # Rule 5: When CPU usage exceeds 80% for 10 consecutive seconds, report the top 5 CPU-consuming processes and log them.
    Cpu = maid.attend('cpu')
    @Cpu.is_too_busy(over=80, duration=10)
    # You can also specify per-logical-processor thresholds to resolve average utilization calculation errors on heterogeneous CPUs.
    # @Cpu.is_too_busy(over=[40,40,40,40,70,70,70,70], duration=5)
    def _():
        TopProcesses = maid.get_top_processes(5)
        maid.alarm(TopProcesses)
        maid.write_file('logs/TopProcesses.log',TopProcesses)

    # Set log level and start monitoring
    maid.set_log_level('INFO')
    maid.start()
```

Then run it:

```bash
python my_rules.py
```

## Deployment: Packaging as a Background Service

To achieve true "background standby" and auto-start on boot, it is recommended to use **Nuitka** to package your rule script into a standalone `.exe` executable. Nuitka compiles the Python script into C code, generating an efficient, dependency-free program.

**Install Nuitka:**

```bash
pip install nuitka
```

**Packaging Command:**

```bash
nuitka --standalone --windows-uac-admin --windows-console-mode=disable your_rules.py
```

*   `--standalone`: Creates a standalone folder with all dependencies included.
*   `--windows-uac-admin`: Requests administrator privileges, which are necessary for operations like stopping services.
*   `--windows-console-mode=disable`: Creates a windowless background application that won't show a black console window when run.
*   `your_rules.py`: Your rule script filename.

After successful packaging, you will find the generated `.exe` file in the `your_rules.dist` folder. You can place this file or its shortcut into the system's "Startup" folder to have it launch automatically on boot.

## Future Plans

SysMaid's goal extends beyond simple process management. We hope to develop it into the most comprehensive **AutoRun ecosystem** on Windows, including but not limited to:

*   Richer trigger conditions (e.g., network activity, CPU/memory usage).
*   More diverse response actions (e.g., modifying the registry, file operations).
*   Providing a graphical user interface to make it accessible for users unfamiliar with programming.
*   ...

## Contributing

Contributions of any kind are welcome! If you have good ideas or find a bug, please feel free to submit an Issue or Pull Request. To capture logs, you can run the script directly in a Python environment and ensure the logging level is set to `INFO` or higher.

<a href="https://roocode.com/">
<img height="32" src="https://github.com/user-attachments/assets/b963732e-8cb2-42c0-a398-d80768a7f86f"></img>
</a>

## License

This project is open-sourced under the [GPLv3 License](https://github.com/zhangtony239/SysMaid/blob/main/LICENSE).
