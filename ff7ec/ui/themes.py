"""
Modern FlatLaf & Material UI Theme Engine
Curated color palettes and dynamic ttk / tk widget styler for desktop GUI.
"""

from typing import Dict, Any

THEMES: Dict[str, Dict[str, Any]] = {
    "Material Dark": {
        "bg": "#121212", "fg": "#e0e0e0", "muted_fg": "#9e9e9e", "border": "#333333",
        "entry_bg": "#252526", "entry_fg": "#ffffff", "btn_bg": "#2c2c2c", "btn_fg": "#ffffff",
        "btn_border": "#3f3f3f", "btn_hover": "#383838", "btn_pressed": "#1a1a1a",
        "btn_disabled_bg": "#1a1a1a", "btn_disabled_fg": "#555555",
        "accent": "#00b4d8", "accent_hover": "#0096c7", "accent_fg": "#ffffff",
        "trough": "#2a2a2a", "log_bg": "#141414", "log_fg": "#e0e0e0",
        "log_info": "#80d4ff", "log_success": "#52b788", "log_warning": "#ffb703", "log_error": "#ff595e",
    },
    "Material Light": {
        "bg": "#f5f5f7", "fg": "#212121", "muted_fg": "#616161", "border": "#d1d5db",
        "entry_bg": "#ffffff", "entry_fg": "#212121", "btn_bg": "#e5e7eb", "btn_fg": "#1f2937",
        "btn_border": "#cbd5e1", "btn_hover": "#d1d5db", "btn_pressed": "#9ca3af",
        "btn_disabled_bg": "#f3f4f6", "btn_disabled_fg": "#9ca3af",
        "accent": "#1976d2", "accent_hover": "#1565c0", "accent_fg": "#ffffff",
        "trough": "#e0e0e0", "log_bg": "#ffffff", "log_fg": "#212121",
        "log_info": "#0288d1", "log_success": "#2e7d32", "log_warning": "#f57c00", "log_error": "#d32f2f",
    },
    "Atom One Dark": {
        "bg": "#21252b", "fg": "#abb2bf", "muted_fg": "#5c6370", "border": "#3e4451",
        "entry_bg": "#1e2227", "entry_fg": "#d7dae0", "btn_bg": "#353b45", "btn_fg": "#d7dae0",
        "btn_border": "#4b5263", "btn_hover": "#3e4451", "btn_pressed": "#282c34",
        "btn_disabled_bg": "#21252b", "btn_disabled_fg": "#5c6370",
        "accent": "#528bff", "accent_hover": "#4078f2", "accent_fg": "#ffffff",
        "trough": "#1e2227", "log_bg": "#1e2227", "log_fg": "#abb2bf",
        "log_info": "#61afef", "log_success": "#98c379", "log_warning": "#e5c07b", "log_error": "#e06c75",
    },
    "Carbon (Flat Dark)": {
        "bg": "#2b2b2b", "fg": "#a9b7c6", "muted_fg": "#808080", "border": "#4e5254",
        "entry_bg": "#3c3f41", "entry_fg": "#bbbbbb", "btn_bg": "#4c5052", "btn_fg": "#dfdfdf",
        "btn_border": "#5c6164", "btn_hover": "#565a5c", "btn_pressed": "#3c3f41",
        "btn_disabled_bg": "#313335", "btn_disabled_fg": "#666666",
        "accent": "#e5a50a", "accent_hover": "#c68e08", "accent_fg": "#2b2b2b",
        "trough": "#2b2b2b", "log_bg": "#232525", "log_fg": "#a9b7c6",
        "log_info": "#6897bb", "log_success": "#629755", "log_warning": "#bbb529", "log_error": "#cc666e",
    },
    "Arc Dark": {
        "bg": "#2f343f", "fg": "#d3dae3", "muted_fg": "#8a95a5", "border": "#404552",
        "entry_bg": "#282c37", "entry_fg": "#cfd6e6", "btn_bg": "#434857", "btn_fg": "#e4e8f0",
        "btn_border": "#4b5162", "btn_hover": "#4d5363", "btn_pressed": "#2f343f",
        "btn_disabled_bg": "#2b303c", "btn_disabled_fg": "#6b7382",
        "accent": "#5294e2", "accent_hover": "#4185d8", "accent_fg": "#ffffff",
        "trough": "#282c37", "log_bg": "#252932", "log_fg": "#cfd6e6",
        "log_info": "#5294e2", "log_success": "#70c08b", "log_warning": "#ebcb8b", "log_error": "#e06c75",
    },
    "Nord (Arctic Frost)": {
        "bg": "#2e3440", "fg": "#eceff4", "muted_fg": "#9099a8", "border": "#4c566a",
        "entry_bg": "#272c36", "entry_fg": "#e5e9f0", "btn_bg": "#434c5e", "btn_fg": "#e5e9f0",
        "btn_border": "#4c566a", "btn_hover": "#4c566a", "btn_pressed": "#2e3440",
        "btn_disabled_bg": "#2e3440", "btn_disabled_fg": "#616e85",
        "accent": "#88c0d0", "accent_hover": "#81a1c1", "accent_fg": "#2e3440",
        "trough": "#272c36", "log_bg": "#242933", "log_fg": "#eceff4",
        "log_info": "#88c0d0", "log_success": "#a3be8c", "log_warning": "#ebcb8b", "log_error": "#bf616a",
    },
    "Cyberpunk Midnight": {
        "bg": "#0d1117", "fg": "#c9d1d9", "muted_fg": "#7d8590", "border": "#30363d",
        "entry_bg": "#090d13", "entry_fg": "#e6edf3", "btn_bg": "#21262d", "btn_fg": "#f0f6fc",
        "btn_border": "#363b42", "btn_hover": "#30363d", "btn_pressed": "#161b22",
        "btn_disabled_bg": "#11151c", "btn_disabled_fg": "#484f58",
        "accent": "#00f0ff", "accent_hover": "#00d4e3", "accent_fg": "#0d1117",
        "trough": "#090d13", "log_bg": "#080b0f", "log_fg": "#c9d1d9",
        "log_info": "#58a6ff", "log_success": "#3fb950", "log_warning": "#d29922", "log_error": "#f85149",
    },
    "Flat Minimal Light": {
        "bg": "#f8f9fa", "fg": "#212529", "muted_fg": "#6c757d", "border": "#dee2e6",
        "entry_bg": "#ffffff", "entry_fg": "#212529", "btn_bg": "#e9ecef", "btn_fg": "#212529",
        "btn_border": "#ced4da", "btn_hover": "#dee2e6", "btn_pressed": "#ced4da",
        "btn_disabled_bg": "#f1f3f5", "btn_disabled_fg": "#adb5bd",
        "accent": "#0d6efd", "accent_hover": "#0b5ed7", "accent_fg": "#ffffff",
        "trough": "#e9ecef", "log_bg": "#ffffff", "log_fg": "#212529",
        "log_info": "#0d6efd", "log_success": "#198754", "log_warning": "#fd7e14", "log_error": "#dc3545",
    },
    "Dracula (Vibrant Dark)": {
        "bg": "#282a36", "fg": "#f8f8f2", "muted_fg": "#6272a4", "border": "#44475a",
        "entry_bg": "#21222c", "entry_fg": "#f8f8f2", "btn_bg": "#44475a", "btn_fg": "#f8f8f2",
        "btn_border": "#6272a4", "btn_hover": "#50556c", "btn_pressed": "#282a36",
        "btn_disabled_bg": "#21222c", "btn_disabled_fg": "#6272a4",
        "accent": "#bd93f9", "accent_hover": "#a372eb", "accent_fg": "#282a36",
        "trough": "#21222c", "log_bg": "#1e1f29", "log_fg": "#f8f8f2",
        "log_info": "#8be9fd", "log_success": "#50fa7b", "log_warning": "#ffb86c", "log_error": "#ff5555",
    },
}


