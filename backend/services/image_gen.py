"""Hugging Face image-generation service (FLUX.2-klein / Qwen-Image).

- ImageGenClient talks to the HF Inference API via httpx.
- Character consistency: optional `character_ref` token is baked into the
  prompt plus a fixed identity phrase, and `seed` is pinned so re-renders
  of Mia's avatar stay uniform.
- Offline/no-key fallback: labelled placeholder PNG with PIL so the
  frontend still receives a preview instead of an error.
"""
from __future__ import annotations

import time
from pathlib import Path

import httpx

from core.config import settings

STYLE_PRESETS: dict[str, str] = {
    "portrait": "soft studio portrait, 85mm lens, gentle key light, clean background",
    "anime": "clean anime style, cel shading, expressive eyes, vibrant but soft palette",
    "realistic": "ultra realistic photo, natural skin texture, daylight, shallow depth of field",
    "schematic": "clean technical schematic, white background, precise linework, labelled parts",
    "diagram": "minimal flat vector diagram, pastel palette, clear labels, no photo texture",
}

CHARACTER_IDENTITY_PHRASE = "same consistent character identity, same face, same hairstyle"


def get_outputs_dir(override: str | Path | None = None) -> Path:
    base = Path(__file__).resolve().parent.parent
    out = Path(override) if override else base / getattr(settings, "MIA_OUTPUTS_DIR", "outputs")
    if not out.is_absolute():
        out = base / out
    out.mkdir(parents=True, exist_ok=True)
    return out


def get_profiles_file(output_dir: str | Path | None = None) -> Path:
    return get_outputs_dir(output_dir) / "avatar_profiles.json"


def build_prompt(prompt: str, style: str = "portrait", character_ref: str | None = None) -> str:
    suffix = STYLE_PRESETS.get(style, STYLE_PRESETS["portrait"])
    full = f"{prompt.strip()}, {suffix}"
    if character_ref:
        full += f", {CHARACTER_IDENTITY_PHRASE}, character token [{character_ref}]"
    return full


def _placeholder_png(path: Path, label: str, width: int = 512, height: int = 512) -> Path:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (width, height), (24, 33, 58))
    draw = ImageDraw.Draw(img)
    for i in range(0, height, 8):
        shade = 24 + int(30 * i / max(height, 1))
        draw.line([(0, i), (width, i)], fill=(shade, shade + 12, 58 + shade // 2))
    text = (label[:48] + "…") if len(label) > 48 else label
    draw.text((20, height // 2 - 20), "Mia [stub render]", fill=(125, 211, 252))
    draw.text((20, height // 2 + 5), text, fill=(226, 232, 240))
    img.save(path)
    return path


class ImageGenClient:
    def __init__(self, endpoint=None, api_key=None, model=None, timeout_seconds=120, output_dir=None):
        self.endpoint = endpoint or settings.HF_IMAGE_ENDPOINT
        self.api_key = api_key if api_key is not None else settings.HUGGINGFACE_API_KEY
        self.model = model or settings.HF_IMAGE_MODEL
        self.timeout = timeout_seconds
        self.output_dir = get_outputs_dir(output_dir)

    def _headers(self):
        headers = {"Accept": "image/png", "Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _stub_result(self, path, fname, prompt, seed, note):
        _placeholder_png(path, prompt)
        return {"ok": True, "stub": True, "note": note, "path": str(path),
                "url": f"/outputs/{fname}", "prompt": prompt, "seed": seed, "model": self.model}

    def generate(self, prompt, style="portrait", seed=None, character_ref=None,
                 width=512, height=512, steps=20, guidance_scale=7.0):
        full_prompt = build_prompt(prompt, style, character_ref)
        seed = seed if seed is not None else 42
        fname = f"mia_{style}_{seed}_{int(time.time())}.png"
        path = self.output_dir / fname
        payload = {"inputs": full_prompt, "parameters": {
            "seed": seed, "width": width, "height": height,
            "num_inference_steps": steps, "guidance_scale": guidance_scale}}
        if not self.api_key:
            return self._stub_result(path, fname, full_prompt, seed,
                                     "HUGGINGFACE_API_KEY not set — placeholder render.")
        try:
            r = httpx.post(self.endpoint, headers=self._headers(), json=payload, timeout=self.timeout)
            r.raise_for_status()
            ctype = r.headers.get("content-type", "")
            is_img = "image" in ctype or r.content[:8].startswith(b"\x89PNG") or r.content[:2] == b"\xff\xd8"
            if is_img:
                path.write_bytes(r.content)
                return {"ok": True, "stub": False, "path": str(path),
                        "url": f"/outputs/{fname}", "prompt": full_prompt, "seed": seed, "model": self.model}
            return {"ok": False, "error": f"unexpected content-type: {ctype or 'unknown'}"}
        except Exception as exc:
            return self._stub_result(path, fname, full_prompt, seed,
                                     f"HF request failed ({exc}) — placeholder render.")

    def generate_avatar(self, prompt, seed=None, character_ref=None, style="portrait"):
        return self.generate(prompt=prompt, style=style, seed=seed, character_ref=character_ref)

    def render_design(self, prompt, seed=None, width=768, height=512):
        return self.generate(prompt=prompt, style="schematic", seed=seed, width=width, height=height)


def save_profile(name, data, output_dir=None):
    import json
    f = get_profiles_file(output_dir)
    profiles = {}
    if f.exists():
        try:
            profiles = json.loads(f.read_text())
        except Exception:
            profiles = {}
    profiles[name] = data
    f.write_text(json.dumps(profiles, indent=2))
    return {"ok": True, "name": name, "profile": data}


def list_profiles(output_dir=None):
    import json
    f = get_profiles_file(output_dir)
    if not f.exists():
        return {"profiles": {}}
    try:
        return {"profiles": json.loads(f.read_text())}
    except Exception as exc:
        return {"profiles": {}, "error": str(exc)}

