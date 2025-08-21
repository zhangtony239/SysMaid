# SysMaid

**SysMaid** 是一个为 Windows 设计的高阶 `win32 api` 抽象层，允许用户通过编写简单的 Python 脚本来管理和优化系统行为。它就像一个本地的 uBlock Origin，但专注于进程管理，旨在解决那些“不得不用的”后台软件问题，并致力于成为 Windows 下最全面的 AutoRun 生态系统。

## 核心功能

*   **简洁的规则定义**：通过 Python 装饰器，直观地定义监控规则。
*   **进程和服务监控**：轻松监控指定进程的状态，如窗口是否存在、进程是否退出等。
*   **自动化操作**：在满足条件时自动执行操作，例如结束进程或停止服务。
*   **可扩展性**：可以轻松添加新的条件和操作，以适应更复杂的需求。


## 一键启动

欢迎大家提交pull request共同构建Tony.py这个rules版本：让它成为一个大而全的拦截规则。从而在本仓库的release中，只需要下载我nuitka好的exe就能直接获得一个更干净的系统环境。

## 从头开始

### 安装

```bash
pip install -r requirements.txt
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

**打包指令：**

```bash
nuitka --standalone --include-data-dir=sysmaid/i18n=sysmaid/i18n --windows-uac-admin --windows-console-mode=disable your_rules.py
```

*   `--standalone`: 创建一个包含所有依赖的独立文件夹。
*   `--include-data-dir`: 将国际化语言文件打包进去。
*   `--windows-uac-admin`: 请求管理员权限，这是停止服务等操作所必需的。
*   `--windows-console-mode=disable`: 创建一个无窗口的后台应用，运行时不会弹出黑色的控制台窗口。
*   `your_rules.py`: 你的规则脚本文件名。

打包成功后，你会在 `your_rules.dist` 文件夹中找到生成的 `.exe` 文件。你可以将这个文件或其快捷方式放入系统的“启动”文件夹，即可实现开机自启。

## 未来规划

SysMaid 的目标不止于简单的进程管理。我们希望将其发展成为 Windows 下最全面的 **AutoRun 生态**，包括但不限于：

*   更丰富的触发条件（如网络活动、CPU/内存占用等）。
*   更多样的响应操作（如修改注册表、文件操作等）。
*   一个社区驱动的规则仓库，用户可以分享和下载针对不同软件的优化脚本。
*   提供图形用户界面，让不熟悉编程的用户也能轻松使用。

## 贡献

欢迎任何形式的贡献！如果你有好的想法或发现了 Bug，请随时提交 Issue 或 Pull Request。想要抓取日志，可以使用python状态直接运行，确保日志记录级别在 `INFO` 以上。

<a href="https://github.com/RooCodeInc/Roo-Code">
<img height="32" src="https://github.com/user-attachments/assets/b963732e-8cb2-42c0-a398-d80768a7f86f"></img>
</a>

## 许可证

本项目基于 [GPLv3 License](LICENSE) 开源。
