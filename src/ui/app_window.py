"""
app_window.py
=============
Main application window for FreeDBC Editor & Previewer.

Layout
------
  ┌─────────────────────────────────────────────────────┐
  │  Toolbar  (Import · Save · Export XLSX · Export CSV) │
  ├───────────────────┬─────────────────────────────────┤
  │  Messages panel   │  Signals panel                   │
  │  (Treeview)       │  (Treeview)                      │
  ├───────────────────┴─────────────────────────────────┤
  │  Status bar                                          │
  └─────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

# Ensure src/ is on the path when running directly
_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from core.dbc_parser import DBCParser
from core.excel_exporter import ExcelExporter
from ui.edit_dialog import EditMessageDialog, EditSignalDialog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DARK_BG = "#1e1e1e"
_PANEL_BG = "#2b2b2b"
_SEL_BLUE = "#1f6aa5"
_GREEN = "#2d7a2d"
_GREEN_H = "#38963a"
_GREY = "#555555"
_GREY_H = "#666666"

# Light-mode equivalents for plain tk.Frame / tk.PanedWindow backgrounds.
# These widgets do NOT react to CTk's set_appearance_mode() automatically,
# so we store both variants and swap them manually inside _toggle_theme().
_LIGHT_BG = "#f5f5f5"
_LIGHT_PANEL_BG = "#e8e8e8"


def _apply_tree_style(dark: bool = True) -> None:
    """Configure ttk.Treeview to match the current CTk theme.

    Why: ttk.Treeview is a standard Tkinter widget — it does NOT react to
    customtkinter's appearance-mode changes automatically.  We must re-apply
    colours manually each time the theme is toggled, passing ``dark=True``
    for dark mode and ``dark=False`` for light mode.
    """
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Choose the full colour palette based on the requested mode
    if dark:
        bg = _PANEL_BG  # "#2b2b2b"
        fg = "#ffffff"
        hdr_bg = "#1a1a1a"
        hdr_fg = "#cccccc"
        act_hdr = "#333333"
        scrl_bg = _PANEL_BG
    else:
        bg = _LIGHT_PANEL_BG  # "#e8e8e8"
        fg = "#1a1a1a"
        hdr_bg = "#d0d0d0"
        hdr_fg = "#333333"
        act_hdr = "#bbbbbb"
        scrl_bg = _LIGHT_PANEL_BG

    style.configure(
        "Treeview",
        background=bg,
        foreground=fg,
        fieldbackground=bg,
        rowheight=26,
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Treeview.Heading",
        background=hdr_bg,
        foreground=hdr_fg,
        relief="flat",
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "Treeview",
        background=[("selected", _SEL_BLUE)],
        foreground=[("selected", "#ffffff")],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", act_hdr)],
    )
    style.configure("Vertical.TScrollbar", background=scrl_bg)
    style.configure("Horizontal.TScrollbar", background=scrl_bg)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------


class AppWindow:
    """Root application controller — owns the CTk root window."""

    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("FreeDBC Editor & Previewer")
        self.root.geometry("1360x820")
        self.root.minsize(900, 600)

        self.parser = DBCParser()
        self.current_message = None
        self._modified = False
        # Tracks the active theme: True = dark (default), False = light.
        # Always kept in sync with ctk.set_appearance_mode() calls in _toggle_theme().
        self._is_dark: bool = True

        _apply_tree_style(dark=True)  # apply initial dark styling to ttk.Treeview
        self._build_ui()
        self._bind_shortcuts()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self._build_toolbar()
        self._build_content()
        self._build_statusbar()

    # ---- Toolbar ---------------------------------------------------------

    def _build_toolbar(self) -> None:
        # fg_color tuple: (light_color, dark_color) — CTk automatically selects
        # the correct value whenever set_appearance_mode() is called at runtime.
        bar = ctk.CTkFrame(
            self.root, height=58, corner_radius=0, fg_color=("#dce3ed", "#16213e")
        )
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)

        # App title
        ctk.CTkLabel(
            bar,
            text="🔌 FreeDBC",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color="#4a9eff",
        ).pack(side="left", padx=(14, 0), pady=10)

        ctk.CTkLabel(
            bar,
            text="Editor & Previewer",
            font=ctk.CTkFont(size=13),
            # Slightly darker in light mode so the subtitle stays readable
            text_color=("#445577", "#8899bb"),
        ).pack(side="left", padx=(6, 18), pady=10)

        # Divider — tuple keeps it visible in both light and dark modes
        ctk.CTkFrame(bar, width=2, height=34, fg_color=("#bbccdd", "#334466")).pack(
            side="left", padx=6, pady=12
        )

        # Action buttons
        _BTN = {"width": 136, "height": 34, "corner_radius": 6}

        ctk.CTkButton(
            bar,
            text="📂  Import DBC",
            command=self.import_dbc,
            fg_color=_SEL_BLUE,
            hover_color="#2878c4",
            **_BTN,
        ).pack(side="left", padx=5, pady=12)

        ctk.CTkButton(
            bar,
            text="💾  Save DBC",
            command=self.save_dbc,
            fg_color=_GREEN,
            hover_color=_GREEN_H,
            **_BTN,
        ).pack(side="left", padx=5, pady=12)

        ctk.CTkButton(
            bar,
            text="📊  Export Excel",
            command=self.export_xlsx,
            fg_color="#7a5c2d",
            hover_color="#966e35",
            **_BTN,
        ).pack(side="left", padx=5, pady=12)

        ctk.CTkButton(
            bar,
            text="📄  Export CSV",
            command=self.export_csv,
            fg_color=_GREY,
            hover_color=_GREY_H,
            **_BTN,
        ).pack(side="left", padx=5, pady=12)

        # Right-side
        ctk.CTkButton(
            bar,
            text="❓  Help",
            command=self.show_help,
            fg_color="transparent",
            hover_color=("#c8d4e8", "#223366"),  # tuple for light/dark hover tint
            width=80,
            height=34,
        ).pack(side="right", padx=12, pady=12)

        # Theme toggle button — always shows what clicking WILL DO (the opposite mode).
        # In dark mode it reads "☀️ Light Mode"; in light mode it reads "🌙 Dark Mode".
        # Stored as self._theme_btn so _toggle_theme() can update its label on every press.
        #
        # Why fg_color tuple instead of "transparent":
        #   A transparent button has NO background fill, so in light mode it becomes
        #   invisible against the light toolbar (#dce3ed).  Giving each mode its own
        #   solid fill colour ensures the button is always readable and distinct from
        #   the toolbar regardless of which mode is active.
        #
        # Colour rationale:
        #   light fg  #b8cce0 — slightly deeper than the toolbar (#dce3ed) → visible depth
        #   dark  fg  #1e3a6e — slightly brighter than the toolbar (#16213e) → visible depth
        #   border adds an extra outline so the button edge is crisp in both modes
        self._theme_btn = ctk.CTkButton(
            bar,
            text="\u2600\ufe0f  Light Mode",  # dark is active at startup, so offer light
            command=self._toggle_theme,
            fg_color=("#b8cce0", "#1e3a6e"),  # solid fill — (light_bg, dark_bg)
            hover_color=("#9ab8d4", "#264a8e"),  # darker on hover for tactile feedback
            border_color=("#7a9ccc", "#4a6fa5"),  # crisp outline in both modes
            text_color=("#0d1f3c", "#c8d8f0"),  # dark text on light, light text on dark
            border_width=1,
            width=130,
            height=34,
            font=ctk.CTkFont(size=13),
        )
        self._theme_btn.pack(side="right", padx=(0, 4), pady=12)

    # ---- Content pane ----------------------------------------------------

    def _build_content(self) -> None:
        # Store the PanedWindow reference so _toggle_theme() can reconfigure its
        # bg colour — tk.PanedWindow is a plain Tkinter widget that ignores CTk
        # appearance-mode changes and must therefore be updated manually.
        self._paned = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            sashwidth=6,
            sashrelief="flat",
            bg=_DARK_BG,
        )
        self._paned.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        left = self._build_messages_panel(self._paned)
        right = self._build_signals_panel(self._paned)

        self._paned.add(left, minsize=260, width=360)
        self._paned.add(right, minsize=480)

    # ---- Messages panel --------------------------------------------------

    def _build_messages_panel(self, parent: tk.PanedWindow) -> tk.Frame:
        # Store the outer tk.Frame so _toggle_theme() can update its bg colour.
        # tk.Frame is a plain Tkinter widget — it does not auto-adapt to CTk themes.
        self._msg_frame = tk.Frame(parent, bg=_DARK_BG)
        frame = self._msg_frame

        # Header — fg_color tuple lets CTk pick the correct shade per mode
        hdr = ctk.CTkFrame(
            frame, height=38, corner_radius=6, fg_color=("#d5dde8", "#162032")
        )
        hdr.pack(fill="x", padx=0, pady=(0, 4))
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="📋  Messages", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=10)
        self._msg_count_lbl = ctk.CTkLabel(
            hdr, text="", text_color="#666666", font=ctk.CTkFont(size=11)
        )
        self._msg_count_lbl.pack(side="right", padx=10)

        # Search bar
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._filter_messages)
        ctk.CTkEntry(
            frame,
            textvariable=self._search_var,
            placeholder_text="🔍  Search messages…",
            height=30,
        ).pack(fill="x", padx=4, pady=(0, 4))

        # Store this inner frame reference too — its bg colour must also be
        # swapped manually because it is a plain tk.Frame, not a CTk widget.
        self._msg_tv_frame = tk.Frame(frame, bg=_PANEL_BG)
        tv_frame = self._msg_tv_frame
        tv_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self._msg_tree = ttk.Treeview(
            tv_frame,
            columns=("hex_id", "name", "dlc"),
            show="headings",
            selectmode="browse",
        )
        self._msg_tree.heading("hex_id", text="ID")
        self._msg_tree.heading("name", text="Message Name")
        self._msg_tree.heading("dlc", text="DLC")
        self._msg_tree.column("hex_id", width=72, anchor="center", stretch=False)
        self._msg_tree.column("name", width=200, anchor="w")
        self._msg_tree.column("dlc", width=48, anchor="center", stretch=False)

        vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=self._msg_tree.yview)
        self._msg_tree.configure(yscrollcommand=vsb.set)
        self._msg_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._msg_tree.bind("<<TreeviewSelect>>", self._on_msg_select)
        self._msg_tree.bind("<Double-1>", self._on_msg_dbl_click)

        return frame

    # ---- Signals panel ---------------------------------------------------

    def _build_signals_panel(self, parent: tk.PanedWindow) -> tk.Frame:
        # Store the outer tk.Frame for manual bg updates during theme toggle.
        # tk.Frame does not respond to CTk appearance-mode changes automatically.
        self._sig_frame = tk.Frame(parent, bg=_DARK_BG)
        frame = self._sig_frame

        # Header — fg_color tuple lets CTk pick the correct shade per mode
        hdr = ctk.CTkFrame(
            frame, height=38, corner_radius=6, fg_color=("#d5dde8", "#162032")
        )
        hdr.pack(fill="x", padx=0, pady=(0, 4))
        hdr.pack_propagate(False)

        self._sig_hdr_lbl = ctk.CTkLabel(
            hdr,
            text="⚡  Signals",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._sig_hdr_lbl.pack(side="left", padx=10)

        self._sig_count_lbl = ctk.CTkLabel(
            hdr, text="", text_color="#666666", font=ctk.CTkFont(size=11)
        )
        self._sig_count_lbl.pack(side="right", padx=10)

        self._edit_sig_btn = ctk.CTkButton(
            hdr,
            text="✏️  Edit Signal",
            command=self._edit_selected_signal,
            width=120,
            height=28,
            fg_color=_GREY,
            hover_color=_GREY_H,
            state="disabled",
        )
        self._edit_sig_btn.pack(side="right", padx=6)

        # Store inner treeview container for bg colour updates on theme toggle.
        self._sig_tv_frame = tk.Frame(frame, bg=_PANEL_BG)
        tv_frame = self._sig_tv_frame
        tv_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        tv_frame.grid_rowconfigure(0, weight=1)
        tv_frame.grid_columnconfigure(0, weight=1)

        columns = (
            "name",
            "start",
            "length",
            "byte_order",
            "factor",
            "offset",
            "min",
            "max",
            "unit",
            "comment",
        )
        self._sig_tree = ttk.Treeview(
            tv_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        col_defs = [
            ("name", "Signal Name", 160, "w"),
            ("start", "Start Bit", 72, "center"),
            ("length", "Bit Len", 60, "center"),
            ("byte_order", "Byte Order", 80, "center"),
            ("factor", "Factor", 70, "center"),
            ("offset", "Offset", 70, "center"),
            ("min", "Min", 70, "center"),
            ("max", "Max", 70, "center"),
            ("unit", "Unit", 70, "center"),
            ("comment", "Comment", 220, "w"),
        ]
        for col_id, heading, width, anchor in col_defs:
            self._sig_tree.heading(col_id, text=heading)
            self._sig_tree.column(col_id, width=width, anchor=anchor)

        vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=self._sig_tree.yview)
        hsb = ttk.Scrollbar(tv_frame, orient="horizontal", command=self._sig_tree.xview)
        self._sig_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._sig_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._sig_tree.bind("<<TreeviewSelect>>", self._on_sig_select)
        self._sig_tree.bind("<Double-1>", self._on_sig_dbl_click)

        return frame

    # ---- Status bar -------------------------------------------------------

    def _build_statusbar(self) -> None:
        # fg_color tuple so the status bar background adapts in both modes
        bar = ctk.CTkFrame(
            self.root, height=26, corner_radius=0, fg_color=("#ebebeb", "#111111")
        )
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_propagate(False)

        self._status_lbl = ctk.CTkLabel(
            bar,
            text="Ready — import a DBC file to begin.",
            font=ctk.CTkFont(size=11),
            text_color=("#555555", "#888888"),  # darker in light mode for legibility
        )
        self._status_lbl.pack(side="left", padx=10)

        self._file_lbl = ctk.CTkLabel(
            bar,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#444444", "#555555"),  # adapts contrast for both modes
        )
        self._file_lbl.pack(side="right", padx=10)

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-o>", lambda _: self.import_dbc())
        self.root.bind("<Control-s>", lambda _: self.save_dbc())
        self.root.bind("<Control-e>", lambda _: self.export_xlsx())

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _toggle_theme(self) -> None:
        """Toggle between dark and light appearance modes.

        Why: customtkinter supports runtime theme switching via
        ``ctk.set_appearance_mode()``.  CTk widgets that use fg_color / text_color
        tuples adapt automatically; plain tk widgets (Frame, PanedWindow) and
        ttk.Treeview styles must be updated manually, which we do here.
        """
        self._is_dark = not self._is_dark

        # Apply the new global CTk appearance mode.
        # All CTk widgets re-render themselves immediately after this call.
        ctk.set_appearance_mode("dark" if self._is_dark else "light")

        # Update the button label AND its text colour explicitly after every toggle.
        # Why reconfigure text_color here even though a tuple was set at creation?
        # CTk re-evaluates tuples on mode change for most properties, but calling
        # configure() with the same tuple forces an immediate redraw so the button
        # never appears stale between the set_appearance_mode() call and the next
        # paint cycle.
        if self._is_dark:
            # Now in dark mode — button offers "switch to light"
            self._theme_btn.configure(
                text="\u2600\ufe0f  Light Mode",
                fg_color=("#b8cce0", "#1e3a6e"),
                hover_color=("#9ab8d4", "#264a8e"),
                border_color=("#7a9ccc", "#4a6fa5"),
                text_color=("#0d1f3c", "#c8d8f0"),
            )
        else:
            # Now in light mode — button offers "switch to dark"
            self._theme_btn.configure(
                text="\U0001f319  Dark Mode",
                fg_color=("#b8cce0", "#1e3a6e"),
                hover_color=("#9ab8d4", "#264a8e"),
                border_color=("#7a9ccc", "#4a6fa5"),
                text_color=("#0d1f3c", "#c8d8f0"),
            )

        # Re-style ttk.Treeview — it does NOT auto-respond to CTk mode changes.
        # We must call _apply_tree_style() again with the updated flag.
        _apply_tree_style(dark=self._is_dark)

        # Update plain tk.Frame and tk.PanedWindow backgrounds manually.
        # These are standard Tkinter widgets with no knowledge of CTk themes;
        # without this step their background colours would remain stuck on
        # the colour they were given at widget-creation time.
        bg = _DARK_BG if self._is_dark else _LIGHT_BG
        panel_bg = _PANEL_BG if self._is_dark else _LIGHT_PANEL_BG

        self._paned.configure(bg=bg)
        self._msg_frame.configure(bg=bg)
        self._sig_frame.configure(bg=bg)
        self._msg_tv_frame.configure(bg=panel_bg)
        self._sig_tv_frame.configure(bg=panel_bg)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def import_dbc(self) -> None:
        path = filedialog.askopenfilename(
            title="Import DBC File",
            filetypes=[("DBC Files", "*.dbc"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            self.parser.load(path)
            self._modified = False
            self._populate_messages()
            self._set_status(
                f"✅  Loaded: {os.path.basename(path)} — {len(self.parser.messages)} messages",
                "#4caf50",
            )
            self._file_lbl.configure(text=path)
            self.root.title(f"FreeDBC Editor — {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("Import Error", str(exc))
            self._set_status("❌  Failed to load file.", "#f44336")

    def save_dbc(self) -> None:
        if not self.parser.messages:
            messagebox.showwarning("No Data", "No DBC data is currently loaded.")
            return
        init_name = (
            os.path.basename(self.parser.file_path)
            if self.parser.file_path
            else "output.dbc"
        )
        path = filedialog.asksaveasfilename(
            title="Save DBC File",
            defaultextension=".dbc",
            filetypes=[("DBC Files", "*.dbc"), ("All Files", "*.*")],
            initialfile=init_name,
        )
        if not path:
            return
        try:
            self.parser.save(path)
            self._modified = False
            self._set_status(f"✅  Saved: {path}", "#4caf50")
        except Exception as exc:
            messagebox.showerror("Save Error", str(exc))

    def export_xlsx(self) -> None:
        if not self.parser.messages:
            messagebox.showwarning("No Data", "No DBC data is currently loaded.")
            return
        path = filedialog.asksaveasfilename(
            title="Export to Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            ExcelExporter.export_xlsx(self.parser.messages, path)
            self._set_status(
                f"✅  Exported to Excel: {os.path.basename(path)}", "#4caf50"
            )
            messagebox.showinfo(
                "Export Complete", f"Data successfully exported to:\n{path}"
            )
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def export_csv(self) -> None:
        if not self.parser.messages:
            messagebox.showwarning("No Data", "No DBC data is currently loaded.")
            return
        path = filedialog.asksaveasfilename(
            title="Export to CSV",
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            ExcelExporter.export_csv(self.parser.messages, path)
            self._set_status(
                f"✅  Exported to CSV: {os.path.basename(path)}", "#4caf50"
            )
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def show_help(self) -> None:
        win = ctk.CTkToplevel(self.root)
        win.title("Help — FreeDBC Editor & Previewer")
        win.geometry("540x460")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()
        win.focus()

        tb = ctk.CTkTextbox(win, wrap="word", font=ctk.CTkFont(size=12))
        tb.pack(fill="both", expand=True, padx=16, pady=(16, 6))
        tb.insert("1.0", HELP_TEXT)
        tb.configure(state="disabled")

        ctk.CTkButton(win, text="Close", command=win.destroy, width=100).pack(
            pady=(0, 14)
        )

    # ------------------------------------------------------------------
    # Populate / filter helpers
    # ------------------------------------------------------------------

    def _populate_messages(self, filter_text: str = "") -> None:
        for item in self._msg_tree.get_children():
            self._msg_tree.delete(item)

        count = 0
        ft = filter_text.lower()
        for msg in self.parser.messages:
            if ft in msg.name.lower() or ft in f"0x{msg.id:03x}":
                self._msg_tree.insert(
                    "",
                    "end",
                    iid=str(msg.id),
                    values=(f"0x{msg.id:03X}", msg.name, msg.length),
                )
                count += 1

        self._msg_count_lbl.configure(text=f"{count} messages")
        self._clear_signals()

    def _populate_signals(self, msg) -> None:
        for item in self._sig_tree.get_children():
            self._sig_tree.delete(item)

        for sig in msg.signals:
            self._sig_tree.insert(
                "",
                "end",
                iid=sig.name,
                values=(
                    sig.name,
                    sig.start_bit,
                    sig.length,
                    "LE" if sig.byte_order == "little_endian" else "BE",
                    sig.factor,
                    sig.offset,
                    sig.minimum if sig.minimum is not None else "",
                    sig.maximum if sig.maximum is not None else "",
                    sig.unit,
                    sig.comment or "",
                ),
            )

        self._sig_hdr_lbl.configure(text=f"⚡  Signals — {msg.name}")
        self._sig_count_lbl.configure(text=f"{len(msg.signals)} signals")

    def _clear_signals(self) -> None:
        for item in self._sig_tree.get_children():
            self._sig_tree.delete(item)
        self.current_message = None
        self._sig_hdr_lbl.configure(text="⚡  Signals")
        self._sig_count_lbl.configure(text="")
        self._edit_sig_btn.configure(state="disabled")

    def _filter_messages(self, *_args) -> None:
        if self.parser.messages:
            self._populate_messages(self._search_var.get())

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_msg_select(self, _event) -> None:
        sel = self._msg_tree.selection()
        if not sel:
            return
        msg_id = int(sel[0])
        for msg in self.parser.messages:
            if msg.id == msg_id:
                self.current_message = msg
                self._populate_signals(msg)
                self._set_status(
                    f"Selected: {msg.name}  (0x{msg.id:03X}) — {len(msg.signals)} signals"
                )
                break

    def _on_msg_dbl_click(self, _event) -> None:
        sel = self._msg_tree.selection()
        if not sel:
            return
        msg_id = int(sel[0])
        for msg in self.parser.messages:
            if msg.id == msg_id:
                dlg = EditMessageDialog(self.root, msg)
                self.root.wait_window(dlg.dialog)
                if dlg.result:
                    for k, v in dlg.result.items():
                        setattr(msg, k, v)
                    self._populate_messages(self._search_var.get())
                    self._modified = True
                    self._set_status(f"✏️  Modified message: {msg.name}", "#ff9800")
                break

    def _on_sig_select(self, _event) -> None:
        state = "normal" if self._sig_tree.selection() else "disabled"
        self._edit_sig_btn.configure(state=state)

    def _on_sig_dbl_click(self, _event) -> None:
        self._edit_selected_signal()

    def _edit_selected_signal(self) -> None:
        if not self.current_message:
            return
        sel = self._sig_tree.selection()
        if not sel:
            return
        sig_name = sel[0]
        for sig in self.current_message.signals:
            if sig.name == sig_name:
                dlg = EditSignalDialog(self.root, sig)
                self.root.wait_window(dlg.dialog)
                if dlg.result:
                    for k, v in dlg.result.items():
                        setattr(sig, k, v)
                    self._populate_signals(self.current_message)
                    self._modified = True
                    self._set_status(f"✏️  Modified signal: {sig.name}", "#ff9800")
                break

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _set_status(self, text: str, color: str = "#888888") -> None:
        self._status_lbl.configure(text=text, text_color=color)


# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------

HELP_TEXT = """\
FreeDBC Editor & Previewer
══════════════════════════════════════════════════

