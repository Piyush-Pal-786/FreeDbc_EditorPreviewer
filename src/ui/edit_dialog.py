"""
edit_dialog.py
==============
Modal dialogs for editing a MessageData or SignalData object in-place.
The caller checks ``dialog.result`` after ``root.wait_window(dialog.dialog)``.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Any, Dict, Optional

import customtkinter as ctk


# ---------------------------------------------------------------------------
# Signal editor
# ---------------------------------------------------------------------------


class EditSignalDialog:
    """Edit the user-facing attributes of a :class:`~core.dbc_parser.SignalData`."""

    def __init__(self, parent: ctk.CTk, signal: Any) -> None:
        self.result: Optional[Dict[str, Any]] = None
        self._signal = signal

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(f"Edit Signal — {signal.name}")
        self.dialog.geometry("520x620")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.focus()

        self._build()

    # ------------------------------------------------------------------

    def _build(self) -> None:
        sig = self._signal

        # Scrollable main area
        scroll = ctk.CTkScrollableFrame(self.dialog)
        scroll.pack(fill="both", expand=True, padx=16, pady=(16, 4))
        scroll.grid_columnconfigure(1, weight=1)

        # Section: editable fields
        self._section(scroll, "✏️  Editable Properties", row=0)

        self.name_var = tk.StringVar(value=sig.name)
        self.unit_var = tk.StringVar(value=sig.unit)
        self.factor_var = tk.StringVar(value=str(sig.factor))
        self.offset_var = tk.StringVar(value=str(sig.offset))
        self.min_var = tk.StringVar(
            value="" if sig.minimum is None else str(sig.minimum)
        )
        self.max_var = tk.StringVar(
            value="" if sig.maximum is None else str(sig.maximum)
        )
        self.comment_var = tk.StringVar(value=sig.comment or "")

        editable = [
            ("Signal Name *", self.name_var),
            ("Unit", self.unit_var),
            ("Factor", self.factor_var),
            ("Offset", self.offset_var),
            ("Minimum", self.min_var),
            ("Maximum", self.max_var),
            ("Comment", self.comment_var),
        ]
        for i, (label, var) in enumerate(editable, start=1):
            self._field_row(scroll, label, var, row=i)

        # Section: read-only info
        row_start = len(editable) + 2
        self._section(scroll, "🔒  Read-only Properties", row=row_start)
        ro_frame = ctk.CTkFrame(
            scroll, fg_color=("#1a1a1a", "#1a1a1a"), corner_radius=6
        )
        ro_frame.grid(
            row=row_start + 1, column=0, columnspan=2, sticky="ew", pady=4, padx=2
        )

        ro_items = [
            ("Start Bit", str(sig.start_bit)),
            ("Bit Length", str(sig.length)),
            ("Byte Order", sig.byte_order),
            ("Signed", "Yes" if sig.is_signed else "No"),
        ]
        for label, value in ro_items:
            row_f = ctk.CTkFrame(ro_frame, fg_color="transparent")
            row_f.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(
                row_f, text=f"{label}:", width=100, anchor="w", text_color="#aaaaaa"
            ).pack(side="left")
            ctk.CTkLabel(row_f, text=value, anchor="w").pack(side="left")

        # Section: value descriptions (if any)
        if sig.choices:
            row_val = row_start + 3
            self._section(scroll, "📋  Value Descriptions", row=row_val)
            val_frame = ctk.CTkFrame(
                scroll, fg_color=("#1a1a1a", "#1a1a1a"), corner_radius=6
            )
            val_frame.grid(
                row=row_val + 1, column=0, columnspan=2, sticky="ew", pady=4, padx=2
            )
            for k, v in sorted(sig.choices.items()):
                row_f = ctk.CTkFrame(val_frame, fg_color="transparent")
                row_f.pack(fill="x", padx=12, pady=2)
                ctk.CTkLabel(
                    row_f, text=f"{k}", width=60, anchor="e", text_color="#4a9eff"
                ).pack(side="left")
                ctk.CTkLabel(
                    row_f, text="→", width=30, anchor="center", text_color="#666666"
                ).pack(side="left")
                ctk.CTkLabel(row_f, text=v, anchor="w").pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(4, 16))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.dialog.destroy,
            width=100,
            fg_color="#555555",
            hover_color="#666666",
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame,
            text="💾  Save Changes",
            command=self._save,
            width=140,
            fg_color="#2d7a2d",
            hover_color="#38963a",
        ).pack(side="right", padx=4)

    # ------------------------------------------------------------------

    def _section(self, parent: ctk.CTkScrollableFrame, text: str, row: int) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4a9eff",
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(12, 4), padx=2)

    def _field_row(
        self,
        parent: ctk.CTkScrollableFrame,
        label: str,
        var: tk.StringVar,
        row: int,
    ) -> None:
        ctk.CTkLabel(parent, text=label, anchor="w", width=120).grid(
            row=row, column=0, sticky="w", pady=5, padx=(2, 8)
        )
        ctk.CTkEntry(parent, textvariable=var).grid(
            row=row, column=1, sticky="ew", pady=5, padx=2
        )

    def _save(self) -> None:
        try:
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror(
                    "Validation", "Signal name cannot be empty.", parent=self.dialog
                )
                return

            self.result = {
                "name": name,
                "unit": self.unit_var.get().strip(),
                "factor": float(self.factor_var.get()),
                "offset": float(self.offset_var.get()),
                "minimum": (
                    float(self.min_var.get()) if self.min_var.get().strip() else None
                ),
                "maximum": (
                    float(self.max_var.get()) if self.max_var.get().strip() else None
                ),
                "comment": self.comment_var.get().strip() or None,
            }
            self.dialog.destroy()
        except ValueError as exc:
            messagebox.showerror(
                "Validation Error", f"Invalid number: {exc}", parent=self.dialog
            )


# ---------------------------------------------------------------------------
# Message editor
# ---------------------------------------------------------------------------


class EditMessageDialog:
    """Edit the user-facing attributes of a :class:`~core.dbc_parser.MessageData`."""

    def __init__(self, parent: ctk.CTk, message: Any) -> None:
        self.result: Optional[Dict[str, Any]] = None
        self._message = message

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(f"Edit Message — {message.name}")
        self.dialog.geometry("460x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.focus()

        self._build()

    # ------------------------------------------------------------------

    def _build(self) -> None:
        msg = self._message

        main = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=16, pady=16)
        main.grid_columnconfigure(1, weight=1)

        self.name_var = tk.StringVar(value=msg.name)
        self.comment_var = tk.StringVar(value=msg.comment or "")

        fields = [
            ("Message Name *", self.name_var),
            ("Comment", self.comment_var),
        ]
        for i, (label, var) in enumerate(fields):
            ctk.CTkLabel(main, text=label, anchor="w", width=130).grid(
                row=i, column=0, sticky="w", pady=8, padx=(0, 10)
            )
            ctk.CTkEntry(main, textvariable=var).grid(
                row=i, column=1, sticky="ew", pady=8
            )

        # Read-only info box
        info = ctk.CTkFrame(main, fg_color=("#1a1a1a", "#1a1a1a"), corner_radius=6)
        info.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        ctk.CTkLabel(
            info,
            text=f"  ID: 0x{msg.id:03X}  ({msg.id} dec)       DLC: {msg.length} bytes",
            text_color="#aaaaaa",
        ).pack(anchor="w", padx=12, pady=8)

        # Buttons
        btn_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.dialog.destroy,
            width=100,
            fg_color="#555555",
            hover_color="#666666",
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame,
            text="💾  Save Changes",
            command=self._save,
            width=140,
            fg_color="#2d7a2d",
            hover_color="#38963a",
        ).pack(side="right", padx=4)

    # ------------------------------------------------------------------

    def _save(self) -> None:
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror(
                "Validation", "Message name cannot be empty.", parent=self.dialog
            )
            return
        self.result = {
            "name": name,
            "comment": self.comment_var.get().strip() or None,
        }
        self.dialog.destroy()
