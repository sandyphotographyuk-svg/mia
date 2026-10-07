"""Animated preview endpoints (Phase 3 video frame-sequence renderer)."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.video_render import render_gif

router = APIRouter()


class PreviewIn(BaseModel):
    label: str = "Mia"
    prompt: str = ""
    frames: int = Field(default=12, ge=2, le=48)
    fps: int = Field(default=6, ge=1, le=24)


@router.post("/preview")
def preview(body: PreviewIn):
    return render_gif(label=body.label, prompt=body.prompt, frames=body.frames, fps=body.fps)
