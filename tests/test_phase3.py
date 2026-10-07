"""Phase 3 tests: prompt building, stub image gen, video renderer, routes."""
from pathlib import Path

from services import image_gen
from services.image_gen import ImageGenClient, build_prompt, list_profiles, save_profile
from services.video_render import render_gif


def _client(tmp_path: Path) -> ImageGenClient:
    return ImageGenClient(endpoint="http://stub", api_key="", output_dir=tmp_path)


def test_build_prompt_style_and_consistency():
    p = build_prompt("Mia smiling", style="anime", character_ref="mia-v1")
    assert "anime" in p.lower()
    assert "mia-v1" in p
    assert "same face" in p.lower()


def test_build_prompt_unknown_style_falls_back():
    p = build_prompt("hi", style="nope")
    assert "studio portrait" in p.lower()


def test_generate_stub_without_key(tmp_path):
    c = _client(tmp_path)
    res = c.generate_avatar(prompt="Mia portrait test", seed=7, character_ref="mia-v1")
    assert res["ok"] is True and res["stub"] is True
    assert res["seed"] == 7
    assert Path(res["path"]).exists()
    assert res["url"].startswith("/outputs/")


def test_generate_hf_failure_falls_back_to_stub(tmp_path, monkeypatch):
    import services.image_gen as ig

    def boom(url, headers=None, json=None, timeout=None):
        raise ConnectionError("hf down")

    monkeypatch.setattr(ig.httpx, "post", boom)
    c = ImageGenClient(endpoint="http://stub", api_key="key", output_dir=tmp_path)
    res = c.generate(prompt="x", seed=1)
    assert res["ok"] is True and res["stub"] is True
    assert Path(res["path"]).exists()


def test_generate_hf_image_bytes(tmp_path, monkeypatch):
    import services.image_gen as ig
    from PIL import Image
    import io

    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (1, 2, 3)).save(buf, format="PNG")

    class Resp:
        headers = {"content-type": "image/png"}
        content = buf.getvalue()

        def raise_for_status(self):
            pass

    monkeypatch.setattr(ig.httpx, "post", lambda *a, **k: Resp())
    c = ImageGenClient(endpoint="http://stub", api_key="key", output_dir=tmp_path)
    res = c.generate(prompt="x", seed=3)
    assert res["ok"] is True and res["stub"] is False
    assert Path(res["path"]).exists()


def test_render_design_uses_schematic(tmp_path, monkeypatch):
    seen = {}

    def fake_generate(self, **kwargs):
        seen.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(ImageGenClient, "generate", fake_generate)
    c = ImageGenClient(endpoint="http://stub", api_key="", output_dir=tmp_path)
    c.render_design(prompt="floor plan")
    assert seen["style"] == "schematic"


def test_profiles_roundtrip(tmp_path):
    assert list_profiles(tmp_path) == {"profiles": {}}
    save_profile("mia-default", {"style": "portrait"}, tmp_path)
    assert list_profiles(tmp_path)["profiles"]["mia-default"]["style"] == "portrait"


def test_render_gif(tmp_path):
    res = render_gif(label="test", prompt="hello", frames=4, fps=4, width=64, height=48, output_dir=tmp_path)
    assert res["ok"] is True
    assert res["frames"] == 4
    p = Path(res["path"])
    assert p.exists() and p.stat().st_size > 0
    assert res["url"].startswith("/outputs/")


def test_render_gif_clamps(tmp_path):
    res = render_gif(frames=500, fps=500, width=32, height=24, output_dir=tmp_path)
    assert res["frames"] == 48 and res["fps"] == 24


def test_avatar_routes():
    from fastapi.testclient import TestClient

    import main as app_module

    with TestClient(app_module.app) as t:
        r = t.get("/api/avatar/styles")
        assert r.status_code == 200 and "portrait" in r.json()["styles"]
        r = t.post("/api/avatar/generate", json={"prompt": "Mia smiling", "seed": 11})
        assert r.status_code == 200 and r.json()["ok"] is True
        r = t.post("/api/avatar/render", json={"prompt": "server rack"})
        assert r.status_code == 200 and r.json()["ok"] is True
        r = t.get("/api/avatar/profiles")
        assert r.status_code == 200 and "profiles" in r.json()


def test_render_route():
    from fastapi.testclient import TestClient

    import main as app_module

    with TestClient(app_module.app) as t:
        r = t.post("/api/render/preview", json={"label": "briefing", "frames": 3, "fps": 3})
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True and body["frames"] == 3
