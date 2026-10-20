"""
Modern Graphical User Interface (Tkinter / FlatLaf Style)
Main window, path grid, transcoding settings, execution controls, and execution log console.
"""

import os
import sys
import threading
import logging
from typing import Optional

from ff7ec.constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_SCOPE,
    DEFAULT_VIDEO_FORMAT,
    DEFAULT_AUDIO_FORMAT,
    DEFAULT_WORKER_THREADS,
    MIN_WORKER_THREADS,
    MAX_WORKER_THREADS,
    SUPPORTED_VIDEO_FORMATS,
    SUPPORTED_AUDIO_FORMATS,
    SCOPE_DISPLAY_TO_VAL,
    SCOPE_VAL_TO_DISPLAY,
    SCOPE_VIDEO_ONLY,
    SCOPE_AUDIO_ONLY,
    SCOPE_BUNDLES_ONLY,
    SUBDIR_CONVERTED_VIDEOS,
    SUBDIR_CONVERTED_AUDIO,
)
from ff7ec.config.manager import (
    load_config,
    save_config,
    get_app_icon_path,
    get_initial_mapping_path,
)
from ff7ec.common.logger import setup_logger
from ff7ec.tools.locator import ToolManager
from ff7ec.mapping.database import build_mapping_database
from ff7ec.scanner.engine_scanner import scan_game_engine_and_keys, format_scan_report
from ff7ec.engine.batch import run_batch_process
from ff7ec.media.postprocess import (
    convert_existing_videos_only,
    convert_existing_audio_only,
    extract_audio_from_videos_only,
)
from ff7ec.ui.themes import THEMES, ThemeManager


