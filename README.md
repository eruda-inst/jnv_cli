# JNV - Jacobina Network Viewer

Curses-based terminal UI for browsing OLT slots and PONs and inspecting ONU/PON alarms on Datacom (SSH) and Fiberhome (Telnet) OLTs.

## How to run

1. Install uv (package and project manger for Python)

- On MacOS/Linux

```sh
# With wget
wget -qO- https://astral.sh/uv/install.sh | sh

# With curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

- On Windows

```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. Clone the repository

```sh
git clone https://github.com/eruda-inst/jnv_cli.git
```

3. Access the directory

```sh
cd jnv_cli
```

4. Install dependencies

```sh
uv sync
```

5. Run

```sh
uv run jnv
```