GETTING STARTED
  1. Click "📂 Import DBC" (or Ctrl+O) to open a .dbc file.
  2. Select any message in the left panel to see its signals.
  3. Double-click a message or signal row to edit it.
  4. Save, export to Excel, or export to CSV when done.

KEYBOARD SHORTCUTS
  Ctrl+O  ─  Import DBC file
  Ctrl+S  ─  Save DBC file
  Ctrl+E  ─  Export to Excel

EDITING
  • Double-click a message row to change its name or comment.
  • Double-click a signal row (or click ✏️ Edit Signal) to
    modify: name, unit, factor, offset, min, max, comment.
  • Read-only fields (start bit, bit length, byte order, etc.)
    require a text editor and a restart to change safely.

EXPORT
  Excel (.xlsx) — produces a multi-sheet workbook:
    • Summary sheet
    • Messages sheet (all messages at a glance)
    • Signals sheet  (all signals in one table)
    • One sheet per message
  CSV (.csv) — flat table suitable for any spreadsheet app.

ABOUT DBC FILES
  A .dbc (Database CAN) file describes the structure of CAN
  bus communication: messages (frames) and signals (bit-fields)
  with their encoding (factor, offset, range, unit).
  They are used heavily in automotive & industrial systems.

──────────────────────────────────────────────────
  Open-Source · MIT License
  https://github.com/Piyush-Pal-786/FreeDbc_EditorPreviewer
"""
