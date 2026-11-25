"""Shared Streamlit UI helpers: theme CSS, HTML snippets and small utilities."""
from __future__ import annotations

import html
from typing import Dict, Optional

import numpy as np
import streamlit as st

PURPLE, LAVENDER, INK, PANEL, LINE = "#8B5CF6", "#C4B5FD", "#0B0B14", "#14142A", "#2A2547"

CSS = """
<style>
.block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px;}
#MainMenu, footer {visibility: hidden;}
h1, h2, h3 {letter-spacing: -0.01em;}
div.stButton > button, div.stDownloadButton > button {width: 100%; border-radius: 12px; font-weight: 600; padding: .55rem 1rem;}
div.stButton > button[kind="primary"] {background: linear-gradient(135deg,#8B5CF6,#6D3BE0); border: 0; color: #fff;}
div.stButton > button[kind="primary"]:hover {filter: brightness(1.12);}
textarea {font-size: 1.15rem !important; line-height: 1.5 !important;}
.sg-hero {border: 1px solid #3a2f6b; border-radius: 22px; padding: 2.6rem 2.4rem; margin-bottom: 1.4rem;
  background: radial-gradient(900px 340px at 8% -10%, rgba(139,92,246,.38), transparent 60%), linear-gradient(135deg,#17132f,#0b0b14);}
.sg-brand {font-size: 3.4rem; font-weight: 800; letter-spacing: .04em; line-height: 1.05; color: #fff; margin: 0;}
.sg-brand span {color: #A78BFA;}
.sg-sub {font-size: 1.25rem; color: #d8d0f5; margin: .5rem 0 .2rem 0;}
.sg-lede {color: #a9a3c7; max-width: 46rem; font-size: 1.02rem; line-height: 1.6;}
.sg-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 14px; margin: .6rem 0 1.2rem 0;}
.sg-card {background: #14142A; border: 1px solid #2A2547; border-radius: 16px; padding: 1.1rem 1.2rem;}
.sg-card h4 {margin: 0 0 .35rem 0; color: #E9E4FF; font-size: 1.05rem;}
.sg-card p {margin: 0; color: #a9a3c7; font-size: .93rem; line-height: 1.5;}
.sg-card .ico {font-size: 1.6rem; margin-bottom: .3rem; display: block;}
.sg-note {border-left: 4px solid #8B5CF6; background: #17163a; border-radius: 10px; padding: .9rem 1.1rem; color: #d8d0f5; margin: 1rem 0;}
.sg-badges {display: flex; flex-wrap: wrap; gap: 8px; margin: .5rem 0;}
.sg-badge {display: inline-flex; align-items: center; gap: 7px; padding: 5px 12px; border-radius: 999px; font-size: .85rem; border: 1px solid #2A2547; background: #14142A; color: #d8d0f5;}
.sg-badge i {width: 9px; height: 9px; border-radius: 50%; display: inline-block; background: #6b6590;}
.sg-badge.ok i {background: #4ADE80; box-shadow: 0 0 8px #4ADE80;} .sg-badge.ok {border-color: #1f6b42;}
.sg-badge.warn i {background: #FBBF24;} .sg-badge.warn {border-color: #7a5c14;}
.sg-badge.err i {background: #F87171;} .sg-badge.err {border-color: #7a2a2a;}
.sg-gesture {background: #14142A; border: 1px solid #2A2547; border-radius: 18px; padding: 1.1rem 1.3rem; margin-bottom: .8rem;}
.sg-gesture .name {font-size: 1.9rem; font-weight: 700; color: #fff; line-height: 1.2;}
.sg-gesture .word {font-size: 1.05rem; color: #C4B5FD; margin-top: .15rem;}
.sg-gesture.unknown .name {color: #9b95b8;}
.sg-meter {height: 10px; border-radius: 999px; background: #241f45; overflow: hidden; margin: .35rem 0 .15rem 0;}
.sg-meter > div {height: 100%; border-radius: 999px; background: linear-gradient(90deg,#6D3BE0,#A78BFA);}
.sg-meter.hold > div {background: linear-gradient(90deg,#8B5CF6,#C4B5FD);}
.sg-meter.done > div {background: #4ADE80;}
.sg-cap {font-size: .82rem; color: #8f89b0;}
.sg-chips {display: flex; gap: 6px; flex-wrap: wrap; margin: .6rem 0;}
.sg-chip {padding: 4px 10px; border-radius: 8px; font-size: .8rem; border: 1px solid #2A2547; color: #8f89b0; background: #101024;}
.sg-chip.on {background: #2a1f5c; border-color: #8B5CF6; color: #fff;}
.sg-kv {display: grid; grid-template-columns: auto 1fr; gap: 4px 14px; font-size: .9rem; color: #d8d0f5; margin-top: .4rem;}
.sg-kv span:nth-child(odd) {color: #8f89b0;}
.sg-recent {font-size: .9rem; color: #d8d0f5; padding: 3px 0; border-bottom: 1px solid #1d1a38;}
.sg-recent small {color: #8f89b0;}
.sg-hist {font-size: 1.1rem; color: #fff; line-height: 1.5;}
.sg-hist-meta {color: #8f89b0; font-size: .85rem;}
@media (max-width: 640px) {.sg-brand {font-size: 2.4rem;} .sg-hero {padding: 1.6rem 1.2rem;}}
</style>
"""

_image_width_mode: Optional[str] = None


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def show_image(img: np.ndarray, caption: str = "") -> None:
    """Show an RGB array at full column width on both old and new Streamlit versions."""
    global _image_width_mode
    kwargs = dict(channels="RGB", output_format="JPEG", caption=caption or None)
    if _image_width_mode in (None, "stretch"):
        try:
            st.image(img, width="stretch", **kwargs)
            _image_width_mode = "stretch"
            return
        except Exception:
            _image_width_mode = "legacy"
    st.image(img, use_container_width=True, **kwargs)


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def badge(label: str, kind: str = "off") -> str:
    return f'<span class="sg-badge {kind}"><i></i>{esc(label)}</span>'


def badges(*items: str) -> str:
    return '<div class="sg-badges">' + "".join(items) + "</div>"


def card(icon: str, title: str, body: str) -> str:
    return f'<div class="sg-card"><span class="ico">{icon}</span><h4>{esc(title)}</h4><p>{esc(body)}</p></div>'


def grid(*cards: str) -> str:
    return '<div class="sg-grid">' + "".join(cards) + "</div>"


def meter(value: float, css: str = "") -> str:
    pct = int(max(0.0, min(1.0, value)) * 100)
    return f'<div class="sg-meter {css}"><div style="width:{pct}%"></div></div>'


def finger_chips(fingers: Dict[str, bool]) -> str:
    chips = "".join(f'<span class="sg-chip {"on" if on else ""}">{esc(name.capitalize())}</span>'
                    for name, on in fingers.items())
    return f'<div class="sg-chips">{chips}</div>'


def kv(rows: Dict[str, str]) -> str:
    return '<div class="sg-kv">' + "".join(f"<span>{esc(k)}</span><span>{esc(v)}</span>" for k, v in rows.items()) + "</div>"


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