class ThemeManager:
    """Applies themes dynamically across all Tk and ttk widgets in real time."""

    @classmethod
    def apply_theme(
        cls,
        theme_name: str,
        root,
        style,
        main_frame,
        lbl_title,
        lbl_sub,
        lbl_status,
        txt_log,
    ) -> None:
        """Configures all ttk styles and Tk text widgets to reflect the chosen theme."""
        t = THEMES.get(theme_name, THEMES["Material Dark"])
        root.configure(bg=t["bg"])
        main_frame.configure(style="TFrame")

        # Base style config
        style.configure(".", background=t["bg"], foreground=t["fg"])
        style.configure("TFrame", background=t["bg"])

        # LabelFrame
        style.configure("TLabelframe", background=t["bg"], bordercolor=t["border"])
        style.configure("TLabelframe.Label", background=t["bg"], foreground=t["accent"], font=("Segoe UI", 9, "bold"))

        # Labels
        style.configure("TLabel", background=t["bg"], foreground=t["fg"], font=("Segoe UI", 9))
        lbl_title.configure(foreground=t["accent"])
        lbl_sub.configure(foreground=t["muted_fg"])
        lbl_status.configure(foreground=t["fg"])

        # Standard Buttons
        style.configure(
            "TButton",
            background=t["btn_bg"],
            foreground=t["btn_fg"],
            bordercolor=t["btn_border"],
            focuscolor=t["accent"],
            relief="flat",
            padding=(8, 4),
            font=("Segoe UI", 9),
        )
        style.map(
            "TButton",
            background=[("pressed", t["btn_pressed"]), ("active", t["btn_hover"]), ("disabled", t["btn_disabled_bg"])],
            foreground=[("disabled", t["btn_disabled_fg"]), ("active", t["btn_fg"])],
            bordercolor=[("active", t["accent"]), ("disabled", t["border"])],
        )

        # Accent Button (Primary Action - Start Extraction)
        style.configure(
            "Accent.TButton",
            background=t["accent"],
            foreground=t["accent_fg"],
            bordercolor=t["accent_hover"],
            focuscolor=t["accent_hover"],
            relief="flat",
            padding=(8, 4),
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("pressed", t["accent_hover"]), ("active", t["accent_hover"]), ("disabled", t["btn_disabled_bg"])],
            foreground=[("disabled", t["btn_disabled_fg"]), ("active", t["accent_fg"])],
            bordercolor=[("active", t["accent"]), ("disabled", t["border"])],
        )

        # Entries
        style.configure(
            "TEntry",
            fieldbackground=t["entry_bg"],
            foreground=t["entry_fg"],
            insertcolor=t["fg"],
            bordercolor=t["border"],
            padding=(4, 2),
        )
        style.map("TEntry", bordercolor=[("focus", t["accent"])], lightcolor=[("focus", t["accent"])])

        # Comboboxes
        style.configure(
            "TCombobox",
            fieldbackground=t["entry_bg"],
            foreground=t["entry_fg"],
            background=t["btn_bg"],
            arrowcolor=t["fg"],
            bordercolor=t["border"],
            padding=(4, 2),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", t["entry_bg"])],
            foreground=[("readonly", t["entry_fg"])],
            bordercolor=[("focus", t["accent"])],
        )
        root.option_add("*TCombobox*Listbox.background", t["entry_bg"])
        root.option_add("*TCombobox*Listbox.foreground", t["entry_fg"])
        root.option_add("*TCombobox*Listbox.selectBackground", t["accent"])
        root.option_add("*TCombobox*Listbox.selectForeground", t["accent_fg"])

        # Spinbox
        style.configure(
            "TSpinbox",
            fieldbackground=t["entry_bg"],
            foreground=t["entry_fg"],
            background=t["btn_bg"],
            arrowcolor=t["fg"],
            bordercolor=t["border"],
        )

        # Checkbutton
        style.configure("TCheckbutton", background=t["bg"], foreground=t["fg"], focuscolor=t["bg"])
        style.map(
            "TCheckbutton",
            indicatorcolor=[("selected", t["accent"]), ("!selected", t["entry_bg"])],
            indicatorbackground=[("selected", t["accent"]), ("!selected", t["entry_bg"])],
        )

        # Progressbar
        style.configure("Horizontal.TProgressbar", background=t["accent"], troughcolor=t["trough"], bordercolor=t["border"])

        # Log ScrolledText & Highlighting Tags
        txt_log.configure(
            bg=t["log_bg"],
            fg=t["log_fg"],
            insertbackground=t["log_fg"],
            selectbackground=t["accent"],
            selectforeground=t["accent_fg"],
        )
        txt_log.tag_config("INFO", foreground=t["log_info"])
        txt_log.tag_config("SUCCESS", foreground=t["log_success"])
        txt_log.tag_config("WARNING", foreground=t["log_warning"])
        txt_log.tag_config("ERROR", foreground=t["log_error"])
