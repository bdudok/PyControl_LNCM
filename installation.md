# Installation

The pyControl GUI runs in its own uv environment (Python 3.11, PyQt6), defined by `pyproject.toml` and
`uv.lock` in this repo. `uv sync` creates it in `.venv` in this folder.

**It does not use the Recorder's environment.** The two apps run as separate processes and talk only through
zmq, so each repo needs its own `uv sync`. The Recorder's `.venv` can't run this GUI: it has PySide6 and no
PyQt6 or pyqtgraph. pyControl uses `QtCore.pyqtSignal`, which exists only in PyQt, so keep it on PyQt6.

Commands are for PowerShell on Windows.

## Install

If `uv --version` doesn't work, install uv, then reopen PowerShell:

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Get the code and build the environment. uv downloads Python 3.11 by itself when needed.

```
git clone https://github.com/bdudok/PyControl.git
cd PyControl
git switch pycontrol-v2.1.1
uv sync
```

The branch is not merged yet; after that, `git switch` won't be needed. `uv sync` also installs the packages
for `tools/` (pandas, matplotlib, scikit-learn).

Check it:

```
uv run python -c "import PyQt6, pyqtgraph, serial, zmq; print('ok')"
```

## Run

Always start the GUI from the PyControl folder. The default folders and `config\settings.json` are found
relative to the current directory.

```
cd PyControl
uv run python pyControl_GUI.pyw
```

`uv run` picks this repo's `.venv` from the folder, even if another environment is active in the shell.

For daily use without a console window, run `.venv\Scripts\pythonw.exe pyControl_GUI.pyw`. A desktop shortcut
works, with "Start in" set to the PyControl folder.

If no window opens, read `ErrorLog.txt` in this folder. When a dependency is missing, which is what happens
with the wrong interpreter, the launcher writes the error there and exits silently.

In PyCharm, use `.venv\Scripts\python.exe` from this repo as the project interpreter, and set the working
directory of the run configuration to this folder.

## First-time setup

- Settings (gear icon): check the tasks and data folders. They are saved in `config\settings.json`, which is
  not in git. `config\user_settings.json` is an old file; this version doesn't read it.
- Load the framework onto each pyboard. Select the board and press Connect; the log warns if the framework
  on the board doesn't match the GUI. Use Config → Load framework, wait for "OK", then disconnect and
  connect again. The warning should be gone.
- If Windows Firewall asks about Python, allow it on private networks. The Recorder connects from the same
  PC, so blocking it would also work.

## Use with the Recorder

The GUI listens for the Recorder on port 5556, set in `pyControl_GUI.pyw`. Start the two apps separately,
each from its own folder. Upload the task, then press Arm in the "Synchronous recording" box. The GUI answers
the Recorder only while armed.

## Update

```
git pull
uv sync
```

Run `uv sync` after every pull: it applies any change in `uv.lock`, and does nothing otherwise. When the
framework version changes, load it onto the boards again.
