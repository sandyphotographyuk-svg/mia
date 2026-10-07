"""Avatar + design-render endpoints (Phase 3)."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.image_gen import ImageGenClient, list_profiles, save_profile

router = APIRouter()
client = ImageGenClient()


class AvatarIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    style: str = "portrait"
    seed: int | None = None
    character_ref: str | None = None


class DesignIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    seed: int | None = None
    width: int = 768
    height: int = 512


class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    prompt: str = ""
    style: str = "portrait"
    seed: int | None = None
    character_ref: str | None = None


@router.post("/generate")
def generate_avatar(body: AvatarIn):
    return client.generate_avatar(
        prompt=body.prompt, seed=body.seed,
        character_ref=body.character_ref, style=body.style,
    )


@router.post("/render")
def render_design(body: DesignIn):
    return client.render_design(
        prompt=body.prompt, seed=body.seed,
        width=body.width, height=body.height,
    )


@router.get("/styles")
def styles():
    from services.image_gen import STYLE_PRESETS

    return {"styles": sorted(STYLE_PRESETS.keys())}


@router.post("/profiles")
def save_avatar_profile(body: ProfileIn):
    result = client.generate_avatar(
        prompt=body.prompt or body.name, seed=body.seed,
        character_ref=body.character_ref, style=body.style,
    )
    record = {"prompt": body.prompt, "style": body.style,
              "seed": result.get("seed"), "character_ref": body.character_ref,
              "url": result.get("url"), "path": result.get("path")}
    return save_profile(body.name, record)


@router.get("/profiles")
def get_profiles():
    return list_profiles()

