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

Double-click `pyControl.bat`, or use a desktop shortcut (see below). It finds this repo's `.venv` by itself
and works from any folder.

To see errors in a console instead, start the GUI from the PyControl folder. It has to be this folder: the
default folders and `config\settings.json` are found relative to the current directory.

```
cd PyControl
uv run python pyControl_GUI.pyw
```

If no window opens, read `ErrorLog.txt` in this folder. When a dependency is missing, which is what happens
with the wrong interpreter, the launcher writes the error there and exits silently.

## Desktop shortcuts

On the Bruker PC, pyControl, the Recorder and the camera run at the same time, each from its own bat file and
each in its own environment. Run `uv sync` in both the PyControl and the Recorder folder first.

| App | Bat file | Window |
|---|---|---|
| pyControl GUI | `PyControl\pyControl.bat` | no console; messages are in the GUI's log |
| Recorder | `Recorder\Recorder.bat` | console that shows the Recorder's messages |
| Camera | `Recorder\CamGUI.bat` | console that shows the camera's messages |

For each bat file:

1. In File Explorer, right-click the file, then Show more options (Windows 11) → Send to → Desktop (create
   shortcut).
2. Rename the shortcut on the desktop, for example to "pyControl". The default name ends in " - Shortcut".
3. Recorder and camera only, optional: right-click the shortcut → Properties → Run: Minimized, so the console
   starts out of the way.

Keep the two console windows open while recording: closing one stops that app. Check them when something
fails, because some messages appear only there. If an app fails at startup, its console stays open and shows
the error until you press a key.

`Recorder.bat` needs LNCM-lib checked out next to the Recorder folder, for `BaserowAPI`. `Recorder\token.py`
is not in git and has to be there too.

## Editing tasks in PyCharm

The GUIs don't need PyCharm, so no run configurations or per-app interpreters are needed. Open the PyControl
folder as its own project:

1. Settings → Project → Python Interpreter → Add Interpreter → Add Local Interpreter → Select existing, type
   Python, path `.venv\Scripts\python.exe` in this repo. Use this rather than the uv type, which is less
   reliable for an environment that already exists.
2. Right-click the `source` folder → Mark Directory as → Sources Root. This resolves `pyControl.utility` in
   the task files; `devices` resolves from the project root.

Tasks run on the pyboard, not in this environment, so upload them from the GUI. PyCharm will still mark `pyb`
and `hardware_definition` as unresolved, because they exist only on the board.

uv environments have no pip or setuptools, so PyCharm may report that packaging tools or setuptools are
missing. Dismiss it and don't install them from PyCharm. Packages are managed in `pyproject.toml` and
`uv.lock`, and everything the apps need is in the environment.

## First-time setup

- Settings (gear icon): check the tasks and data folders. They are saved in `config\settings.json`, which is
  not in git. `config\user_settings.json` is an old file; this version doesn't read it.
- Load the framework onto each pyboard. Select the board and press Connect; the log warns if the framework
  on the board doesn't match the GUI. Use Config → Load framework, wait for "OK", then disconnect and
  connect again. The warning should be gone.
- If Windows Firewall asks about Python, allow it on private networks. The Recorder connects from the same
  PC, so blocking it would also work.

## Use with the Recorder

The GUI listens for the Recorder on port 5556, set in `pyControl_GUI.pyw`. Upload the task, then press Arm in
the "Synchronous recording" box. The GUI answers the Recorder only while armed.

## Update

```
git pull
uv sync
```

Run `uv sync` after every pull: it applies any change in `uv.lock`, and does nothing otherwise. When the
framework version changes, load it onto the boards again.
