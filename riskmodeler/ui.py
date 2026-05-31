"""
Tkinter 界面样式与布局辅助方法。
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


BG_COLOR = "#f4f7fb"
CARD_COLOR = "#ffffff"
ACCENT_COLOR = "#1f6feb"
ACCENT_SOFT = "#e8f0fe"
TEXT_COLOR = "#17324d"
MUTED_COLOR = "#5b7086"
BORDER_COLOR = "#d7e2ee"
SUCCESS_COLOR = "#1a7f37"
WARNING_COLOR = "#b54708"


def apply_app_style(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.option_add("*Font", "Helvetica 13")
    root.option_add("*Background", BG_COLOR)

    style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR)
    style.configure("App.TFrame", background=BG_COLOR)
    style.configure("Card.TFrame", background=CARD_COLOR, relief="flat")
    style.configure(
        "Card.TLabelframe",
        background=CARD_COLOR,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=CARD_COLOR,
        foreground=TEXT_COLOR,
        font=("Helvetica", 13, "bold"),
    )
    style.configure("Title.TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=("Helvetica", 24, "bold"))
    style.configure("Subtitle.TLabel", background=BG_COLOR, foreground=MUTED_COLOR, font=("Helvetica", 12))
    style.configure("SectionTitle.TLabel", background=CARD_COLOR, foreground=TEXT_COLOR, font=("Helvetica", 14, "bold"))
    style.configure("Field.TLabel", background=CARD_COLOR, foreground=TEXT_COLOR, font=("Helvetica", 12))
    style.configure("Hint.TLabel", background=CARD_COLOR, foreground=MUTED_COLOR, font=("Helvetica", 11))
    style.configure("Status.TLabel", background=BG_COLOR, foreground=MUTED_COLOR, font=("Helvetica", 11))
    style.configure("Accent.TButton", padding=(14, 8), background=ACCENT_COLOR, foreground="white", borderwidth=0)
    style.map("Accent.TButton", background=[("active", "#1857b8")], foreground=[("disabled", "#d7e2ee")])
    style.configure("Secondary.TButton", padding=(12, 8), background=ACCENT_SOFT, foreground=ACCENT_COLOR, borderwidth=0)
    style.map("Secondary.TButton", background=[("active", "#dce8ff")])
    style.configure("Toolbar.TButton", padding=(12, 7), background=CARD_COLOR, foreground=TEXT_COLOR, borderwidth=1)
    style.map("Toolbar.TButton", background=[("active", ACCENT_SOFT)])
    style.configure("TEntry", padding=7, fieldbackground="white", bordercolor=BORDER_COLOR, lightcolor=BORDER_COLOR, darkcolor=BORDER_COLOR)
    style.configure("TCombobox", padding=5, fieldbackground="white")
    style.configure("Treeview", rowheight=28)
    style.configure("TNotebook", background=BG_COLOR, borderwidth=0, tabmargins=(0, 0, 0, 0))
    style.configure("TNotebook.Tab", padding=(14, 8), background=ACCENT_SOFT, foreground=TEXT_COLOR)
    style.map("TNotebook.Tab", background=[("selected", CARD_COLOR)], foreground=[("selected", ACCENT_COLOR)])
    return style


def center_window(window: tk.Misc, width: int, height: int) -> None:
    screenwidth = window.winfo_screenwidth()
    screenheight = window.winfo_screenheight()
    left = int((screenwidth - width) / 2)
    top = int((screenheight - height) / 2)
    window.geometry(f"{width}x{height}+{left}+{top}")


def configure_form_grid(container: tk.Misc, column_count: int = 2) -> None:
    for column in range(column_count):
        container.grid_columnconfigure(column, weight=1 if column == column_count - 1 else 0)


def set_window_ready(window: tk.Misc, title: str, width: int, height: int, resizable: bool = False) -> None:
    window.title(title)
    window.configure(bg=BG_COLOR)
    center_window(window, width, height)
    window.resizable(resizable, resizable)


def clear_and_fill(entry_widget: tk.Entry, value: str) -> None:
    entry_widget.delete(0, tk.END)
    entry_widget.insert(tk.INSERT, value)


def create_scrollable_treeview(
    parent: tk.Misc,
    columns: tuple[str, ...],
    height: int | None = None,
    selectmode: str = "browse",
) -> tuple[ttk.Frame, ttk.Treeview]:
    container = ttk.Frame(parent, style="Card.TFrame")
    container.grid_columnconfigure(0, weight=1)
    container.grid_rowconfigure(0, weight=1)

    tree = ttk.Treeview(container, show="headings", columns=columns, selectmode=selectmode, height=height)
    tree.grid(column=0, row=0, sticky="nsew")

    yscroll = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    yscroll.grid(column=1, row=0, sticky="ns")
    xscroll = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
    xscroll.grid(column=0, row=1, sticky="ew")
    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
    return container, tree


def create_readonly_text(parent: tk.Misc, width: int, height: int) -> ScrolledText:
    text = ScrolledText(parent, width=width, height=height, relief="flat", borderwidth=1)
    text.configure(background="white", foreground=TEXT_COLOR, insertbackground=TEXT_COLOR)
    return text
