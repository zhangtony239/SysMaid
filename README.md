# SysMaid
[English](https://github.com/zhangtony239/SysMaid/blob/main/README_en.md)

**SysMaid** 是一个为 Windows 设计的高阶 `win32 api` 抽象层，允许用户通过编写简单的 Python 脚本来管理和优化系统行为。它就像一个进程管理界的 uBlock Origin，旨在解决那些“不得不用的软件”所存在的后台滥用问题，并致力于成为 Windows 下最全面的 AutoRun 生态系统。
<br /><br />

#### 下载的文件不见了？

由于 SysMaid 的行为涉及系统级的进程监控和操作，某些杀毒软件（如 Windows Defender）可能会将其误报为潜在威胁。为了确保程序正常运行，强烈建议将您的脚本、打包后的 `.exe` 文件或其所在目录添加到杀毒软件的白名单中。

## 核心功能

*   **简洁的规则定义**：通过 Python 装饰器，直观地定义监控规则。
*   **进程和服务监控**：轻松监控指定进程的状态，如窗口是否存在、进程是否退出等。
*   **自动化操作**：在满足条件时自动执行操作，例如结束进程、停止服务、锁定加密卷等。
*   **可扩展性**：可以轻松添加新的条件和操作，以适应更复杂的需求。


## 快速开始

### 安装

```bash
pip install sysmaid
```

### 使用

创建一个 Python 文件（例如 `my_rules.py`），并添加你的规则：

```python
import sysmaid as maid

if __name__ == "__main__":
    # 规则1：当 Canva.exe 进程存在但没有窗口时，结束它
    Canva = maid.attend('Canva.exe')
    @Canva.has_no_window
    def _():
        maid.kill_process('Canva.exe')

    # 规则2：当 GameViewer.exe 进程退出时，停止相关的服务
    GameViewer = maid.attend('GameViewer.exe')
    @GameViewer.is_exited
    def _():
        maid.stop_service('GameViewerService')

    # 规则3：当 CrossDeviceResume.exe 进程运行时，结束它
    CrossDeviceResume = maid.attend('CrossDeviceResume.exe')
    @CrossDeviceResume.is_running
    def _():
        maid.kill_process('CrossDeviceResume.exe')

    # 规则4：当退出 Macrium Reflect 备份软件时，自动锁定备份盘（D盘）
    # (需确保 D 盘已启用 BitLocker)
    Reflect = maid.attend('Reflect.exe')
    @Reflect.is_exited
    def _():
        maid.lock_volume('D')

    # 设置日志级别并启动监控
    maid.set_log_level('INFO')
    maid.start()
```

然后运行它：

```bash
python my_rules.py
```

## 部署：打包为后台服务

为了实现真正的“后台待命”和开机自启，推荐使用 **Nuitka** 将您的规则脚本打包成一个独立的 `.exe` 可执行文件。Nuitka 会将 Python 脚本编译成 C 代码，生成一个高效、无依赖的程序。

**安装 Nuitka：**

```bash
pip install nuitka
```

**打包指令：**

```bash
nuitka --standalone --windows-uac-admin --windows-console-mode=disable your_rules.py
```

*   `--standalone`: 创建一个包含所有依赖的独立文件夹。
*   `--windows-uac-admin`: 请求管理员权限，这是停止服务等操作所必需的。
*   `--windows-console-mode=disable`: 创建一个无窗口的后台应用，运行时不会弹出黑色的控制台窗口。
*   `your_rules.py`: 你的规则脚本文件名。

打包成功后，你会在 `your_rules.dist` 文件夹中找到生成的 `.exe` 文件。你可以将这个文件或其快捷方式放入系统的“启动”文件夹，即可实现开机自启。

## 未来规划

SysMaid 的目标不止于简单的进程管理。我们希望将其发展成为 Windows 下最全面的 **AutoRun 生态**，包括但不限于：

*   更丰富的触发条件（如网络活动、CPU/内存占用等）。
*   更多样的响应操作（如修改注册表、文件操作等）。
*   提供图形用户界面，让不熟悉编程的用户也能轻松使用。
*   ……

## 贡献

欢迎任何形式的贡献！如果你有好的想法或发现了 Bug，请随时提交 Issue 或 Pull Request。想要抓取日志，可以使用python状态直接运行，确保日志记录级别在 `INFO` 以上。

<a href="https://roocode.com/">
<img height="32" src="https://github.com/user-attachments/assets/b963732e-8cb2-42c0-a398-d80768a7f86f"></img>
</a>

## 许可证

本项目基于 [GPLv3 License](https://github.com/zhangtony239/SysMaid/blob/main/LICENSE) 开源。
