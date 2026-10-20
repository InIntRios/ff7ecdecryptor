# FF7EC Asset Decryptor & Media Converter

> **All-in-One Asset Decryptor, Extractor, Audio Decoder & Video Transcoder for *Final Fantasy VII: Ever Crisis***

[![Release](https://img.shields.io/badge/Release-v2.1.0-blue.svg)](https://github.com/InIntRios/ff7ecdecryptor/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue.svg)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📑 Table of Contents

1. [Overview & Key Features](#-overview--key-features)
2. [Prerequisites & Python Setup](#-prerequisites--python-setup)
3. [External Dependencies (crid_mod, vgmstream, ffmpeg)](#-external-dependencies)
4. [Building the Asset Mapping Database (octocacheevai.json)](#-building-the-asset-mapping-database)
5. [User Guide](#-user-guide)
   - [GUI Mode (Graphical User Interface)](#1-gui-mode-graphical-user-interface)
   - [CLI Mode (Command Line Interface)](#2-cli-mode-command-line-interface)
6. [Building Standalone Executable (.exe)](#-building-standalone-executable-exe)
7. [Output Directory Structure](#-output-directory-structure)
8. [Original Research Notes](#-original-research-notes)
9. [License & Disclaimer](#-license--disclaimer)

---

## ✨ Overview & Key Features

`FF7EC Asset Decryptor` is an all-in-one suite designed to decrypt, unpack, demux, and transcode all game assets from **Final Fantasy VII: Ever Crisis** on PC (Steam) as well as offline emulators (NeverCrisis).

- ⚡ **High-Performance Vectorized Decryption:** Implements the Applibot engine XOR cipher using 64-bit vectorized bitwise operations in Python, achieving **15x–20x faster speeds** over standard byte-by-byte loops.
- 🛡️ **100% Read-Only Safety:** Completely non-destructive. Never writes to, modifies, or deletes any files in your original game installation.
- 📂 **Smart Game Folder Detection:** Point directly to the root game directory (`.../FF7EC`). The tool automatically discovers and resolves the internal asset path (`octo\v1`).
- 🌐 **Pure-Python Database Generator:** Downloads and generates `octocacheevai.json` (over 112,000 asset bundles and 5,200 resources) directly in native Python via Protobuf decoding, with zero external dependencies.
- 🔄 **NeverCrisis Offline Server Support:** Includes built-in network timeout handling (8 seconds). If the official API is unavailable, the tool automatically detects `FF7ECServer.exe`, prompts the user, and can launch the offline server seamlessly.
- 🎬 **Complete USM Video Pipeline:** Demuxes CRI USM cutscenes with 64-bit split decryption keys (`000011DA` / `4DE45ADE`), extracts embedded original filenames from headers (e.g. `story_ac_001.mp4`, `gacha_weapon_49007s.mp4`), and muxes synchronized audio/video into clean MP4 or WebM containers.
- 🎨 **Material UI & Multi-Theme Engine:** Integrated FlatLaf-style dynamic theme switcher with 9 curated themes: **Material Dark**, **Material Light**, **Atom One Dark**, **Carbon (Flat Dark)**, **Arc Dark**, **Nord (Arctic Frost)**, **Cyberpunk Midnight**, **Flat Minimal Light**, and **Dracula**. Instantly switchable at runtime with auto-persistence.
- 🖼️ **Native Windows Taskbar & High-Res Icon Integration:** Explicit Windows `AppUserModelID` association with embedded multi-resolution icon (256x256 PNG + DIBs) ensuring crisp taskbar and titlebar display.
- 🖥️ **Dual Interface:** Feature-rich, modern Graphical User Interface (Tkinter) and a versatile Command Line Interface (CLI) for scripting and automation.

---

## 🐍 Prerequisites & Python Setup

### 1. Operating System
- Windows 10 or Windows 11 (64-bit).

### 2. Python Installation
- Download and install **Python 3.10 or newer** from [python.org](https://www.python.org/downloads/).
- **Important:** Ensure you check the box **"Add Python to PATH"** during setup.

### 3. Dependencies & Libraries
- The application core (`ff7ec_decryptor.py`) relies **100% on the Python Standard Library** (`urllib`, `ssl`, `gzip`, `threading`, `tkinter`, `subprocess`, `argparse`, etc.).
- **Zero third-party pip dependencies are required to run the script!**

*(Note: If you plan to compile the script into a standalone `.exe`, you only need `pyinstaller`, detailed in the [Build Executable section](#-building-standalone-executable-exe)).*

---

## 🛠️ External Dependencies

To transcode USM video cutscenes and decode CRIWARE audio banks, the application utilizes three helper binaries located in the `tools/` folder (relative to the script or `.exe`):

| Tool | Purpose | Source / Installation |
| :--- | :--- | :--- |
| **`crid_mod.exe`** | CRI USM video demuxer & decrypter | Located in `tools/crid_mod.exe` |
| **`vgmstream-cli.exe`** | CRIWARE ACB/AWB audio bank decoder | Automatically downloaded via `check-tools` |
| **`ffmpeg.exe`** | Video & audio transcoder and muxer | Discovered from system `PATH` or placed in `tools/ffmpeg.exe` |

### Automatic Tool Verification & Download:
Simply double-click **`setup_tools.bat`** (or run via command line):

```powershell
.\setup_tools.bat
```
*(Or run via python directly: `python ff7ec_decryptor.py check-tools`)*

---

## 🗄️ Building the Asset Mapping Database (`octocacheevai.json`)

The `octocacheevai.json` database maps encrypted MD5 asset hashes into human-readable logical asset paths and original game filenames (e.g., character models, textures, animations, cutscenes).

### Option A: Via GUI
1. Open the application.
2. In the **Mapping JSON (Database)** row, click **`⚡ Build Database`**.
3. The tool queries the resources API, decodes the Protobuf payload, and writes `data/octo/octocacheevai.json` (~49 MB).

> **Offline Mode (NeverCrisis Server):**  
> If external internet is unavailable or connections time out (8 seconds), the tool checks if NeverCrisis offline server (`FF7ECServer.exe`) is running. If not, it presents a helpful dialog:
> ```
> Could not connect to the database server (Connection timed out or failed).
> If you are playing offline with NeverCrisis, the offline server must be running.
> Detected NeverCrisis server at: ...\FF7ECServer.exe
> Would you like to start FF7ECServer.exe now?
> ```
> Clicking **Yes** automatically starts `FF7ECServer.exe` in its own console window.

### Option B: Via Command Line (CLI)
```powershell
python ff7ec_decryptor.py build-mapping
```

---

## 🚀 User Guide

### 1. GUI Mode (Graphical User Interface)

Launch the interface by double-clicking **`FF7EC_Decryptor.exe`** or running:
```powershell
python ff7ec_decryptor.py
```

#### Step-by-Step Workflow:
1. **🎨 Choose Theme:** Switch between 9 modern Material/Flat themes anytime via the top-right `Theme` dropdown (`Material Dark`, `Material Light`, `Atom One Dark`, `Carbon`, `Arc Dark`, `Nord`, `Cyberpunk`, etc.). Your preference is automatically saved.
2. **Game Folder (FF7EC):** Click `Browse...` and select your game root folder (e.g. `C:\Program Files (x86)\Steam\steamapps\common\FF7EC` or `D:\SteamLibrary\steamapps\common\FF7EC`). The tool **automatically detects and resolves the internal `octo\v1` asset folder**. Click **`🔍 Scan Keys`** anytime to audit engine integrity, IL2CPP metadata, and decryption keys.
3. **Output Folder:** Select your extraction destination (Default: `C:\FF7EC_Decrypted_Assets`).
4. **Mapping JSON:** If not populated, click **`⚡ Build Database`** to generate it directly via game API.
5. **Extraction Scope & Concurrency:**
   - Filter by `All Assets`, `Video Only`, `Audio Only`, or `Bundles Only`.
   - Video Format: `mp4` or `webm`.
   - Audio Format: `mp3`, `flac` (Lossless), or `wav`.
   - Worker Threads: Set concurrent parallel threads (auto-configured to your CPU cores).
6. **Execution & Navigation:**
   - **Row 1 (Controls):** Click **`▶ Start Extraction (Scope)`**, or use direct shortcuts **`🎬 Extract Videos Only`** or **`🎵 Extract Audio Only`**.
   - **Row 2 (Shortcuts & Utility):** Instant folder shortcuts (`📁 Open Output Root`, `🎬 Open Videos Folder`, `🎵 Open Audio Folder`) and **`🧹 Clear Log`** (generously padded to avoid clipping).

---

### 2. CLI Mode (Command Line Interface)

Display the complete CLI documentation:
```powershell
python ff7ec_decryptor.py --help
```

#### Common Commands:

- **Audit & Scan Game Engine & Decryption Keys:**
  ```powershell
  python ff7ec_decryptor.py scan-keys --source "D:\SteamLibrary\steamapps\common\FF7EC"
  ```

- **Batch Extraction (Full Process):**
  ```powershell
  python ff7ec_decryptor.py batch --source "C:\Program Files (x86)\Steam\steamapps\common\FF7EC" --output "C:\FF7EC_Decrypted_Assets"
  ```

- **Extract Cutscene Videos Only:**
  ```powershell
  python ff7ec_decryptor.py extract-videos --source "C:\Program Files (x86)\Steam\steamapps\common\FF7EC" --output "C:\FF7EC_Decrypted_Assets" --format mp4
  ```

- **Extract Audio Only:**
  ```powershell
  python ff7ec_decryptor.py extract-audio --source "C:\Program Files (x86)\Steam\steamapps\common\FF7EC" --output "C:\FF7EC_Decrypted_Assets" --format flac
  ```

- **Extract Audio Tracks from USM Cutscenes:**
  ```powershell
  python ff7ec_decryptor.py extract-usm-audio --output "C:\FF7EC_Decrypted_Assets" --format mp3
  ```

- **Post-Process Existing Videos (Without re-scanning game source):**
  ```powershell
  python ff7ec_decryptor.py convert-videos --output "C:\FF7EC_Decrypted_Assets" --format mp4
  ```

- **Post-Process Existing Audio:**
  ```powershell
  python ff7ec_decryptor.py convert-audio --output "C:\FF7EC_Decrypted_Assets" --format mp3
  ```

- **Single File Test:**
  ```powershell
  python ff7ec_decryptor.py single <input_file> <output_file> <asset_mask>
  ```

---

## 📦 Building Standalone Executable (.exe)

You can package the entire Python script into a single standalone `.exe` with embedded icon extracted from `FF7EC.exe`:

### Method A: One-Click Build (.bat)
Simply double-click or run:
```powershell
.\build_exe.bat
```
This batch script automatically:
1. Verifies Python 3.10+ and installs/updates `pyinstaller` if missing.
2. Extracts high-resolution multi-size icons directly from `FF7EC.exe` into `app.ico`.
3. Compiles `FF7EC_Decryptor.exe` with `FF7EC_Decryptor.spec` (UPX disabled, Windows version info and manifest embedded).

### Method B: Manual PyInstaller Build
```powershell
python -m PyInstaller --noconfirm --clean FF7EC_Decryptor.spec
```

---

## 📁 Output Directory Structure

Extracted files are neatly structured and separated into dedicated folders:

```text
C:\FF7EC_Decrypted_Assets\
├── converted_videos\     # Final MP4 / WebM cutscene videos with synchronized audio
│   ├── story_ac_001.mp4
│   └── gacha_weapon_49007s.mp4
├── converted_audio\      # Converted BGM, SFX, and Voice files (MP3 / FLAC / WAV)
│   ├── bgm_battle_01.mp3
│   └── se_system_01.mp3
├── bundles\              # Decrypted UnityFS AssetBundles (open directly with AssetStudio)
│   ├── character\
│   └── weapon\
├── videos\               # Raw demuxed USM files
└── audio_criware\        # Raw CRIWARE wavebanks (.acb / .awb)
```

---

## 🔬 Original Research Notes

*(Reference notes preserved from original reverse-engineering research by shalzuth)*

### High-Level Analysis
To understand how to retrieve assets and communicate over the network:
1. **App Binary Inspection:**
   - Unity app containing `libil2cpp.so`.
   - `global-metadata.bin` is XOR encrypted.
2. **Network & File Serialization:**
   - Protobuf & MessagePack serialization structures.
   - Applibot XOR cipher uses initial mask `0xAB` (adapted from NieR Re[in]carnation).
3. **Network Traffic:**
   - REST API over TCP with headers (`X-OCTO-KEY`, `User-Agent`).
   - Payloads compressed with Gzip.
4. **Native Decryption Workflow:**
   - Online asset mapping downloaded via `octocacheevai.bin` / `octocacheevai.json`.
   - Direct decryption and extraction of assets without APK unpacking.

---

## ⚖️ License & Disclaimer

- **License:** [MIT License](LICENSE).
- **Disclaimer:** This project is developed for educational and personal research purposes only. *Final Fantasy VII: Ever Crisis* is a trademark and copyright of SQUARE ENIX CO., LTD. and Applibot Inc. This project is not affiliated with, endorsed by, or associated with Square Enix or Applibot.
