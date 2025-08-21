# SysMaid
[简体中文](README.md)

**SysMaid** is a high-level `win32 api` abstraction layer for Windows, allowing users to manage and optimize system behavior by writing simple Python scripts. It's like a local uBlock Origin, but focused on process management, designed to solve issues with "must-use" background software and aiming to become the most comprehensive AutoRun ecosystem on Windows.
<br /><br />

#### Downloaded file has disappeared?

Due to SysMaid's behavior involving system-level process monitoring and operations, some antivirus software (like Windows Defender) may misreport it as a potential threat. To ensure the program runs correctly, it is strongly recommended to add your script, the packaged `.exe` file, or its directory to your antivirus software's whitelist.

## Core Features

*   **Concise Rule Definition**: Intuitively define monitoring rules using Python decorators.
*   **Process and Service Monitoring**: Easily monitor the status of specified processes, such as whether a window exists or if a process has exited.
*   **Automated Actions**: Automatically execute actions when conditions are met, such as terminating a process or stopping a service.
*   **Extensibility**: Easily add new conditions and actions to adapt to more complex needs.


## One-Click Start

We welcome everyone to submit pull requests to build the Tony.py rules version together, making it a comprehensive set of interception rules. This way, you can download the Nuitka-compiled exe from this repository's release to get a cleaner system environment directly.

## Getting Started

### Installation

```bash
pip install -r requirements.txt
```

### Usage

Create a Python file (e.g., `my_rules.py`) and add your rules:

```python
import sysmaid as maid

if __name__ == "__main__":
    # Rule 1: Kill Canva.exe when the process exists but has no window
    Canva = maid.attend('Canva.exe')
    @Canva.has_no_window
    def _():
        maid.kill_process('Canva.exe')

    # Rule 2: Stop the related service when the GameViewer.exe process exits
    GameViewer = maid.attend('GameViewer.exe')
    @GameViewer.is_exited
    def _():
        maid.stop_service('GameViewerService')

    # Rule 3: Kill CrossDeviceResume.exe when the process is running
    CrossDeviceResume = maid.attend('CrossDeviceResume.exe')
    @CrossDeviceResume.is_running
    def _():
        maid.kill_process('CrossDeviceResume.exe')

    # Set log level and start monitoring
    maid.set_log_level('INFO')
    maid.start()
```

Then run it:

```bash
python my_rules.py
```

## Deployment: Packaging as a Background Service

To achieve a true "background standby" and auto-start on boot, it is recommended to use **Nuitka** to package your rule script into a standalone `.exe` executable. Nuitka compiles the Python script into C code, generating an efficient, dependency-free program.

**Packaging Command:**

```bash
nuitka --standalone --include-data-dir=sysmaid/i18n=sysmaid/i18n --windows-uac-admin --windows-console-mode=disable your_rules.py
```

*   `--standalone`: Creates a standalone folder with all dependencies.
*   `--include-data-dir`: Packages the internationalization language files.
*   `--windows-uac-admin`: Requests administrator privileges, necessary for operations like stopping services.
*   `--windows-console-mode=disable`: Creates a windowless background application that won't show a black console window when run.
*   `your_rules.py`: Your rule script filename.

After successful packaging, you will find the generated `.exe` file in the `your_rules.dist` folder. You can place this file or its shortcut in the system's "Startup" folder to achieve auto-start on boot.

## Future Plans

SysMaid's goal is not just simple process management. We hope to develop it into the most comprehensive **AutoRun ecosystem** on Windows, including but not limited to:

*   Richer trigger conditions (e.g., network activity, CPU/memory usage).
*   More diverse response actions (e.g., modifying the registry, file operations).
*   Providing a graphical user interface so that users unfamiliar with programming can also use it easily.
*   ...

## Contributing

All forms of contribution are welcome! If you have good ideas or find a bug, please feel free to submit an Issue or Pull Request. To capture logs, you can run it directly in Python, ensuring the logging level is set to `INFO` or higher.

<a href="https://github.com/RooCodeInc/Roo-Code">
<img height="32" src="https://github.com/user-attachments/assets/b963732e-8cb2-42c0-a398-d80768a7f86f"></img>
</a>

## License

This project is open-sourced under the [GPLv3 License](LICENSE).
