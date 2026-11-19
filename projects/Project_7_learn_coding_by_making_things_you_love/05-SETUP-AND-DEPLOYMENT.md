# 05 · Setup and deployment

## Option A: Docker (recommended)

Install **Docker Desktop**, then in the project folder:

```bash
docker compose up --build
```

Open **http://localhost:8000**. The first build downloads the .NET SDK image and installs Python, g++ and Java (5–15 minutes with internet). Later starts take seconds.

Stop with `Ctrl+C`, or run in the background:

```bash
docker compose up -d     # start in the background
docker compose down      # stop
```

### What the image contains

| Item | Why |
|---|---|
| `mcr.microsoft.com/dotnet/sdk:8.0` | C# and the base OS |
| `python3`, `g++`, `default-jdk-headless` | Python, C++17, Java |
| User `quest` (non-root) | Learner code never runs as root |
| Pre-built C# project | The first C# run is fast |

### Container limits (`compose.yaml`)

| Setting | Value |
|---|---|
| Port | `127.0.0.1:8000:8000` (this computer only) |
| Memory | 1 GB |
| CPUs | 2 |
| Processes | 256 |
| Capabilities | all dropped |
| Privileges | `no-new-privileges` |
| Restart | `unless-stopped` |

## Option B: Without Docker

Needs Python 3.8+. For other languages install .NET SDK 8+, `g++` or `clang++`, and Java 17+.

```bash
python server.py
```

Missing languages show "not installed: read-only" and the rest still work.

Flags: `--port 8000`, `--bind 127.0.0.1`, and `--lan` (let other devices on your Wi-Fi connect, see Security).

## Shipping to another Windows laptop

### Easiest: the zip and the `.bat` files
1. Install **Docker Desktop** on the target laptop and open it once (accept WSL 2 if asked).
2. Unzip the project to a folder such as `C:\CodeQuest`.
3. Double-click **`Start-CodeQuest.bat`**. It builds, starts and opens the browser.
4. **`Stop-CodeQuest.bat`** stops it.

Tip: tick "Start Docker Desktop when you sign in" so Code Quest restarts itself.

### Offline copy (no build on the target)
On your machine:

```bash
docker build -t codequest .
docker save codequest | gzip > codequest.tar.gz
```

On the target (PowerShell, without gzip use `docker save -o codequest.tar codequest`):

```bash
docker load -i codequest.tar.gz
docker run -d --restart unless-stopped -p 127.0.0.1:8000:8000 \
  --memory 1g --pids-limit 256 --cap-drop ALL \
  --security-opt no-new-privileges --name codequest codequest
```

## iPad or phone at home (optional)

Not enabled by default. Without Docker run `python server.py --lan`. With Docker, change the port line in `compose.yaml` to `"8000:8000"` and add `"--lan"` to the `CMD` in the `Dockerfile`. Then open `http://<laptop-ip>:8000` on the same Wi-Fi. **Anyone on that network could run code on the laptop**, so use it only on a trusted home network.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Cannot connect to the Docker daemon" | Open Docker Desktop and wait for "Engine running" |
| Port 8000 already in use | Change `127.0.0.1:8000:8000` to `127.0.0.1:8080:8000` in `compose.yaml`, open `http://localhost:8080` |
| First C# run is slow or fails | Check the Docker build finished; the project is pre-built into the image |
| Stories say "offline pick" | The laptop has no internet, or a feed has moved; the app still works |
| Progress disappeared | Progress is stored per browser; use the same browser and profile |
| Keyboard input does nothing in Unity | Edit > Project Settings > Player > Active Input Handling → **Both** |

## Security

- Code Quest **runs whatever code the learner types**. That is the whole point, and also the risk.
- In Docker it is isolated and limited, and reachable only from the same computer.
- `--lan` opens it to the local network, so use it only at home.
- **Do not expose this server to the public internet.** A public version needs a real sandbox (see the [roadmap](09-ROADMAP.md)).
- Progress is stored in the browser only; no accounts, no personal data on a server.
