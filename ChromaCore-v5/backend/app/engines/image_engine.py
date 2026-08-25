from io import BytesIO
from PIL import Image


def inspect_image(data: bytes) -> dict:
    """Deterministic image-engine baseline; replace/augment with a vision model adapter."""
    with Image.open(BytesIO(data)) as im:
        return {
            "engine": "pillow-baseline",
            "format": im.format,
            "mode": im.mode,
            "width": im.width,
            "height": im.height,
            "pixels": im.width * im.height,
        }
