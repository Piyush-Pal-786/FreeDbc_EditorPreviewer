"""
dbc_parser.py
=============
Wraps the `cantools` library to load, represent, modify, and re-serialize
DBC (CAN Database) files.  All internal data is stored in plain Python
dataclasses so the rest of the application never touches cantools directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import cantools


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class SignalData:
    """Mutable representation of a single CAN signal."""

    name: str
    start_bit: int
    length: int
    byte_order: str  # 'little_endian' | 'big_endian'
    is_signed: bool
    factor: float
    offset: float
    minimum: Optional[float]
    maximum: Optional[float]
    unit: str
    comment: Optional[str]
    choices: Dict[int, str] = field(default_factory=dict)


@dataclass
class MessageData:
    """Mutable representation of a single CAN message (frame)."""

    id: int
    name: str
    length: int  # DLC in bytes
    comment: Optional[str]
    signals: List[SignalData] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser / Writer
# ---------------------------------------------------------------------------


class DBCParser:
    """Load, expose, modify and save DBC files."""

    def __init__(self) -> None:
        self.db: Optional[cantools.db.Database] = None
        self.file_path: Optional[str] = None
        self.messages: List[MessageData] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, file_path: str) -> None:
        """Parse *file_path* and populate :attr:`messages`.

        Raises :class:`ValueError` on any parse error.
        """
        try:
            self.db = cantools.database.load_file(file_path)
            self.file_path = file_path
            self._parse_messages()
        except Exception as exc:
            raise ValueError(f"Failed to load DBC file:\n{exc}") from exc

    def save(self, file_path: Optional[str] = None) -> None:
        """Write the current (possibly modified) data back to a .dbc file."""
        target = file_path or self.file_path
        if not target:
            raise ValueError("No output path specified.")
        content = self._generate_dbc()
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(content)

    def update_signal(self, msg_id: int, signal_name: str, **kwargs) -> bool:
        """Patch attributes of a signal by message-id and signal name."""
        for msg in self.messages:
            if msg.id == msg_id:
                for sig in msg.signals:
                    if sig.name == signal_name:
                        for key, value in kwargs.items():
                            if hasattr(sig, key):
                                setattr(sig, key, value)
                        return True
        return False

    def update_message(self, msg_id: int, **kwargs) -> bool:
        """Patch attributes of a message by id."""
        for msg in self.messages:
            if msg.id == msg_id:
                for key, value in kwargs.items():
                    if hasattr(msg, key):
                        setattr(msg, key, value)
                return True
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_messages(self) -> None:
        self.messages = []
        for cantools_msg in sorted(self.db.messages, key=lambda m: m.frame_id):
            signals: List[SignalData] = []
            for sig in cantools_msg.signals:
                choices: Dict[int, str] = {}
                if sig.choices:
                    choices = {int(k): str(v) for k, v in sig.choices.items()}

                signals.append(
                    SignalData(
                        name=sig.name,
                        start_bit=sig.start,
                        length=sig.length,
                        byte_order=sig.byte_order,  # already a string in cantools
                        is_signed=bool(sig.is_signed),
                        factor=float(sig.scale) if sig.scale is not None else 1.0,
                        offset=float(sig.offset) if sig.offset is not None else 0.0,
                        minimum=float(sig.minimum) if sig.minimum is not None else None,
                        maximum=float(sig.maximum) if sig.maximum is not None else None,
                        unit=sig.unit or "",
                        comment=sig.comment,
                        choices=choices,
                    )
                )

            self.messages.append(
                MessageData(
                    id=cantools_msg.frame_id,
                    name=cantools_msg.name,
                    length=cantools_msg.length,
                    comment=cantools_msg.comment,
                    signals=signals,
                )
            )

    def _generate_dbc(self) -> str:
        """Produce a valid DBC text from the current :attr:`messages` list."""
        lines: List[str] = []

        # ---- Header -------------------------------------------------------
        lines += [
            'VERSION ""',
            "",
            "NS_ :",
            "\tNS_DESC_",
            "\tCM_",
            "\tBA_DEF_",
            "\tBA_",
            "\tVAL_",
            "\tCAT_DEF_",
            "\tCAT_",
            "\tFILTER",
            "\tBA_DEF_DEF_",
            "\tEV_DATA_",
            "\tENVVAR_DATA_",
            "\tSGTYPE_",
            "\tSGTYPE_VAL_",
            "\tBA_DEF_SGTYPE_",
            "\tBA_SGTYPE_",
            "\tSIG_TYPE_REF_",
            "\tVAL_TABLE_",
            "\tSIG_GROUP_",
            "\tSIG_VALTYPE_",
            "\tSIGTYPE_VALTYPE_",
            "\tBO_TX_BU_",
            "\tBA_DEF_REL_",
            "\tBA_REL_",
            "\tBA_DEF_DEF_REL_",
            "\tBU_SG_REL_",
            "\tBU_EV_REL_",
            "\tBU_BO_REL_",
            "\tSG_MUL_VAL_",
            "",
            "BS_:",
            "",
            "BU_:",
            "",
        ]

        # ---- Messages & signals -------------------------------------------
        for msg in self.messages:
            lines.append(f"BO_ {msg.id} {msg.name}: {msg.length} Vector__XXX")
            for sig in msg.signals:
                byte_order_char = "1" if sig.byte_order == "little_endian" else "0"
                sign_char = "+" if not sig.is_signed else "-"
                min_val = sig.minimum if sig.minimum is not None else 0
                max_val = sig.maximum if sig.maximum is not None else 0
                lines.append(
                    f" SG_ {sig.name} : "
                    f"{sig.start_bit}|{sig.length}@{byte_order_char}{sign_char} "
                    f"({sig.factor},{sig.offset}) "
                    f"[{min_val}|{max_val}] "
                    f'"{sig.unit}" Vector__XXX'
                )
            lines.append("")

        # ---- Comments -------------------------------------------------------
        lines.append("")
        for msg in self.messages:
            if msg.comment:
                lines.append(f'CM_ BO_ {msg.id} "{self._esc(msg.comment)}";')
            for sig in msg.signals:
                if sig.comment:
                    lines.append(
                        f'CM_ SG_ {msg.id} {sig.name} "{self._esc(sig.comment)}";'
                    )

        # ---- Value descriptions ----------------------------------------------
        lines.append("")
        for msg in self.messages:
            for sig in msg.signals:
                if sig.choices:
                    val_str = " ".join(
                        f'{k} "{v}"' for k, v in sorted(sig.choices.items())
                    )
                    lines.append(f"VAL_ {msg.id} {sig.name} {val_str} ;")

        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _esc(text: str) -> str:
        """Escape double-quotes inside DBC comment strings."""
        return text.replace('"', '\\"')
