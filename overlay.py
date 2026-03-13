"""
Overlay helper module.

Draws CAN message data onto webcam frames so operators can correlate
visual information with live bus traffic at a glance.
"""

from __future__ import annotations

from typing import List

import can
import cv2
import numpy as np

import config


# ── Colours (BGR) ──────────────────────────────────────────────────────────────
_BG_COLOUR   = (0,   0,   0)
_TEXT_CH1    = (0, 255,   0)   # green  for channel 1
_TEXT_CH2    = (0, 200, 255)   # yellow for channel 2
_HEADER_COL  = (255, 255, 255)


def draw_overlay(
    frame: np.ndarray,
    ch1_messages: List[can.Message],
    ch2_messages: List[can.Message],
) -> np.ndarray:
    """
    Return a copy of *frame* with a semi-transparent CAN data panel
    drawn in the top-left corner.

    Parameters
    ----------
    frame:
        BGR image captured from the webcam.
    ch1_messages:
        Latest messages from CAN channel 1.
    ch2_messages:
        Latest messages from CAN channel 2.
    """
    if not config.OVERLAY_CAN:
        return frame

    out = frame.copy()
    font       = cv2.FONT_HERSHEY_SIMPLEX
    scale      = config.OVERLAY_FONT_SCALE
    thickness  = config.OVERLAY_THICKNESS
    line_h     = int(cv2.getTextSize("A", font, scale, thickness)[0][1] * 2.2)
    pad        = 6
    max_rows   = config.OVERLAY_MAX_ROWS

    # Build text lines
    lines: list[tuple[str, tuple[int, int, int]]] = []
    lines.append(("── CAN Channel 1 ──", _HEADER_COL))
    recent_ch1 = ch1_messages[-max_rows // 2:] if ch1_messages else []
    if recent_ch1:
        for msg in recent_ch1:
            lines.append((
                f"  ID:0x{msg.arbitration_id:03X}  [{msg.dlc}]  {msg.data.hex(' ')}",
                _TEXT_CH1,
            ))
    else:
        lines.append(("  (no data)", _TEXT_CH1))

    lines.append(("── CAN Channel 2 ──", _HEADER_COL))
    recent_ch2 = ch2_messages[-max_rows // 2:] if ch2_messages else []
    if recent_ch2:
        for msg in recent_ch2:
            lines.append((
                f"  ID:0x{msg.arbitration_id:03X}  [{msg.dlc}]  {msg.data.hex(' ')}",
                _TEXT_CH2,
            ))
    else:
        lines.append(("  (no data)", _TEXT_CH2))

    # Measure panel
    panel_w = int(
        max(
            cv2.getTextSize(text, font, scale, thickness)[0][0]
            for text, _ in lines
        )
        + pad * 2
    )
    panel_h = line_h * len(lines) + pad * 2

    # Draw semi-transparent background
    overlay = out.copy()
    cv2.rectangle(overlay, (0, 0), (panel_w, panel_h), _BG_COLOUR, -1)
    cv2.addWeighted(overlay, 0.55, out, 0.45, 0, out)

    # Draw text
    for i, (text, colour) in enumerate(lines):
        y = pad + (i + 1) * line_h
        cv2.putText(out, text, (pad, y), font, scale, colour, thickness,
                    cv2.LINE_AA)

    return out
