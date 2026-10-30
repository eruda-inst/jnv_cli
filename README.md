# JNV - Jacobina Network Viewer

Curses-based terminal UI for browsing OLT slots and PONs and inspecting ONU/PON alarms on Datacom (SSH) and Fiberhome (Telnet) OLTs.

## How to run

1. **Install `uv` (package and project manger for Python)**

- On MacOS/Linux

```sh
# With wget
wget -qO- https://astral.sh/uv/install.sh | sh

# With curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After that, restart your terminal/console (close and reopen it).

- On Windows

```sh
# This is supposed to work for both CMD and PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After that, restart your CMD/PowerShell (close and reopen it).

2. **Install `git`**

- On MacOS/Linux

```sh
sudo apt install git --yes
```

- On Windows

Access: [https://git-scm.com/install/windows](https://git-scm.com/install/windows).

2. **Clone the repository**

```sh
git clone https://github.com/eruda-inst/jnv_cli.git
```

3. **Access the directory**

```sh
cd jnv_cli
```

4. **Set up a `.env` file**

Inside `jnv_cli` directory, create a file named `.env` (make sure the file is named exactly like that, without `.txt` at the end, for example) with the following content:

```sh
OLT_ACIJA_HOSTNAME="..."
OLT_ITAITU_HOSTNAME="..."
OLT_JAC_3_HOSTNAME="..."
OLT_LAJES_HOSTNAME="..."
OLT_NEWNET_HOSTNAME="..."
OLT_PALMEIRINHA_HOSTNAME="..."
OLT_PARAISO_HOSTNAME="..."

OLT_DEFAULT_USERNAME="..."
OLT_DEFAULT_PASSWORD="..."

OLT_FIBERHOME_DEFAULT_USERNAME="..."
OLT_FIBERHOME_DEFAULT_PASSWORD="..."
```

Replace the placeholders (ellipses) with real data.

5. **Install dependencies**

```sh
uv sync
```

6. **Run**

```sh
uv run jnv_cli
```