def launch_gui():
    """Initializes and runs the graphical user interface."""
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from tkinter.scrolledtext import ScrolledText

    config = load_config()

    root = tk.Tk()
    root.title(f"{APP_NAME} v{APP_VERSION}")
    root.geometry(config.get("window_geometry", "1040x800+100+60"))
    root.minsize(900, 700)

    # Set Windows Titlebar & Taskbar Icons
    ico_path = get_app_icon_path()
    if ico_path and os.path.exists(ico_path):
        try:
            root.iconbitmap(default=ico_path)
        except Exception:
            try:
                root.iconbitmap(ico_path)
            except Exception:
                pass

        if sys.platform == "win32":
            try:
                import ctypes
                root.update_idletasks()
                hwnd = ctypes.windll.user32.GetAncestor(root.winfo_id(), 2) or root.winfo_id()
                IMAGE_ICON = 1
                LR_LOADFROMFILE = 0x00000010
                LR_DEFAULTSIZE = 0x00000040
                h_icon_big = ctypes.windll.user32.LoadImageW(
                    None, os.path.abspath(ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
                )
                h_icon_small = ctypes.windll.user32.LoadImageW(
                    None, os.path.abspath(ico_path), IMAGE_ICON, 16, 16, LR_LOADFROMFILE
                )
                WM_SETICON = 0x0080
                if h_icon_small:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 0, h_icon_small)
                if h_icon_big:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 1, h_icon_big)
            except Exception:
                pass

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    stop_event = threading.Event()
    pause_event = threading.Event()
    pause_event.set()
    worker_thread = None

    var_source = tk.StringVar(value=config.get("source_dir", ""))
    var_output = tk.StringVar(value=config.get("output_dir", ""))
    var_mapping = tk.StringVar(value=config.get("mapping_path", ""))
    var_crid = tk.StringVar(value=config.get("crid_mod_path", ""))
    var_vgmstream = tk.StringVar(value=config.get("vgmstream_path", ""))

    var_conv_video = tk.BooleanVar(value=config.get("convert_video", True))
    var_conv_audio = tk.BooleanVar(value=config.get("convert_audio", True))
    var_video_format = tk.StringVar(value=config.get("video_format", DEFAULT_VIDEO_FORMAT))
    var_audio_format = tk.StringVar(value=config.get("audio_format", DEFAULT_AUDIO_FORMAT))

    var_threads = tk.IntVar(value=config.get("worker_threads", DEFAULT_WORKER_THREADS))
    var_resume = tk.BooleanVar(value=config.get("resume_mode", True))

    cur_scope = config.get("extract_scope", DEFAULT_SCOPE)
    var_scope_display = tk.StringVar(value=SCOPE_VAL_TO_DISPLAY.get(cur_scope, SCOPE_VAL_TO_DISPLAY[DEFAULT_SCOPE]))

    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Header Frame (Title & Subtitle on Left, Theme Switcher on Right)
    f_header = ttk.Frame(main_frame)
    f_header.pack(fill=tk.X, pady=(0, 6))

    f_header_left = ttk.Frame(f_header)
    f_header_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    lbl_title = ttk.Label(f_header_left, text=APP_NAME, font=("Segoe UI", 13, "bold"))
    lbl_title.pack(anchor="w", pady=(0, 2))

    lbl_sub = ttk.Label(
        f_header_left,
        text="High-Performance Parallel Decryptor & Media Transcoder for Final Fantasy VII: Ever Crisis",
        font=("Segoe UI", 9),
    )
    lbl_sub.pack(anchor="w")

    f_header_right = ttk.Frame(f_header)
    f_header_right.pack(side=tk.RIGHT, anchor="e")

    ttk.Label(f_header_right, text="🎨 Theme:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
    cur_theme = config.get("ui_theme", "Material Dark")
    if cur_theme not in THEMES:
        cur_theme = "Material Dark"
    var_theme = tk.StringVar(value=cur_theme)
    cb_theme = ttk.Combobox(
        f_header_right,
        textvariable=var_theme,
        values=list(THEMES.keys()),
        state="readonly",
        width=22,
    )
    cb_theme.pack(side=tk.LEFT)

    # SECTION 1: Paths & Files Configuration
    grp_paths = ttk.LabelFrame(main_frame, text=" File & Folder Configurations ", padding="8")
    grp_paths.pack(fill=tk.X, pady=(0, 6))
    grp_paths.columnconfigure(1, weight=1)

    def _create_browse_btn(row_idx, str_var, browse_type="dir"):
        def _browse():
            if browse_type == "dir":
                d = filedialog.askdirectory(initialdir=str_var.get())
                if d:
                    str_var.set(os.path.normpath(d))
            elif browse_type == "open_file":
                f = filedialog.askopenfilename()
                if f:
                    str_var.set(os.path.normpath(f))
            elif browse_type == "json_file":
                f = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
                if f:
                    str_var.set(os.path.normpath(f))

        btn = ttk.Button(grp_paths, text="Browse...", width=10, command=_browse)
        btn.grid(row=row_idx, column=2, padx=(4, 2), pady=2, sticky="ew")
        return btn

    # Row 0: Game Folder (FF7EC)
    ttk.Label(grp_paths, text="Game Folder (FF7EC):", width=24, anchor="w").grid(row=0, column=0, padx=4, pady=2, sticky="w")
    entry_src = ttk.Entry(grp_paths, textvariable=var_source)
    entry_src.grid(row=0, column=1, padx=4, pady=2, sticky="ew")
    _create_browse_btn(0, var_source, "dir")

    def _gui_scan_keys():
        def _worker():
            rep = scan_game_engine_and_keys(var_source.get(), logger=logger)
            rep_text = format_scan_report(rep)
            logger.info("\n" + rep_text)
            root.after(0, lambda: messagebox.showinfo("Game Engine & Decryption Keys", rep_text))
        threading.Thread(target=_worker, daemon=True).start()

    btn_scan_keys = ttk.Button(grp_paths, text="🔍 Scan Keys", width=16, command=_gui_scan_keys)
    btn_scan_keys.grid(row=0, column=3, padx=(2, 4), pady=2, sticky="ew")

    # Row 1: Output Folder (Root Dest)
    ttk.Label(grp_paths, text="Output Folder (Root Dest):", width=24, anchor="w").grid(row=1, column=0, padx=4, pady=2, sticky="w")
    entry_out = ttk.Entry(grp_paths, textvariable=var_output)
    entry_out.grid(row=1, column=1, padx=4, pady=2, sticky="ew")
    _create_browse_btn(1, var_output, "dir")

    # Row 2: Mapping JSON (Database)
    ttk.Label(grp_paths, text="Mapping JSON (Database):", width=24, anchor="w").grid(row=2, column=0, padx=4, pady=2, sticky="w")
    entry_map = ttk.Entry(grp_paths, textvariable=var_mapping)
    entry_map.grid(row=2, column=1, padx=4, pady=2, sticky="ew")
    _create_browse_btn(2, var_mapping, "json_file")

    btn_build_map = None

    def _build_map_native():
        nonlocal btn_build_map
        if btn_build_map:
            btn_build_map.config(text="⏳ Building...", state=tk.DISABLED)

        def _worker():
            try:
                logger.info("Fetching and building octocacheevai.json database via API...")
                hint_dir = var_source.get().strip() or None
                found, b_cnt, r_cnt = build_mapping_database(game_hint_dir=hint_dir, timeout_sec=8, logger=logger)
                if found:
                    var_mapping.set(found)
                    config["mapping_path"] = found
                    save_config(config)
                    root.after(0, lambda: messagebox.showinfo(
                        "Database Built",
                        f"Successfully generated octocacheevai.json database!\n\n"
                        f"• Saved To: {found}\n"
                        f"• Asset Bundles: {b_cnt:,}\n"
                        f"• Resources: {r_cnt:,}\n\n"
                        f"Mapping is now active for high-speed named asset extraction!"
                    ))
                else:
                    root.after(0, lambda: messagebox.showerror(
                        "Build Failed",
                        "Could not generate database via API.\n"
                        "Please check your internet connection or verify offline server is running."
                    ))
            except Exception as ex:
                root.after(0, lambda: messagebox.showerror("Build Error", f"Exception during database build:\n{ex}"))
            finally:
                if btn_build_map:
                    root.after(0, lambda: btn_build_map.config(text="⚡ Build Database", state=tk.NORMAL))

        threading.Thread(target=_worker, daemon=True).start()

    btn_build_map = ttk.Button(grp_paths, text="⚡ Build Database", width=16, command=_build_map_native)
    btn_build_map.grid(row=2, column=3, padx=(2, 4), pady=2, sticky="ew")

    # Row 3: crid_mod.exe Path
    ttk.Label(grp_paths, text="crid_mod.exe Path:", width=24, anchor="w").grid(row=3, column=0, padx=4, pady=2, sticky="w")
    entry_crid = ttk.Entry(grp_paths, textvariable=var_crid)
    entry_crid.grid(row=3, column=1, padx=4, pady=2, sticky="ew")
    _create_browse_btn(3, var_crid, "open_file")

    # SECTION 2: Transcoding & Concurrency Settings
    grp_options = ttk.LabelFrame(main_frame, text=" Transcoding & Concurrency Settings ", padding="8")
    grp_options.pack(fill=tk.X, pady=(0, 6))

    f_opt_line1 = ttk.Frame(grp_options)
    f_opt_line1.pack(fill=tk.X, pady=(0, 4))

    chk_vid = ttk.Checkbutton(f_opt_line1, text="Convert Videos", variable=var_conv_video)
    chk_vid.pack(side=tk.LEFT, padx=(0, 4))

    ttk.Label(f_opt_line1, text="Format:").pack(side=tk.LEFT, padx=(0, 2))
    cb_video = ttk.Combobox(f_opt_line1, textvariable=var_video_format, values=SUPPORTED_VIDEO_FORMATS, state="readonly", width=7)
    cb_video.pack(side=tk.LEFT, padx=(0, 16))

    chk_aud = ttk.Checkbutton(f_opt_line1, text="Convert Audio (ACB/AWB)", variable=var_conv_audio)
    chk_aud.pack(side=tk.LEFT, padx=(0, 4))

    ttk.Label(f_opt_line1, text="Format:").pack(side=tk.LEFT, padx=(0, 2))
    cb_audio = ttk.Combobox(f_opt_line1, textvariable=var_audio_format, values=SUPPORTED_AUDIO_FORMATS, state="readonly", width=7)
    cb_audio.pack(side=tk.LEFT, padx=(0, 16))

    ttk.Label(f_opt_line1, text="Threads:").pack(side=tk.LEFT, padx=(0, 4))
    sp_threads = ttk.Spinbox(f_opt_line1, from_=MIN_WORKER_THREADS, to=MAX_WORKER_THREADS, textvariable=var_threads, width=5)
    sp_threads.pack(side=tk.LEFT, padx=(0, 16))

    chk_res = ttk.Checkbutton(f_opt_line1, text="Skip existing (Resume)", variable=var_resume)
    chk_res.pack(side=tk.LEFT, padx=(0, 8))

    def on_check_tools():
        c_p, f_p, v_p = ToolManager.ensure_tools(logger, auto_download=True)
        if c_p and os.path.exists(c_p):
            var_crid.set(c_p)
        if v_p and os.path.exists(v_p):
            var_vgmstream.set(v_p)
        msg = f"- crid_mod.exe:     {'READY (' + c_p + ')' if c_p else 'NOT FOUND'}\n"
        msg += f"- vgmstream-cli:   {'READY (' + v_p + ')' if v_p else 'NOT FOUND'}\n"
        msg += f"- ffmpeg.exe:       {'READY (' + f_p + ')' if f_p else 'NOT FOUND'}"
        messagebox.showinfo("Tool Dependencies Status", msg)

    btn_tools_check = ttk.Button(f_opt_line1, text="🛠 Check / Setup Tools", command=on_check_tools)
    btn_tools_check.pack(side=tk.RIGHT)

    # Extraction Scope line
    f_opt_line2 = ttk.Frame(grp_options)
    f_opt_line2.pack(fill=tk.X, pady=(2, 0))

    ttk.Label(f_opt_line2, text="Extraction Scope:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    cb_scope = ttk.Combobox(
        f_opt_line2,
        textvariable=var_scope_display,
        values=list(SCOPE_DISPLAY_TO_VAL.keys()),
        state="readonly",
        width=44,
    )
    cb_scope.pack(side=tk.LEFT, padx=(0, 16))
    ttk.Label(f_opt_line2, text="Filter: All Assets, Video Only, Audio Only, or Bundles Only.", font=("Segoe UI", 8, "italic")).pack(side=tk.LEFT)

    # SECTION 3: Post-Processing Actions (Separate destination folders)
    grp_post = ttk.LabelFrame(main_frame, text=" Post-Processing & Quick Actions ", padding="8")
    grp_post.pack(fill=tk.X, pady=(0, 6))

    f_post_btns = ttk.Frame(grp_post)
    f_post_btns.pack(fill=tk.X)

    btn_conv_exist_video = ttk.Button(f_post_btns, text="🎬 Convert Existing Videos (.usm ➔ converted_videos/)")
    btn_conv_exist_video.pack(side=tk.LEFT, padx=(0, 6), ipady=2)

    btn_conv_exist_audio = ttk.Button(f_post_btns, text="🎵 Convert Existing Audio (.acb/.awb/.wav ➔ converted_audio/)")
    btn_conv_exist_audio.pack(side=tk.LEFT, padx=(0, 6), ipady=2)

    btn_ext_usm_audio = ttk.Button(f_post_btns, text="🔊 Extract Audio from USMs (.usm ➔ converted_audio/)")
    btn_ext_usm_audio.pack(side=tk.LEFT, padx=(0, 6), ipady=2)

    # SECTION 4: Controls & Progress
    # Row 1: Execution Control Bar
    f_ctrl_1 = ttk.Frame(main_frame)
    f_ctrl_1.pack(fill=tk.X, pady=(0, 4))

    btn_start = ttk.Button(f_ctrl_1, text="▶  Start Extraction (Scope)", style="Accent.TButton")
    btn_start.pack(side=tk.LEFT, padx=(0, 6), ipady=3)

    btn_ext_vid = ttk.Button(f_ctrl_1, text="🎬 Extract Videos Only")
    btn_ext_vid.pack(side=tk.LEFT, padx=(0, 6), ipady=3)

    btn_ext_aud = ttk.Button(f_ctrl_1, text="🎵 Extract Audio Only")
    btn_ext_aud.pack(side=tk.LEFT, padx=(0, 6), ipady=3)

    btn_pause = ttk.Button(f_ctrl_1, text="⏸  Pause", state=tk.DISABLED)
    btn_pause.pack(side=tk.LEFT, padx=(0, 6), ipady=3)

    btn_stop = ttk.Button(f_ctrl_1, text="⏹  Stop", state=tk.DISABLED)
    btn_stop.pack(side=tk.LEFT, padx=(0, 6), ipady=3)

    # Row 2: Navigation Shortcuts & Clear Log Utility Bar
    f_ctrl_2 = ttk.Frame(main_frame)
    f_ctrl_2.pack(fill=tk.X, pady=(0, 6))

    def on_open_output():
        out = var_output.get()
        if os.path.exists(out):
            os.startfile(out)
        else:
            messagebox.showinfo("Information", f"Output directory does not exist yet:\n{out}")

    def on_open_converted_videos():
        v_dir = os.path.join(var_output.get(), SUBDIR_CONVERTED_VIDEOS)
        if os.path.exists(v_dir):
            os.startfile(v_dir)
        else:
            messagebox.showinfo("Information", f"Converted videos folder does not exist yet:\n{v_dir}")

    def on_open_converted_audio():
        a_dir = os.path.join(var_output.get(), SUBDIR_CONVERTED_AUDIO)
        if os.path.exists(a_dir):
            os.startfile(a_dir)
        else:
            messagebox.showinfo("Information", f"Converted audio folder does not exist yet:\n{a_dir}")

    btn_open_out = ttk.Button(f_ctrl_2, text="📁 Open Output Root", command=on_open_output)
    btn_open_out.pack(side=tk.LEFT, padx=(0, 6), ipady=2)

    btn_open_vid = ttk.Button(f_ctrl_2, text="🎬 Open Videos Folder", command=on_open_converted_videos)
    btn_open_vid.pack(side=tk.LEFT, padx=(0, 6), ipady=2)

    btn_open_aud = ttk.Button(f_ctrl_2, text="🎵 Open Audio Folder", command=on_open_converted_audio)
    btn_open_aud.pack(side=tk.LEFT, padx=(0, 6), ipady=2)

    btn_clear_log = ttk.Button(f_ctrl_2, text="🧹 Clear Log")
    btn_clear_log.pack(side=tk.RIGHT, padx=(6, 0), ipady=2)

    # Progress bar and status label
    f_prog = ttk.Frame(main_frame)
    f_prog.pack(fill=tk.X, pady=(0, 4))

    prog_bar = ttk.Progressbar(f_prog, orient="horizontal", mode="determinate")
    prog_bar.pack(fill=tk.X, pady=(0, 2))

    lbl_status = ttk.Label(f_prog, text="Ready. Click 'Start Batch Extraction' or select a Post-Processing action.", font=("Segoe UI", 9))
    lbl_status.pack(anchor="w")

    # SECTION 5: Log Console
    grp_log = ttk.LabelFrame(main_frame, text=" Execution Log ", padding="4")
    grp_log.pack(fill=tk.BOTH, expand=True)

    txt_log = ScrolledText(grp_log, wrap=tk.WORD, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
    txt_log.pack(fill=tk.BOTH, expand=True)

    def apply_current_theme(theme_name: str):
        ThemeManager.apply_theme(
            theme_name=theme_name,
            root=root,
            style=style,
            main_frame=main_frame,
            lbl_title=lbl_title,
            lbl_sub=lbl_sub,
            lbl_status=lbl_status,
            txt_log=txt_log,
        )

    def on_theme_change(event=None):
        selected_theme = var_theme.get()
        apply_current_theme(selected_theme)
        config["ui_theme"] = selected_theme
        save_config(config)

    cb_theme.bind("<<ComboboxSelected>>", on_theme_change)
    apply_current_theme(cur_theme)

    def append_log(level, msg):
        def _do():
            txt_log.insert(tk.END, msg + "\n", level)
            txt_log.see(tk.END)
        root.after(0, _do)

    btn_clear_log.config(command=lambda: txt_log.delete("1.0", tk.END))

    logger = setup_logger(callback=append_log)

    c_found, f_found, v_found = ToolManager.ensure_tools(logger, auto_download=False)
    if c_found and not var_crid.get():
        var_crid.set(c_found)
    if v_found and not var_vgmstream.get():
        var_vgmstream.set(v_found)

    def on_scan_progress(count: int, total_bytes: int):
        def _do():
            size_gb = total_bytes / (1024 ** 3)
            lbl_status.config(
                text=f"Step 1/2: Scanning asset directory... {count:,} files found ({size_gb:.2f} GB)"
            )
        root.after(0, _do)

    def update_progress(curr, total, success, skipped):
        def _do():
            if str(prog_bar.cget("mode")) != "determinate":
                prog_bar.stop()
                prog_bar.config(mode="determinate")
            prog_bar["maximum"] = max(1, total)
            prog_bar["value"] = curr
            pct = (curr / total * 100) if total > 0 else 0
            lbl_status.config(
                text=f"Step 2/2: Progress: {curr:,}/{total:,} ({pct:.1f}%) | Success: {success:,} | Skipped: {skipped:,}"
            )
        root.after(0, _do)

    def set_buttons_running(running: bool):
        def _do():
            if not running and str(prog_bar.cget("mode")) == "indeterminate":
                prog_bar.stop()
                prog_bar.config(mode="determinate")
            state_run = tk.DISABLED if running else tk.NORMAL
            state_active = tk.NORMAL if running else tk.DISABLED
            btn_start.config(state=state_run)
            btn_ext_vid.config(state=state_run)
            btn_ext_aud.config(state=state_run)
            btn_conv_exist_video.config(state=state_run)
            btn_conv_exist_audio.config(state=state_run)
            btn_ext_usm_audio.config(state=state_run)
            btn_pause.config(state=state_active, text="⏸  Pause")
            btn_stop.config(state=state_active)
            if btn_scan_keys:
                btn_scan_keys.config(state=state_run)
            if btn_build_map:
                btn_build_map.config(state=state_run)
        root.after(0, _do)

    def toggle_pause():
        if pause_event.is_set():
            pause_event.clear()
            if str(prog_bar.cget("mode")) == "indeterminate":
                prog_bar.stop()
            btn_pause.config(text="▶  Resume")
            lbl_status.config(text="Process PAUSED. Click 'Resume' to continue.")
            append_log("WARNING", "[!] Process PAUSED by user.")
        else:
            pause_event.set()
            if str(prog_bar.cget("mode")) == "indeterminate":
                prog_bar.start(10)
            btn_pause.config(text="⏸  Pause")
            lbl_status.config(text="Process RESUMED.")
            append_log("INFO", "[+] Process RESUMED.")

    btn_pause.config(command=toggle_pause)

    # 1. Action: Batch Extraction
    def start_batch_worker(forced_scope=None):
        nonlocal worker_thread
        src = var_source.get().strip()
        out = var_output.get().strip()
        mapping = var_mapping.get().strip()
        crid = var_crid.get().strip()
        vgm = var_vgmstream.get().strip()
        conv_vid = var_conv_video.get()
        conv_aud = var_conv_audio.get()
        vid_fmt = var_video_format.get().strip()
        aud_fmt = var_audio_format.get().strip()
        threads = max(MIN_WORKER_THREADS, min(MAX_WORKER_THREADS, var_threads.get()))
        res = var_resume.get()

        if forced_scope:
            scope_val = forced_scope
            if forced_scope == SCOPE_VIDEO_ONLY:
                conv_vid = True
                conv_aud = False
            elif forced_scope == SCOPE_AUDIO_ONLY:
                conv_vid = False
                conv_aud = True
            elif forced_scope == SCOPE_BUNDLES_ONLY:
                conv_vid = False
                conv_aud = False
        else:
            scope_val = SCOPE_DISPLAY_TO_VAL.get(var_scope_display.get(), DEFAULT_SCOPE)
            if scope_val == SCOPE_VIDEO_ONLY:
                conv_aud = False
            elif scope_val == SCOPE_AUDIO_ONLY:
                conv_vid = False
            elif scope_val == SCOPE_BUNDLES_ONLY:
                conv_vid = False
                conv_aud = False

        if not os.path.exists(src):
            messagebox.showerror("Error", f"Source directory does not exist:\n{src}")
            return

        # Validate octocacheevai.json presence when extracting bundles
        if scope_val in (DEFAULT_SCOPE, SCOPE_BUNDLES_ONLY):
            has_valid_mapping = mapping and os.path.isfile(mapping) and os.path.getsize(mapping) > 0
            if not has_valid_mapping:
                auto_map = get_initial_mapping_path()
                if auto_map and os.path.isfile(auto_map) and os.path.getsize(auto_map) > 0:
                    mapping = auto_map
                    var_mapping.set(auto_map)
                    config["mapping_path"] = auto_map
                    save_config(config)
                    logger.info(f"Auto-detected asset mapping database: {auto_map}")
                else:
                    err_msg = (
                        "Missing 'octocacheevai.json' Database!\n\n"
                        "Cannot decrypt Asset Bundles (3D models, textures, animations) without 'octocacheevai.json'.\n"
                        "The Applibot XOR cipher requires the asset database to resolve decryption keys for each file.\n\n"
                        "Would you like to build and download the database via game API now?"
                    )
                    logger.error("================================================================================")
                    logger.error("[ERROR] Missing 'octocacheevai.json' database! Cannot decrypt Asset Bundles.")
                    logger.error("[ERROR] Please click '⚡ Build Database' or select a valid octocacheevai.json file.")
                    logger.error("================================================================================")
                    if messagebox.askyesno("Missing Database (octocacheevai.json)", err_msg):
                        _build_map_native()
                    return

        stop_event.clear()
        pause_event.set()
        set_buttons_running(True)
        prog_bar.config(mode="indeterminate")
        prog_bar.start(10)
        lbl_status.config(text="Step 1/2: Scanning source directory for asset files...")

        def _work():
            try:
                run_batch_process(
                    source_dir=src,
                    output_dir=out,
                    mapping_path=mapping,
                    crid_mod_path=crid,
                    vgmstream_path=vgm,
                    convert_video=conv_vid,
                    convert_audio=conv_aud,
                    video_format=vid_fmt,
                    audio_format=aud_fmt,
                    max_workers=threads,
                    resume=res,
                    extract_scope=scope_val,
                    logger=logger,
                    stop_event=stop_event,
                    pause_event=pause_event,
                    progress_callback=update_progress,
                    scan_progress_callback=on_scan_progress,
                )
            finally:
                set_buttons_running(False)

        worker_thread = threading.Thread(target=_work, daemon=True)
        worker_thread.start()

    def start_video_only_extraction():
        var_scope_display.set(SCOPE_VAL_TO_DISPLAY[SCOPE_VIDEO_ONLY])
        var_conv_video.set(True)
        start_batch_worker(forced_scope=SCOPE_VIDEO_ONLY)

    def start_audio_only_extraction():
        var_scope_display.set(SCOPE_VAL_TO_DISPLAY[SCOPE_AUDIO_ONLY])
        var_conv_audio.set(True)
        start_batch_worker(forced_scope=SCOPE_AUDIO_ONLY)

    # 2. Action: Post-Processing Videos Only
    def start_post_video_worker():
        nonlocal worker_thread
        out = var_output.get().strip()
        crid = var_crid.get().strip()
        vgm = var_vgmstream.get().strip()
        vid_fmt = var_video_format.get().strip()
        threads = max(MIN_WORKER_THREADS, min(MAX_WORKER_THREADS, var_threads.get()))

        if not os.path.exists(out):
            messagebox.showerror("Error", f"Output directory does not exist:\n{out}")
            return

        if not os.path.exists(crid):
            messagebox.showwarning("Warning", f"crid_mod.exe was not found at:\n{crid}\nPlease verify path.")
            return

        stop_event.clear()
        pause_event.set()
        set_buttons_running(True)
        prog_bar.config(mode="indeterminate")
        prog_bar.start(10)
        lbl_status.config(text="Scanning output directory for USM video cutscenes...")

        def _work():
            try:
                convert_existing_videos_only(
                    output_dir=out,
                    target_format=vid_fmt,
                    crid_mod_path=crid,
                    vgmstream_path=vgm,
                    max_workers=threads,
                    logger=logger,
                    stop_event=stop_event,
                    pause_event=pause_event,
                    progress_callback=update_progress,
                )
            finally:
                set_buttons_running(False)

        worker_thread = threading.Thread(target=_work, daemon=True)
        worker_thread.start()

    # 3. Action: Post-Processing Audio Only
    def start_post_audio_worker():
        nonlocal worker_thread
        out = var_output.get().strip()
        vgm = var_vgmstream.get().strip()
        aud_fmt = var_audio_format.get().strip()
        threads = max(MIN_WORKER_THREADS, min(MAX_WORKER_THREADS, var_threads.get()))

        if not os.path.exists(out):
            messagebox.showerror("Error", f"Output directory does not exist:\n{out}")
            return

        if not os.path.exists(vgm):
            c_p, f_p, v_p = ToolManager.ensure_tools(logger, auto_download=True)
            if v_p and os.path.exists(v_p):
                var_vgmstream.set(v_p)
                vgm = v_p
            else:
                messagebox.showerror("Error", "vgmstream-cli.exe is required for ACB/AWB decoding but was not found.")
                return

        stop_event.clear()
        pause_event.set()
        set_buttons_running(True)
        prog_bar.config(mode="indeterminate")
        prog_bar.start(10)
        lbl_status.config(text="Scanning output directory for audio banks (ACB/AWB)...")

        def _work():
            try:
                convert_existing_audio_only(
                    output_dir=out,
                    target_format=aud_fmt,
                    vgmstream_path=vgm,
                    max_workers=threads,
                    logger=logger,
                    stop_event=stop_event,
                    pause_event=pause_event,
                    progress_callback=update_progress,
                )
            finally:
                set_buttons_running(False)

        worker_thread = threading.Thread(target=_work, daemon=True)
        worker_thread.start()

    # 4. Action: Extract Audio Directly from USMs
    def start_post_usm_audio_worker():
        nonlocal worker_thread
        out = var_output.get().strip()
        crid = var_crid.get().strip()
        vgm = var_vgmstream.get().strip()
        aud_fmt = var_audio_format.get().strip()
        threads = max(MIN_WORKER_THREADS, min(MAX_WORKER_THREADS, var_threads.get()))

        if not os.path.exists(out):
            messagebox.showerror("Error", f"Output directory does not exist:\n{out}")
            return

        if not os.path.exists(crid):
            messagebox.showwarning("Warning", f"crid_mod.exe was not found at:\n{crid}\nPlease verify path.")
            return

        stop_event.clear()
        pause_event.set()
        set_buttons_running(True)
        prog_bar.config(mode="indeterminate")
        prog_bar.start(10)
        lbl_status.config(text="Scanning output directory for USM cutscenes to extract audio...")

        def _work():
            try:
                extract_audio_from_videos_only(
                    output_dir=out,
                    target_format=aud_fmt,
                    crid_mod_path=crid,
                    vgmstream_path=vgm,
                    max_workers=threads,
                    logger=logger,
                    stop_event=stop_event,
                    pause_event=pause_event,
                    progress_callback=update_progress,
                )
            finally:
                set_buttons_running(False)

        worker_thread = threading.Thread(target=_work, daemon=True)
        worker_thread.start()

    def stop_worker():
        stop_event.set()
        pause_event.set()
        append_log("WARNING", "[!] Stop signal sent to worker pool...")

    btn_start.config(command=lambda: start_batch_worker())
    btn_ext_vid.config(command=start_video_only_extraction)
    btn_ext_aud.config(command=start_audio_only_extraction)
    btn_conv_exist_video.config(command=start_post_video_worker)
    btn_conv_exist_audio.config(command=start_post_audio_worker)
    btn_ext_usm_audio.config(command=start_post_usm_audio_worker)
    btn_stop.config(command=stop_worker)

    def on_closing():
        geom = root.geometry()
        cfg_to_save = {
            "source_dir": var_source.get(),
            "output_dir": var_output.get(),
            "mapping_path": var_mapping.get(),
            "crid_mod_path": var_crid.get(),
            "vgmstream_path": var_vgmstream.get(),
            "convert_video": var_conv_video.get(),
            "convert_audio": var_conv_audio.get(),
            "video_format": var_video_format.get(),
            "audio_format": var_audio_format.get(),
            "extract_scope": SCOPE_DISPLAY_TO_VAL.get(var_scope_display.get(), DEFAULT_SCOPE),
            "worker_threads": var_threads.get(),
            "resume_mode": var_resume.get(),
            "ui_theme": var_theme.get(),
            "window_geometry": geom,
        }
        save_config(cfg_to_save)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
