"""Lightweight animation / video frame-sequence renderer.

Produces short animated GIF previews with PIL only (no ffmpeg needed),
so browsers can render them inline as video feedback. Used for Mia's
avatar motion previews and daily-briefing visual snippets.
"""
from __future__ import annotations

import time
from pathlib import Path

from core.config import settings


def get_outputs_dir(override: str | Path | None = None) -> Path:
    base = Path(__file__).resolve().parent.parent
    out = Path(override) if override else base / getattr(settings, "MIA_OUTPUTS_DIR", "outputs")
    if not out.is_absolute():
        out = base / out
    out.mkdir(parents=True, exist_ok=True)
    return out


def render_gif(
    label: str = "Mia",
    prompt: str = "",
    frames: int = 12,
    fps: int = 6,
    width: int = 320,
    height: int = 240,
    output_dir: str | Path | None = None,
) -> dict:
    """Render a hue-cycling captioned GIF. Returns {ok, path, url, frames, fps}."""
    from PIL import Image, ImageDraw

    frames = max(2, min(int(frames), 48))
    fps = max(1, min(int(fps), 24))
    out_dir = get_outputs_dir(output_dir)
    fname = f"mia_preview_{int(time.time())}.gif"
    path = out_dir / fname

    caption = (prompt[:42] + "…") if len(prompt) > 42 else (prompt or label)
    imgs = []
    for i in range(frames):
        hue_shift = int(255 * i / frames)
        img = Image.new("RGB", (width, height), (20 + hue_shift // 6, 30, 60 + hue_shift // 3))
        d = ImageDraw.Draw(img)
        # bouncing bar as a motion cue
        x = int((width - 60) * i / max(frames - 1, 1))
        d.rectangle([x, height - 30, x + 60, height - 18], fill=(56, 189, 248))
        d.text((12, 12), f"Mia · {label[:28]}", fill=(224, 242, 254))
        d.text((12, 32), caption, fill=(148, 197, 255))
        d.text((12, height - 52), f"frame {i + 1}/{frames}", fill=(100, 116, 139))
        imgs.append(img)

    imgs[0].save(
        path, save_all=True, append_images=imgs[1:],
        duration=int(1000 / fps), loop=0,
    )
    return {
        "ok": True,
        "path": str(path),
        "url": f"/outputs/{fname}",
        "frames": frames,
        "fps": fps,
        "width": width,
        "height": height,
        "label": label,
    }
