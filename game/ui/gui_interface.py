"""PySide6 graphical frontend.

This is an alternative UI layer that drives the SAME engine as the CLI. It never
contains gameplay rules: every button click builds a structured command
(``{"action": ...}``) exactly like the command router would, hands it to
``engine.process_action``, and renders the returned result dictionary into Qt
widgets. Swapping the CLI for this GUI required zero changes to the core, the
systems, or the models.

Combat uses a Pokemon-style menu: a 2x2 command grid (FIGHT / BAG / STATS / RUN),
where FIGHT opens a grid of techniques (moves) showing qi cost and cooldown,
disabling any technique that is on cooldown or unaffordable.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMainWindow,
)

from game.core.constants import Action, EventType
from game.core.game_engine import GameEngine
from game.ui import ui_theme as T


def martial_path_icon_path() -> Optional[str]:
    """Return the absolute path to the shared Martial Path app icon, if present.

    The icon lives at "Images/Martial Path Icon.png" under the repository root.
    Resolving it relative to this module lets the main window and the QApplication share it.
    """
    candidate = Path(__file__).resolve().parents[2] / "Images" / "Martial Path Icon.png"
    return str(candidate) if candidate.exists() else None


def _esc(text: Any) -> str:
    """Escape text for safe insertion into the rich-text log.

    Uses the stdlib HTML escaper (quotes included) so player/NPC names are
    preserved intact rather than having characters stripped out.
    """
    return escape(str(text), quote=True)


def _danger_color(label: Any) -> str:
    """Map a danger word to a semantic colour (presentation only, no rules)."""
    word = str(label).strip().lower()
    if word in {"safe", "low"}:
        return T.SUCCESS
    if word in {"moderate"}:
        return T.WARNING
    if word in {"high", "deadly", "lethal"}:
        return T.DANGER
    return T.TEXT_SECONDARY


def _stylesheet() -> str:
    """Build the global Qt Style Sheet from the theme palette."""
    return f"""
        QWidget {{
            color: {T.TEXT_PRIMARY};
            font-family: "Segoe UI", "Segoe UI Symbol", sans-serif;
            font-size: 13px;
        }}
        QMainWindow, QDialog {{ background-color: {T.BACKGROUND}; }}

        QFrame#Panel {{
            background-color: {T.PANEL};
            border: 1px solid {T.BORDER};
            border-radius: 8px;
        }}
        QFrame#TopBar {{
            background-color: {T.HEADER};
            border: 1px solid {T.BORDER};
            border-radius: 8px;
        }}
        QFrame#Artwork {{
            border: 1px solid {T.BORDER};
            border-radius: 6px;
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0F1A16, stop:0.5 #0C1512, stop:1 #0A0F13);
        }}
        QFrame#EnemyBox {{
            background-color: {T.PANEL_SOFT};
            border: 1px solid {T.DANGER};
            border-radius: 6px;
        }}
        QLabel#Emblem {{
            border: 2px solid {T.BORDER_STRONG};
            border-radius: 22px;
            background-color: {T.PANEL_SOFT};
        }}

        QLabel#GameTitle {{
            color: {T.GOLD_BRIGHT};
            font-family: "Georgia", "Cambria", "Times New Roman", serif;
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 2px;
        }}
        QLabel#PlayerName {{ color: {T.TEXT_SECONDARY}; font-size: 12px; }}
        QLabel#SectionTitle {{
            color: {T.GOLD};
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 2px;
        }}
        QLabel#Caption {{ color: {T.TEXT_MUTED}; font-size: 11px; }}
        QLabel#Body {{ color: {T.TEXT_PRIMARY}; font-size: 13px; }}
        QLabel#StatValue {{ color: {T.TEXT_PRIMARY}; font-weight: bold; }}
        QLabel#Prompt {{ color: {T.TEXT_MUTED}; font-size: 12px; }}
        QLabel#TopStat {{ color: {T.TEXT_PRIMARY}; font-size: 13px; font-weight: bold; }}
        QLabel#TopTime {{ color: {T.TEXT_PRIMARY}; font-size: 12px; font-weight: bold; }}
        QLabel#LocationName {{
            color: {T.GOLD_BRIGHT};
            font-family: "Georgia", "Cambria", serif;
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 1px;
        }}
        QLabel#ArtworkLabel {{
            color: rgba(242, 232, 213, 90);
            font-family: "Georgia", "Cambria", serif;
            font-size: 20px;
            font-weight: bold;
            letter-spacing: 2px;
        }}
        QLabel#EnemyName {{ color: {T.DANGER}; font-size: 14px; font-weight: bold; }}
        QLabel#GoldLabel {{ color: {T.GOLD}; font-weight: bold; }}
        QLabel#StoneLabel {{ color: {T.INVENTORY_BLUE}; font-weight: bold; }}

        QTextEdit#Log {{
            background-color: {T.PANEL_SOFT};
            border: 1px solid {T.BORDER};
            border-radius: 6px;
            font-size: 12px;
            padding: 6px;
        }}

        QLineEdit {{
            background-color: {T.PANEL_RAISED};
            color: {T.TEXT_PRIMARY};
            border: 1px solid {T.BORDER_STRONG};
            border-radius: 4px;
            padding: 6px 8px;
            selection-background-color: {T.GOLD};
            selection-color: {T.TEXT_ON_ACCENT};
        }}
        QLineEdit:focus {{ border-color: {T.FOCUS_RING}; }}

        QProgressBar {{
            background-color: {T.PANEL_RAISED};
            border: 1px solid {T.BORDER};
            border-radius: 4px;
            text-align: center;
            color: {T.TEXT_PRIMARY};
            font-size: 10px;
            font-weight: bold;
        }}
        QProgressBar::chunk {{ background-color: {T.BODY_GREEN}; border-radius: 3px; }}

        QPushButton {{
            background-color: {T.PANEL_RAISED};
            color: {T.TEXT_PRIMARY};
            border: 1px solid {T.BORDER};
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {T.STATE_HOVER}; border-color: {T.BORDER_STRONG}; }}
        QPushButton:pressed {{ background-color: {T.STATE_ACTIVE}; }}
        QPushButton:disabled {{
            background-color: {T.STATE_DISABLED_BG};
            color: {T.STATE_DISABLED_FG};
            border-color: {T.BORDER};
        }}

        QPushButton#ActionCard {{
            background-color: {T.PANEL_RAISED};
            border: 1px solid {T.BORDER};
            border-radius: 6px;
            padding: 0px;
            text-align: left;
        }}
        QPushButton#ActionCard:hover {{ border-color: {T.BORDER_STRONG}; background-color: {T.STATE_HOVER}; }}
        QPushButton#ActionCard:disabled {{ background-color: {T.STATE_DISABLED_BG}; border-color: {T.BORDER}; }}
        QLabel#CardTitle {{ color: {T.GOLD}; font-weight: bold; font-size: 13px; background: transparent; }}
        QLabel#CardSub {{ color: {T.TEXT_MUTED}; font-size: 10px; background: transparent; }}
        QLabel#CardTitle:disabled {{ color: {T.STATE_DISABLED_FG}; }}
        QLabel#CardSub:disabled {{ color: {T.STATE_DISABLED_FG}; }}

        QPushButton#Ghost {{
            background-color: transparent;
            border: 1px solid {T.BORDER};
            color: {T.TEXT_SECONDARY};
            padding: 6px 10px;
        }}
        QPushButton#Ghost:hover {{ border-color: {T.GOLD}; color: {T.GOLD_BRIGHT}; }}

        QPushButton#BattlePrimary {{
            background-color: {T.GOLD};
            color: {T.TEXT_ON_ACCENT};
            border: 1px solid {T.GOLD_BRIGHT};
            font-size: 15px;
            padding: 18px;
        }}
        QPushButton#BattlePrimary:hover {{ background-color: {T.GOLD_BRIGHT}; }}
        QPushButton#BattleBtn {{ font-size: 14px; padding: 16px; }}
        QPushButton#MoveBtn {{ font-size: 13px; padding: 14px; }}
        QPushButton#BagBtn {{ text-align: left; padding: 10px 14px; }}

        QTabWidget#RightTabs::pane {{
            background-color: {T.PANEL};
            border: 1px solid {T.BORDER};
            border-radius: 8px;
            top: -1px;
        }}
        QTabBar::tab {{
            background: {T.PANEL_SOFT};
            color: {T.TEXT_SECONDARY};
            border: 1px solid {T.BORDER};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 7px 12px;
            margin-right: 2px;
            font-size: 12px;
        }}
        QTabBar::tab:selected {{ background: {T.PANEL}; color: {T.GOLD_BRIGHT}; border-color: {T.BORDER_STRONG}; }}
        QTabBar::tab:hover {{ color: {T.GOLD}; }}

        QToolTip {{
            background-color: {T.PANEL};
            color: {T.TEXT_PRIMARY};
            border: 1px solid {T.GOLD};
            padding: 4px;
        }}
        QScrollBar:vertical {{ background: {T.BACKGROUND}; width: 12px; margin: 0; }}
        QScrollBar::handle:vertical {{ background: {T.BORDER_STRONG}; border-radius: 6px; min-height: 24px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """


class _HoverButton(QPushButton):
    """A push button that reports hover, so the move menu can show move details."""

    def __init__(self, text: str, on_hover: Callable[[], None]) -> None:
        super().__init__(text)
        self._on_hover = on_hover

    def enterEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        self._on_hover()
        super().enterEvent(event)


class GUIInterface(QMainWindow):
    """Qt main window that renders the game and forwards structured commands."""

    def __init__(self, engine: GameEngine) -> None:
        super().__init__()
        self._engine = engine
        # Cosmetic display state only (the engine has no calendar yet); the top
        # bar reads real values from state["time"] when the engine provides them.
        self._day = 1
        self._period = "Morning"
        # UI-only inventory capacity for the "used / capacity" readout; there is
        # no backend capacity system, so this is a presentation constant.
        self._inv_capacity = 50
        self.setWindowTitle("Martial Path - Cultivation RPG")
        icon_path = martial_path_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        self.setMinimumSize(1120, 720)
        self.setStyleSheet(_stylesheet())
        self._build_ui()

    # -- lifecycle --------------------------------------------------------
    def start(self) -> None:
        """Prompt for a name and begin the session (call after ``show()``)."""
        name, ok = QInputDialog.getText(self, "Enter the Dao", "Your cultivator's name:")
        chosen = name.strip() if (ok and name.strip()) else "Nameless Daozi"
        self._engine.set_player_name(chosen)
        self._log("The long road of cultivation opens before you...", T.ACCENT_LINK)
        self._log("Train to build progress - Explore for fortune and foes - then Breakthrough.", T.TEXT_SECONDARY)
        self._refresh()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        self._engine.process_action({"action": Action.QUIT})
        event.accept()

    # -- UI construction --------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addWidget(self._build_top_bar())

        content = QHBoxLayout()
        content.setSpacing(8)
        content.addWidget(self._build_character_panel())
        center = QVBoxLayout()
        center.setSpacing(8)
        center.addWidget(self._build_location_panel(), 1)
        center.addWidget(self._build_action_panel())
        content.addLayout(center, 1)
        content.addWidget(self._build_right_tabs())
        root.addLayout(content, 1)

        root.addWidget(self._build_event_log())

    # -- top bar ----------------------------------------------------------
    def _build_top_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(72)
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 8, 16, 8)
        h.setSpacing(16)

        emblem = QLabel()
        emblem.setObjectName("Emblem")
        emblem.setFixedSize(44, 44)
        emblem.setAlignment(Qt.AlignCenter)
        icon_path = martial_path_icon_path()
        if icon_path:
            pix = QPixmap(icon_path)
            if not pix.isNull():
                emblem.setPixmap(pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title = QLabel("MARTIAL PATH")
        title.setObjectName("GameTitle")
        self._lbl_player = QLabel("-")
        self._lbl_player.setObjectName("PlayerName")
        title_col.addWidget(title)
        title_col.addWidget(self._lbl_player)
        h.addWidget(emblem)
        h.addLayout(title_col)
        h.addStretch(1)

        self._top_hp = QLabel("HP -/-")
        self._top_hp.setObjectName("TopStat")
        self._bar_hp = self._mini_bar(T.HP_COLOR)
        h.addLayout(self._top_stat_block(self._top_hp, self._bar_hp))

        self._top_qi = QLabel("Qi -/-")
        self._top_qi.setObjectName("TopStat")
        self._bar_qi = self._mini_bar(T.QI_COLOR)
        h.addLayout(self._top_stat_block(self._top_qi, self._bar_qi))

        self._top_time = QLabel("Day 1\nMorning")
        self._top_time.setObjectName("TopTime")
        h.addWidget(self._top_time)

        h.addStretch(1)
        settings = self._btn("\u2699  Settings", self._open_settings, "Ghost")
        h.addWidget(settings)
        return bar

    def _top_stat_block(self, label: QLabel, bar: QProgressBar) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(label)
        col.addWidget(bar)
        return col

    # -- left character panel --------------------------------------------
    def _build_character_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setFixedWidth(258)
        v = QVBoxLayout(panel)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(5)

        v.addWidget(self._section_title("Character"))
        self._cp_name = self._rich_label()
        self._cp_path = self._rich_label()
        v.addWidget(self._cp_name)
        v.addWidget(self._cp_path)
        v.addSpacing(6)

        v.addWidget(self._section_title("Cultivation"))
        self._cp_body = self._rich_label()
        self._cp_progress = self._rich_label()
        self._bar_body = self._make_bar()
        self._cp_foundation = self._rich_label()
        self._cp_strength = self._rich_label()
        v.addWidget(self._cp_body)
        v.addWidget(self._cp_progress)
        v.addWidget(self._bar_body)
        v.addWidget(self._cp_foundation)
        v.addWidget(self._cp_strength)
        v.addSpacing(4)
        self._cp_essence = self._rich_label()
        self._cp_essence_req = self._rich_label()
        self._cp_essence_req.setWordWrap(True)
        v.addWidget(self._cp_essence)
        v.addWidget(self._cp_essence_req)
        v.addSpacing(6)

        v.addWidget(self._section_title("Combat"))
        atk_row, self._cp_atk = self._stat_row("ATK")
        def_row, self._cp_def = self._stat_row("DEF")
        comp_row, self._cp_comp = self._stat_row("Comprehension")
        rep_row, self._cp_rep = self._stat_row("Reputation")
        v.addWidget(atk_row)
        v.addWidget(def_row)
        v.addWidget(comp_row)
        v.addWidget(rep_row)
        v.addSpacing(8)
        self._btn_status = self._btn("View Detailed Status", lambda: self._focus_tab(2), "Ghost")
        v.addWidget(self._btn_status)
        v.addStretch(1)
        return panel

    # -- centre location panel -------------------------------------------
    def _build_location_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        v = QVBoxLayout(panel)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(8)

        self._loc_name = QLabel("-")
        self._loc_name.setObjectName("LocationName")
        v.addWidget(self._loc_name)

        self._artwork = QFrame()
        self._artwork.setObjectName("Artwork")
        self._artwork.setMinimumHeight(190)
        self._artwork.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        av = QVBoxLayout(self._artwork)
        av.setContentsMargins(12, 12, 12, 12)
        self._artwork_label = QLabel("-")
        self._artwork_label.setObjectName("ArtworkLabel")
        self._artwork_label.setAlignment(Qt.AlignCenter)
        self._artwork_label.setWordWrap(True)
        av.addStretch(1)
        av.addWidget(self._artwork_label)
        av.addStretch(1)
        v.addWidget(self._artwork, 1)

        self._enemy_box = QFrame()
        self._enemy_box.setObjectName("EnemyBox")
        ev = QHBoxLayout(self._enemy_box)
        ev.setContentsMargins(12, 6, 12, 6)
        ev.setSpacing(8)
        self._lbl_enemy = QLabel("-")
        self._lbl_enemy.setObjectName("EnemyName")
        self._bar_enemy = self._mini_bar(T.HP_COLOR)
        self._bar_enemy.setFixedWidth(180)
        ev.addWidget(self._lbl_enemy)
        ev.addStretch(1)
        ev.addWidget(self._bar_enemy)
        v.addWidget(self._enemy_box)
        self._enemy_box.hide()

        self._loc_desc = QLabel("-")
        self._loc_desc.setObjectName("Body")
        self._loc_desc.setWordWrap(True)
        v.addWidget(self._loc_desc)

        self._loc_meta = self._rich_label()
        self._loc_meta.setWordWrap(True)
        self._loc_exits = self._rich_label()
        self._loc_exits.setWordWrap(True)
        v.addWidget(self._loc_meta)
        v.addWidget(self._loc_exits)
        return panel

    # -- centre action panel ---------------------------------------------
    def _build_action_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        v = QVBoxLayout(panel)
        v.setContentsMargins(14, 10, 14, 12)
        v.setSpacing(8)
        header = QHBoxLayout()
        header.addWidget(self._section_title("Actions"))
        header.addStretch(1)
        self._prompt = QLabel("...")
        self._prompt.setObjectName("Prompt")
        header.addWidget(self._prompt)
        v.addLayout(header)
        self._action_host = QWidget()
        self._action_layout = QVBoxLayout(self._action_host)
        self._action_layout.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self._action_host)
        return panel

    # -- right tabbed panel ----------------------------------------------
    def _build_right_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName("RightTabs")
        tabs.setFixedWidth(340)
        self._right_tabs = tabs

        inv = QWidget()
        iv = QVBoxLayout(inv)
        iv.setContentsMargins(12, 10, 12, 10)
        iv.setSpacing(6)
        inv_header = QHBoxLayout()
        inv_header.addWidget(self._section_title("Inventory"))
        inv_header.addStretch(1)
        self._inv_count = QLabel("0 / 50")
        self._inv_count.setObjectName("Caption")
        inv_header.addWidget(self._inv_count)
        iv.addLayout(inv_header)
        self._inv_list = QTextEdit()
        self._inv_list.setObjectName("Log")
        self._inv_list.setReadOnly(True)
        iv.addWidget(self._inv_list, 1)
        footer = QHBoxLayout()
        self._inv_gold = QLabel("Gold: 0")
        self._inv_gold.setObjectName("GoldLabel")
        self._inv_stones = QLabel("Spirit Stones: 0")
        self._inv_stones.setObjectName("StoneLabel")
        footer.addWidget(self._inv_gold)
        footer.addStretch(1)
        footer.addWidget(self._inv_stones)
        iv.addLayout(footer)
        tabs.addTab(inv, "Inventory")

        self._journal_view = QTextEdit()
        self._journal_view.setObjectName("Log")
        self._journal_view.setReadOnly(True)
        tabs.addTab(self._journal_view, "Journal")

        self._status_view = QTextEdit()
        self._status_view.setObjectName("Log")
        self._status_view.setReadOnly(True)
        tabs.addTab(self._status_view, "Status")

        self._tech_view = QTextEdit()
        self._tech_view.setObjectName("Log")
        self._tech_view.setReadOnly(True)
        tabs.addTab(self._tech_view, "Techniques")
        return tabs

    # -- bottom event log -------------------------------------------------
    def _build_event_log(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setFixedHeight(148)
        v = QVBoxLayout(panel)
        v.setContentsMargins(14, 8, 14, 10)
        v.setSpacing(4)
        header = QHBoxLayout()
        header.addWidget(self._section_title("Event Log"))
        header.addStretch(1)
        clear = self._btn("Clear Log", self._clear_log, "Ghost")
        header.addWidget(clear)
        v.addLayout(header)
        self._log_view = QTextEdit()
        self._log_view.setObjectName("Log")
        self._log_view.setReadOnly(True)
        v.addWidget(self._log_view, 1)
        return panel

    # -- small widget helpers --------------------------------------------
    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setObjectName("SectionTitle")
        return lbl

    def _caption(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("Caption")
        return lbl

    def _rich_label(self) -> QLabel:
        lbl = QLabel("-")
        lbl.setTextFormat(Qt.RichText)
        return lbl

    def _stat_row(self, label: str) -> tuple:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)
        name = QLabel(label)
        name.setObjectName("Caption")
        value = QLabel("-")
        value.setObjectName("StatValue")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h.addWidget(name)
        h.addStretch(1)
        h.addWidget(value)
        return row, value

    def _make_bar(self) -> QProgressBar:
        bar = QProgressBar()
        bar.setFixedHeight(16)
        bar.setTextVisible(True)
        bar.setAlignment(Qt.AlignCenter)
        return bar

    def _mini_bar(self, color: str) -> QProgressBar:
        bar = QProgressBar()
        bar.setFixedHeight(8)
        bar.setFixedWidth(150)
        bar.setTextVisible(False)
        bar.setRange(0, 1)
        bar.setValue(1)
        self._chunk(bar, color)
        return bar

    def _clear_log(self) -> None:
        self._log_view.clear()

    # -- state refresh ----------------------------------------------------
    def _refresh(self) -> None:
        state = self._engine.get_game_state()
        self._refresh_top_bar(state)
        self._refresh_character(state)
        self._refresh_location(state)
        self._refresh_tabs(state)

        if state.get("in_combat") and state.get("enemy"):
            e = state["enemy"]
            self._lbl_enemy.setText(f"{e['name']}  Lv.{e['level']}")
            self._set_bar(self._bar_enemy, e["hp"], e["max_hp"], T.hp_color(_ratio(e["hp"], e["max_hp"])))
            self._enemy_box.show()
            self._show_battle_menu()
        else:
            self._enemy_box.hide()
            self._show_explore_menu()

    def _refresh_top_bar(self, state: Dict[str, Any]) -> None:
        p = state["player"]
        self._lbl_player.setText(p.get("name", "-"))
        self._top_hp.setText(f"HP {p['hp']}/{p['max_hp']}")
        self._set_bar(self._bar_hp, p["hp"], p["max_hp"], T.HP_COLOR)
        self._top_qi.setText(f"Qi {p['qi']}/{p['max_qi']}")
        self._set_bar(self._bar_qi, p["qi"], p["max_qi"], T.QI_COLOR)
        # Day/time is cosmetic until the engine tracks a calendar; honour a
        # state["time"] block if one is ever supplied.
        time_info = state.get("time", {})
        self._day = time_info.get("day", self._day)
        self._period = time_info.get("period", self._period)
        self._top_time.setText(f"Day {self._day}\n{self._period}")

    def _refresh_character(self, state: Dict[str, Any]) -> None:
        p = state["player"]
        cs = p.get("cultivation_state", {})
        body = cs.get("body_transformation", {})
        essence = cs.get("essence_gathering", {})
        self._cp_name.setText(self._kv_html("Name", p.get("name", "-")))
        self._cp_path.setText(self._kv_html("Path", p.get("path", "Unassigned")))

        body_name = body.get("display_name", p.get("realm", "-"))
        body_progress = float(body.get("progress", p.get("progress", 0)))
        self._cp_body.setText(
            f"<span style='color:{T.TEXT_SECONDARY}'>Body:</span> "
            f"<span style='color:{T.BODY_GREEN};font-weight:bold'>{_esc(body_name)}</span>"
        )
        self._cp_progress.setText(
            f"<span style='color:{T.TEXT_SECONDARY}'>Progress:</span> {body_progress:.1f}%"
        )
        self._bar_body.setRange(0, 100)
        self._bar_body.setValue(int(body_progress))
        self._bar_body.setFormat(f"{body_progress:.1f}%")
        self._chunk(self._bar_body, T.BODY_GREEN)
        self._cp_foundation.setText(
            f"<span style='color:{T.TEXT_SECONDARY}'>Foundation:</span> "
            f"<span style='color:{T.BODY_GREEN}'>{body.get('foundation', 0)}</span>"
        )
        self._cp_strength.setText(
            f"<span style='color:{T.TEXT_SECONDARY}'>Strength:</span> "
            f"<span style='color:{T.BODY_GREEN}'>{body.get('body_strength', 0)}</span>"
        )

        essence_unlocked = bool(p.get("essence_unlocked", essence.get("unlocked", True)))
        if essence_unlocked:
            ename = essence.get("display_name", "-")
            eprog = float(essence.get("progress", 0))
            self._cp_essence.setText(
                f"<span style='color:{T.TEXT_SECONDARY}'>Essence:</span> "
                f"<span style='color:{T.ESSENCE_PURPLE};font-weight:bold'>{_esc(ename)}</span>"
                f" <span style='color:{T.TEXT_SECONDARY}'>- {eprog:.1f}%</span>"
            )
            self._cp_essence_req.setVisible(False)
        else:
            self._cp_essence.setText(
                f"<span style='color:{T.TEXT_SECONDARY}'>Essence:</span> "
                f"<span style='color:{T.ESSENCE_PURPLE};font-weight:bold'>Locked</span>"
            )
            req = essence.get("unlock_requirement", "")
            self._cp_essence_req.setText(
                f"<span style='color:{T.TEXT_MUTED}'>Requirement: {_esc(req)}</span>" if req else ""
            )
            self._cp_essence_req.setVisible(bool(req))

        self._cp_atk.setText(f"{p.get('attack', 0)}")
        self._cp_def.setText(f"{p.get('defense', 0)}")
        self._cp_comp.setText(f"{p.get('comprehension', 0)}")
        self._cp_rep.setText(f"{p.get('reputation', 0)}")

    def _refresh_location(self, state: Dict[str, Any]) -> None:
        loc = state.get("location", {})
        name = loc.get("display_name", loc.get("name", "Unknown"))
        self._loc_name.setText(name.upper())
        self._artwork_label.setText(name)
        self._loc_desc.setText(loc.get("description", ""))
        danger = loc.get("danger", "?")
        qi = loc.get("qi_density", "?")
        resources = ", ".join(loc.get("resources", [])) or "None"
        self._loc_meta.setText(
            f"<span style='color:{T.TEXT_SECONDARY}'>Danger:</span> "
            f"<span style='color:{_danger_color(danger)};font-weight:bold'>{_esc(danger)}</span>"
            f"&nbsp;&nbsp;|&nbsp;&nbsp;<span style='color:{T.TEXT_SECONDARY}'>Qi Density:</span> "
            f"<span style='color:{T.QI_COLOR}'>{_esc(qi)}</span>"
            f"&nbsp;&nbsp;|&nbsp;&nbsp;<span style='color:{T.TEXT_SECONDARY}'>Resources:</span> "
            f"<span style='color:{T.GOLD}'>{_esc(resources)}</span>"
        )
        exits = ", ".join(c.get("name", c.get("id", "?")) for c in loc.get("connections", [])) or "None"
        self._loc_exits.setText(
            f"<span style='color:{T.TEXT_SECONDARY}'>Exits:</span> "
            f"<span style='color:{T.INVENTORY_BLUE}'>{_esc(exits)}</span>"
        )

    def _refresh_tabs(self, state: Dict[str, Any]) -> None:
        p = state["player"]
        items = self._engine.get_inventory_items()
        self._inv_count.setText(f"{len(items)} / {self._inv_capacity}")
        self._inv_list.setHtml(self._inventory_html(items))
        self._inv_gold.setText(f"Gold: {p.get('gold', 0)}")
        stones = next((it["count"] for it in items if it["item_id"] == "spirit_stone"), 0)
        self._inv_stones.setText(f"Spirit Stones: {stones}")
        self._journal_view.setHtml(self._journal_html(state.get("quests", [])))
        self._status_view.setHtml(self._status_html(p))
        self._tech_view.setHtml(self._techniques_html())

    # -- tab content (presentation only) ---------------------------------
    def _kv_html(self, label: str, value: Any) -> str:
        return (
            f"<span style='color:{T.TEXT_SECONDARY}'>{_esc(label)}:</span> "
            f"<span style='color:{T.TEXT_PRIMARY};font-weight:bold'>{_esc(value)}</span>"
        )

    def _inventory_html(self, items: List[Dict[str, Any]]) -> str:
        if not items:
            return f"<div style='color:{T.TEXT_MUTED}'>Your storage ring is empty.</div>"
        parts: List[str] = []
        for it in items:
            parts.append(
                "<table width='100%' cellspacing='0' cellpadding='2'><tr>"
                f"<td style='color:{T.TEXT_PRIMARY};font-weight:bold'>{_esc(it['name'])}</td>"
                f"<td align='right' style='color:{T.GOLD};font-weight:bold'>x{it['count']}</td>"
                "</tr></table>"
                f"<div style='color:{T.TEXT_MUTED};font-size:11px;margin:0 0 8px 0'>"
                f"{_esc(it.get('description', ''))}</div>"
            )
        return "".join(parts)

    def _journal_html(self, quests: List[Dict[str, Any]]) -> str:
        active = [q for q in quests if str(q.get("status", "")).lower() not in {"locked", "hidden"}]
        if not active:
            return f"<div style='color:{T.TEXT_MUTED}'>No active quests yet. Explore to uncover your path.</div>"
        parts: List[str] = []
        for q in active:
            parts.append(
                f"<div style='color:{T.GOLD};font-weight:bold;margin:2px 0'>{_esc(q.get('title', ''))}</div>"
            )
            parts.append(
                f"<div style='color:{T.TEXT_MUTED};font-size:11px;margin:0 0 4px 0'>"
                f"{_esc(str(q.get('status', '')).title())}</div>"
            )
            for obj in q.get("objectives", []):
                cur = obj.get("current", 0)
                req = obj.get("required", 1)
                color = T.SUCCESS if cur >= req else T.TEXT_SECONDARY
                parts.append(
                    f"<div style='color:{color};margin:0 0 2px 10px'>"
                    f"{_esc(obj.get('text', ''))}: {cur} / {req}</div>"
                )
            parts.append("<div style='margin:6px 0'>&nbsp;</div>")
        return "".join(parts)

    def _status_html(self, p: Dict[str, Any]) -> str:
        cs = p.get("cultivation_state", {})
        body = cs.get("body_transformation", {})
        balance = cs.get("balance", {})
        safety = cs.get("breakthrough_safety", {})

        def line(label: str, value: Any, color: str = T.TEXT_PRIMARY) -> str:
            return (
                "<table width='100%'><tr>"
                f"<td style='color:{T.TEXT_SECONDARY}'>{_esc(label)}</td>"
                f"<td align='right' style='color:{color};font-weight:bold'>{_esc(value)}</td>"
                "</tr></table>"
            )

        parts = [f"<div style='color:{T.GOLD};font-weight:bold;letter-spacing:1px'>DETAILED STATUS</div><br>"]
        parts.append(line("HP", f"{p.get('hp', 0)} / {p.get('max_hp', 0)}", T.HP_COLOR))
        parts.append(line("Qi", f"{p.get('qi', 0)} / {p.get('max_qi', 0)}", T.QI_COLOR))
        parts.append(line("Attack", p.get("attack", 0)))
        parts.append(line("Defense", p.get("defense", 0)))
        parts.append(line("Comprehension", p.get("comprehension", 0)))
        parts.append(line("Reputation", p.get("reputation", 0)))
        parts.append(line("Morality", p.get("morality", 0)))
        parts.append("<br>")
        parts.append(line("Body Foundation", body.get("foundation", 0), T.BODY_GREEN))
        parts.append(line("Body Strength", body.get("body_strength", 0), T.BODY_GREEN))
        parts.append(line("Soul Strength", p.get("soul_strength", 0), T.ESSENCE_PURPLE))
        parts.append(line("Foundation Quality", p.get("foundation_quality", 0)))
        parts.append(line("Balance", balance.get("status", "-")))
        parts.append(line("Breakthrough Safety", f"{safety.get('level', '-')} ({safety.get('score', 0)})"))
        parts.append("<br>")
        parts.append(line("Location", p.get("current_location", "-"), T.INVENTORY_BLUE))
        return "".join(parts)

    def _techniques_html(self) -> str:
        skills = self._engine.get_known_skills()
        if not skills:
            return f"<div style='color:{T.TEXT_MUTED}'>You have not learned any techniques yet.</div>"
        parts: List[str] = []
        for s in skills:
            if s.get("type") == "active":
                meta = f"Active | Qi Cost: {s.get('qi_cost', 0)} | Cooldown: {s.get('cooldown', 0)}"
                color = T.GOLD
            else:
                meta = "Passive"
                color = T.INVENTORY_BLUE
            parts.append(
                f"<div style='color:{color};font-weight:bold;margin:2px 0'>{_esc(s.get('name', ''))}</div>"
            )
            parts.append(
                f"<div style='color:{T.TEXT_MUTED};font-size:11px;margin:0 0 6px 0'>{_esc(meta)}</div>"
            )
        return "".join(parts)

    def _set_bar(self, bar: QProgressBar, value: int, maximum: int, color: str) -> None:
        bar.setRange(0, max(1, maximum))
        bar.setValue(value)
        bar.setFormat(f"{value}/{maximum}")
        self._chunk(bar, color)

    def _chunk(self, bar: QProgressBar, color: str) -> None:
        bar.setStyleSheet(f"QProgressBar::chunk{{background-color:{color};border-radius:3px;}}")

    # -- action menus -----------------------------------------------------
    def _mount(self, widget: QWidget) -> None:
        while self._action_layout.count():
            item = self._action_layout.takeAt(0)
            old = item.widget()
            if old is not None:
                old.deleteLater()
        self._action_layout.addWidget(widget)

    def _btn(self, text: str, slot: Optional[Callable[[], None]], obj: str = "", enabled: bool = True) -> QPushButton:
        b = QPushButton(text)
        if obj:
            b.setObjectName(obj)
        b.setEnabled(enabled)
        b.setCursor(Qt.PointingHandCursor)
        if slot is not None:
            b.clicked.connect(lambda _checked=False: slot())
        return b

    def _action_card(
        self,
        title: str,
        subtitle: str,
        slot: Optional[Callable[[], None]],
        *,
        enabled: bool = True,
        locked_reason: str = "",
    ) -> QPushButton:
        """Build a two-line action card. Enabled/locked state comes from the
        engine (e.g. ``essence_unlocked``); the card never decides game rules."""
        card = QPushButton()
        card.setObjectName("ActionCard")
        card.setEnabled(enabled)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(52)
        card.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        if locked_reason:
            card.setToolTip(locked_reason)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(1)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("CardTitle")
        title_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        sub_lbl = QLabel(subtitle)
        sub_lbl.setObjectName("CardSub")
        sub_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        sub_lbl.setWordWrap(True)
        lay.addWidget(title_lbl)
        lay.addWidget(sub_lbl)
        if slot is not None:
            card.clicked.connect(lambda _checked=False: slot())
        return card

    def _show_explore_menu(self) -> None:
        state = self._engine.get_game_state()
        p = state["player"]
        essence = p.get("cultivation_state", {}).get("essence_gathering", {})
        essence_unlocked = bool(p.get("essence_unlocked", essence.get("unlocked", True)))
        req = essence.get("unlock_requirement", "")
        locked_reason = ""
        if not essence_unlocked:
            locked_reason = f"Locked - {req}." if req else "Essence Gathering is still locked."

        cards = [
            self._action_card(
                "Train Body", "Cultivate your body",
                lambda: self._do_action({"action": Action.TRAIN_BODY}),
            ),
            self._action_card(
                "Gather Essence",
                "Absorb spiritual energy" if essence_unlocked else "Locked",
                lambda: self._do_action({"action": Action.TRAIN_ESSENCE}),
                enabled=essence_unlocked, locked_reason=locked_reason,
            ),
            self._action_card(
                "Explore", "Search the area",
                lambda: self._do_action({"action": Action.EXPLORE}),
            ),
            self._action_card(
                "Rest", "Recover HP & Qi",
                lambda: self._do_action({"action": Action.REST}),
            ),
            self._action_card(
                "Body Breakthrough", "Attempt advancement",
                lambda: self._do_action({"action": Action.BODY_BREAKTHROUGH}),
            ),
            self._action_card(
                "Essence Breakthrough",
                "Attempt advancement" if essence_unlocked else "Locked",
                lambda: self._do_action({"action": Action.ESSENCE_BREAKTHROUGH}),
                enabled=essence_unlocked, locked_reason=locked_reason,
            ),
            self._action_card("Travel", "Move to another area", self._open_travel_dialog),
            self._action_card("Inventory", "Manage your items", lambda: self._focus_tab(0)),
        ]
        page = QWidget()
        grid = QGridLayout(page)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        for i, card in enumerate(cards):
            grid.addWidget(card, i // 4, i % 4)
        self._prompt.setText("What path will you walk?")
        self._mount(page)

    def _focus_tab(self, index: int) -> None:
        self._right_tabs.setCurrentIndex(index)

    def _open_travel_dialog(self) -> None:
        state = self._engine.get_game_state()
        destinations = state.get("destinations", [])
        dialog = QDialog(self)
        dialog.setWindowTitle("Travel")
        dialog.resize(360, 340)
        lay = QVBoxLayout(dialog)
        lay.addWidget(self._section_title("Choose a destination"))
        if not destinations:
            empty = QLabel("There is nowhere to travel from here.")
            empty.setObjectName("Caption")
            lay.addWidget(empty)
        for dest in destinations:
            reachable = bool(dest.get("reachable", True))
            label = f"{dest.get('display_name', dest.get('id', '?'))}   ({dest.get('danger', '?')})"
            btn = self._btn(label, None, "BagBtn", enabled=reachable)
            if reachable:
                btn.clicked.connect(
                    lambda _checked=False, loc=dest["id"]: self._travel_and_close(loc, dialog)
                )
            else:
                btn.setToolTip(dest.get("reason", "You cannot travel there yet."))
            lay.addWidget(btn)
        lay.addStretch(1)
        lay.addWidget(self._btn("Cancel", dialog.reject, "BattleBtn"))
        dialog.exec()

    def _travel_and_close(self, location_id: str, dialog: QDialog) -> None:
        dialog.accept()
        self._do_action({"action": Action.TRAVEL, "location_id": location_id})

    def _open_settings(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.resize(300, 300)
        lay = QVBoxLayout(dialog)
        lay.addWidget(self._section_title("Settings"))
        lay.addWidget(self._btn("Save Game", lambda: self._settings_action({"action": Action.SAVE}, dialog), "BagBtn"))
        lay.addWidget(self._btn("Load Game", lambda: self._settings_action({"action": Action.LOAD}, dialog), "BagBtn"))
        lay.addWidget(self._btn("Help", self._show_help_popup, "BagBtn"))
        lay.addWidget(self._btn("Quit Game", self.close, "BagBtn"))
        lay.addStretch(1)
        lay.addWidget(self._btn("Close", dialog.accept, "BattleBtn"))
        dialog.exec()

    def _settings_action(self, command: Dict[str, Any], dialog: QDialog) -> None:
        dialog.accept()
        self._do_action(command)

    def _show_battle_menu(self) -> None:
        page = QWidget()
        grid = QGridLayout(page)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        grid.addWidget(self._btn("FIGHT", self._show_move_menu, "BattlePrimary"), 0, 0)
        grid.addWidget(self._btn("BAG", self._show_bag_menu, "BattleBtn"), 0, 1)
        grid.addWidget(self._btn("STATS", self._show_status_popup, "BattleBtn"), 1, 0)
        grid.addWidget(self._btn("RUN", lambda: self._do_action({"action": Action.FLEE}), "BattleBtn"), 1, 1)
        name = self._engine.get_game_state()["player"]["name"]
        self._prompt.setText(f"What will {name} do?")
        self._mount(page)

    def _show_move_menu(self) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        info = QLabel("Choose a technique.")
        info.setObjectName("Caption")
        info.setWordWrap(True)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        for i, move in enumerate(self._battle_moves()[:4]):
            btn = _HoverButton(move["label"], on_hover=lambda m=move: info.setText(m["desc"]))
            btn.setObjectName("MoveBtn")
            btn.setEnabled(move["enabled"])
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(move["desc"])
            btn.clicked.connect(lambda _checked=False, m=move: self._pick_move(m))
            grid.addWidget(btn, i // 2, i % 2)

        outer.addWidget(grid_host)
        outer.addWidget(info)
        outer.addWidget(self._btn("Back", self._show_battle_menu, "BattleBtn"))
        self._prompt.setText("Choose your technique!")
        self._mount(page)

    def _show_bag_menu(self) -> None:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        items = [i for i in self._engine.get_inventory_items() if i["type"] == "consumable"]
        if not items:
            empty = QLabel("Your bag holds no usable items.")
            empty.setObjectName("Caption")
            v.addWidget(empty)
        for item in items:
            item_id = item["item_id"]
            btn = self._btn(
                f"{item['name']}    x{item['count']}",
                lambda iid=item_id: self._do_action({"action": Action.USE_ITEM, "item_id": iid}),
                "BagBtn",
            )
            btn.setToolTip(item.get("description", ""))
            v.addWidget(btn)
        v.addWidget(self._btn("Back", self._show_battle_menu, "BattleBtn"))
        self._prompt.setText("Use which item?")
        self._mount(page)

    def _battle_moves(self) -> List[Dict[str, Any]]:
        """Assemble the move list: a basic Strike plus each active technique."""
        moves: List[Dict[str, Any]] = [
            {
                "kind": "attack",
                "label": "Strike\n(basic)",
                "desc": "A basic strike with your fists. Costs no Qi.",
                "enabled": True,
            }
        ]
        for s in self._engine.get_known_skills():
            if s["type"] != "active":
                continue
            cd = s.get("cooldown_remaining", 0)
            qi = s.get("qi_cost", 0)
            if cd > 0:
                sub = f"CD {cd}"
            elif not s.get("affordable", True):
                sub = f"Qi {qi} (low)"
            else:
                sub = f"Qi {qi}"
            moves.append(
                {
                    "kind": "skill",
                    "id": s["id"],
                    "label": f"{s['name']}\n{sub}",
                    "desc": s.get("description", ""),
                    "enabled": cd == 0 and s.get("affordable", True),
                }
            )
        return moves

    def _pick_move(self, move: Dict[str, Any]) -> None:
        if move["kind"] == "attack":
            self._do_action({"action": Action.ATTACK})
        else:
            self._do_action({"action": Action.USE_SKILL, "skill_id": move["id"]})

    # -- command dispatch -------------------------------------------------
    def _do_action(self, command: Dict[str, Any]) -> None:
        result = self._engine.process_action(command)
        self._render(result)
        self._refresh()

    # -- rendering --------------------------------------------------------
    def _log(self, text: str, color: str = "") -> None:
        color = color or T.TEXT_PRIMARY
        raw = str(text)
        message = f'<span style="color:{color};">{_esc(raw)}</span>'
        if not raw.startswith(" "):
            # Prefix top-level lines with the current period, like "[Morning]".
            message = f'<span style="color:{T.TEXT_MUTED};">[{_esc(self._period)}]</span> ' + message
        self._log_view.append(message)
        scrollbar = self._log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _render(self, r: Dict[str, Any]) -> None:
        ev = r.get("event")
        if ev == EventType.TRAIN_RESULT:
            track = "Body" if r.get("track_id") == "body_transformation" else "Essence"
            track_color = T.BODY_GREEN if track == "Body" else T.ESSENCE_PURPLE
            self._log(r.get("player_message", f"You train your {track.lower()} cultivation."), track_color)
            exp_text = f"  (EXP +{r['exp_gained']})" if r.get("exp_gained") else ""
            self._log(f"{track} progress +{r['gained']}% -> {r['progress']}%{exp_text}.", T.TEXT_SECONDARY)
            if r.get("ready_to_breakthrough"):
                self._log("This path is ready for a breakthrough attempt.", T.GOLD)
        elif ev == EventType.BREAKTHROUGH_RESULT:
            self._render_breakthrough(r)
        elif ev == EventType.EXPLORE_RESULT:
            self._log(r.get("text", ""), T.TEXT_SECONDARY)
        elif ev == EventType.REST_RESULT:
            self._log(f"You rest and recover {r.get('healed', 0)} HP and {r.get('qi_restored', 0)} Qi.", T.SUCCESS)
        elif ev == EventType.MEDITATE_RESULT:
            gain = r.get("comprehension_gain", 0)
            extra = f"  Comprehension +{gain}." if gain else ""
            self._log(f"You meditate and restore {r.get('qi_restored', 0)} Qi.{extra}", T.QI_COLOR)
        elif ev == EventType.TRAVEL_RESULT:
            loc = r.get("location", {})
            self._log(f"You travel to {loc.get('display_name', loc.get('name', 'a new area'))}.", T.INVENTORY_BLUE)
        elif ev == EventType.COMBAT:
            e = r["enemy"]
            self._log(r.get("text", "A battle begins!"), T.DANGER)
            self._log(f"{e['name']} ({e.get('realm', 'Unknown Realm')}) appears!  HP {e['max_hp']}, ATK {e['attack']}, DEF {e['defense']}", T.TEXT_PRIMARY)
        elif ev == EventType.COMBAT_TURN:
            self._render_turn_events(r)
        elif ev == EventType.COMBAT_END:
            self._render_turn_events(r)
            self._render_combat_end(r)
        elif ev == EventType.LOOT:
            self._log(f"Obtained {r['name']} x{r['count']}  (you hold {r['total']}).", T.GOLD)
        elif ev == EventType.SPECIAL:
            self._render_special(r)
        elif ev == EventType.ITEM_USED:
            self._log(self._item_used_text(r), T.QI_COLOR)
        elif ev == EventType.SAVE_RESULT:
            self._log("Your journey has been recorded.", T.SUCCESS)
        elif ev == EventType.LOAD_RESULT:
            self._log("A saved journey resumes.", T.SUCCESS)
        elif ev == EventType.STATUS:
            self._focus_tab(2)
        elif ev == EventType.INVENTORY:
            self._focus_tab(0)
        elif ev == EventType.HELP:
            self._show_help_popup()
        elif ev == EventType.ERROR:
            self._log("! " + self._describe_error(r), T.DANGER)

    def _render_breakthrough(self, r: Dict[str, Any]) -> None:
        if r.get("success"):
            self._log(f"BREAKTHROUGH!   {r['previous']}  ->  {r['cultivation']}", T.ACCENT_GLOW)
            if r.get("realm_changed"):
                self._log("You ascend to a NEW REALM! The heavens tremble.", T.ACCENT_LINK)
            g = r.get("gains", {})
            self._log(f"  Max HP +{g.get('max_hp', 0)}  Max Qi +{g.get('max_qi', 0)}  ATK +{g.get('attack', 0)}  DEF +{g.get('defense', 0)}", T.SUCCESS)
        elif r.get("reason") == "INSUFFICIENT_PROGRESS":
            self._log(f"Not ready - progress {r['progress']}% (need 100%).", T.TEXT_SECONDARY)
        elif "progress_lost" in r:
            self._log(f"The Breakthrough FAILED! Your qi scatters - progress -{r['progress_lost']}% (now {r['progress']}%).", T.DANGER)
        else:
            self._log(r.get("player_message", f"Breakthrough cannot be attempted ({r.get('reason')})."), T.TEXT_SECONDARY)

    def _render_turn_events(self, r: Dict[str, Any]) -> None:
        for event in r.get("turn_events", []):
            text, color = self._turn_line(event)
            self._log("  " + text, color)

    def _render_combat_end(self, r: Dict[str, Any]) -> None:
        outcome = r.get("outcome")
        if outcome == "VICTORY":
            self._log(f"VICTORY! You have slain the {r.get('enemy_name')}.", T.SUCCESS)
            self._log(f"  EXP +{r.get('exp_reward', 0)}.", T.PHOENIX_ORANGE)
            loot = r.get("loot", [])
            if loot:
                for entry in loot:
                    self._log(f"  Loot: {entry['name']} x{entry['count']}.", T.PHOENIX_ORANGE)
            else:
                self._log("  No spoils this time.", T.TEXT_SECONDARY)
        elif outcome == "DEFEAT":
            penalty = r.get("penalty", {})
            self._log(f"DEFEAT... the {r.get('enemy_name')} overwhelms you.", T.DANGER)
            self._log(f"  An elder rescues you. Progress lost {penalty.get('progress_lost', 0)}%, revived at {penalty.get('revived_hp', 0)} HP.", T.TEXT_SECONDARY)
        elif outcome == "FLED":
            self._log(f"You escaped from the {r.get('enemy_name')}.", T.TEXT_SECONDARY)

    def _render_special(self, r: Dict[str, Any]) -> None:
        self._log(r.get("text", ""), T.ACCENT_LINK)
        if "progress_boost" in r:
            self._log(f"  Cultivation progress +{r['progress_boost']}% (now {r['progress']}%).", T.DRAGON_BLUE)
        if r.get("restored"):
            self._log(f"  Fully restored - HP {r['hp']}, Qi {r['qi']}.", T.SUCCESS)
        if "exp_gained" in r:
            self._log(f"  EXP +{r['exp_gained']}.", T.PHOENIX_ORANGE)

    def _turn_line(self, e: Dict[str, Any]) -> tuple:
        action = e.get("action")
        actor = e.get("actor")
        if action == "ATTACK" and actor == "PLAYER":
            return f"You strike for {e.get('damage')} damage.", T.SUCCESS
        if action == "ATTACK" and actor == "ENEMY":
            return f"{e.get('enemy_name', 'The enemy')} hits you for {e.get('damage')} damage.", T.DANGER
        if action == "SKILL":
            if "damage" in e:
                return f"You unleash {e.get('skill')} for {e.get('damage')} damage!", T.ACCENT_GLOW
            return f"You channel {e.get('skill')}.", T.DRAGON_BLUE
        if action == "USE_ITEM":
            extra = []
            if e.get("healed"):
                extra.append(f"+{e['healed']} HP")
            if e.get("qi_restored"):
                extra.append(f"+{e['qi_restored']} Qi")
            suffix = f"  ({', '.join(extra)})" if extra else ""
            return f"You use {e.get('item')}.{suffix}", T.DRAGON_BLUE
        if action == "FLEE_FAILED":
            return "You try to flee but fail to escape!", T.DANGER
        if action == "FLEE_SUCCESS":
            return "You slip away into the wilderness.", T.TEXT_SECONDARY
        return str(e), T.TEXT_PRIMARY

    def _item_used_text(self, r: Dict[str, Any]) -> str:
        parts = [f"You use {r['name']}."]
        if r.get("healed"):
            parts.append(f"Recovered {r['healed']} HP.")
        if r.get("qi_restored"):
            parts.append(f"Recovered {r['qi_restored']} Qi.")
        if "progress_boost" in r:
            parts.append(f"Cultivation +{r['progress_boost']}%.")
        return " ".join(parts)

    def _describe_error(self, r: Dict[str, Any]) -> str:
        reason = r.get("reason")
        table = {
            "NOT_ENOUGH_QI": f"Not enough Qi (need {r.get('required')}, have {r.get('qi')}).",
            "SKILL_ON_COOLDOWN": f"That technique is recovering ({r.get('remaining')} turn(s) left).",
            "ITEM_NOT_OWNED": f"You do not have '{r.get('item_id')}'.",
            "NO_ITEM_SPECIFIED": "No item selected.",
            "NOT_IN_COMBAT": "There is no enemy here.",
            "INVALID_IN_COMBAT": "You cannot do that mid-battle.",
            "SKILL_ONLY_IN_COMBAT": "Techniques can only be used in combat.",
            "UNKNOWN_COMMAND": f"Unknown command: {r.get('input', '')}.",
        }
        return table.get(reason, f"Something went wrong ({reason}).")

    # -- popups -----------------------------------------------------------
    def _show_status_popup(self) -> None:
        p = self._engine.process_action({"action": Action.STATUS})["player"]
        cultivation = p.get("cultivation_state", {})
        body = cultivation.get("body_transformation", {})
        essence = cultivation.get("essence_gathering", {})
        balance = cultivation.get("balance", {})
        safety = cultivation.get("breakthrough_safety", {})
        rows = [
            f"<h2 style='color:{T.ACCENT_GLOW};margin:0'>{_esc(p['name'])}</h2>",
            f"<p style='color:{T.TEXT_SECONDARY};margin:2px 0'>Body Transformation: {_esc(body.get('display_name', p.get('realm', '-')))} - Progress {body.get('progress', p.get('progress', 0))}% - Foundation {body.get('foundation', 0)}</p>",
            f"<p style='color:{T.TEXT_SECONDARY};margin:2px 0'>Essence Gathering: {_esc(essence.get('display_name', p.get('essence_cultivation', '-')))} - Progress {essence.get('progress', 0)}% - Dantian {essence.get('dantian_capacity', 0)}</p>",
            f"<p style='color:{T.TEXT_SECONDARY};margin:2px 0'>Balance: {_esc(balance.get('status', '-'))} - Safety {safety.get('level', '-')} ({safety.get('score', 0)})</p>",
            f"<p style='margin:2px 0'>HP {p['hp']}/{p['max_hp']} &nbsp; Qi {p['qi']}/{p['max_qi']}</p>",
            f"<p style='margin:2px 0'>ATK {p['attack']} &nbsp; DEF {p['defense']} &nbsp; EXP {p['exp']} &nbsp; Gold {p['gold']}</p>",
            f"<h3 style='color:{T.PHOENIX_ORANGE};margin:8px 0 2px'>Techniques</h3>",
        ]
        for s in p.get("skills", []):
            if s.get("type") == "active":
                rows.append(f"<p style='margin:1px 0'>&bull; {_esc(s['name'])} <span style='color:{T.TEXT_SECONDARY}'>[active] Qi {s.get('qi_cost', 0)}, CD {s.get('cooldown', 0)}</span></p>")
            else:
                rows.append(f"<p style='margin:1px 0'>&bull; {_esc(s['name'])} <span style='color:{T.TEXT_SECONDARY}'>[passive]</span></p>")
        self._info_dialog("Status", "".join(rows))

    def _show_help_popup(self) -> None:
        html = f"""
            <h2 style='color:{T.ACCENT_GLOW};margin:0'>How to Play</h2>
            <p style='color:{T.TEXT_SECONDARY}'>The cultivator's loop: Train &rarr; Explore &rarr; Fight &rarr; Loot &rarr; Breakthrough.</p>
            <p><b style='color:{T.PHOENIX_ORANGE}'>Train Body</b> - raise Body Transformation progress.</p>
            <p><b style='color:{T.PHOENIX_ORANGE}'>Gather Essence</b> - raise Essence Gathering progress.</p>
            <p><b style='color:{T.PHOENIX_ORANGE}'>Breakthrough</b> - at 100% progress, advance the selected path (may fail).</p>
            <p><b style='color:{T.PHOENIX_ORANGE}'>Explore</b> - venture out for loot, encounters, or a fight.</p>
            <h3 style='color:{T.ACCENT_LINK};margin:8px 0 2px'>In battle (Pokemon-style)</h3>
            <p><b>FIGHT</b> opens your techniques - each shows Qi cost and cooldown.
            A technique is greyed out while on cooldown or if you lack Qi.</p>
            <p><b>BAG</b> uses an item, <b>STATS</b> shows your sheet, <b>RUN</b> attempts escape.</p>
        """
        self._info_dialog("Help", html)

    def _info_dialog(self, title: str, html: str) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(440, 380)
        layout = QVBoxLayout(dialog)
        view = QTextEdit()
        view.setObjectName("Log")
        view.setReadOnly(True)
        view.setHtml(f"<div style='color:{T.TEXT_PRIMARY}'>{html}</div>")
        layout.addWidget(view)
        close = QPushButton("Close")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()


def _ratio(value: int, maximum: int) -> float:
    return 0.0 if maximum <= 0 else value / maximum
