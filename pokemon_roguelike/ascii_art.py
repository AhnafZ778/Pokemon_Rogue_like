"""Convert transparent raster sprites into color-aware character grids.

This is intentionally a small game-specific adapter around Pillow. It can be
extracted into a separate package later if the game develops requirements that
existing image-to-ASCII libraries do not satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageEnhance, ImageOps

CHARACTER_RAMP = " .,:;irsXA253hMHGS#9B&@"


@dataclass(frozen=True, slots=True)
class AsciiCell:
    character: str
    color: tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class AsciiSprite:
    rows: tuple[tuple[AsciiCell | None, ...], ...]

    @property
    def width(self) -> int:
        return len(self.rows[0]) if self.rows else 0

    @property
    def height(self) -> int:
        return len(self.rows)

    @classmethod
    def from_image_bytes(
        cls,
        image_bytes: bytes,
        width: int = 30,
        cell_aspect_ratio: float = 0.52,
        mirrored: bool = False,
    ) -> AsciiSprite:
        """Create a glyph grid while preserving transparency and sprite color."""

        if width < 1:
            raise ValueError("ASCII sprite width must be positive")

        with Image.open(BytesIO(image_bytes)) as source:
            image = source.convert("RGBA")
            if mirrored:
                image = ImageOps.mirror(image)

            bounds = image.getchannel("A").getbbox()
            if bounds is None:
                raise ValueError("Sprite image is fully transparent")
            image = image.crop(bounds)

            height = max(
                1,
                round(image.height / image.width * width * cell_aspect_ratio),
            )
            image = image.resize((width, height), Image.Resampling.LANCZOS)
            image = ImageEnhance.Color(image).enhance(1.25)
            image = ImageEnhance.Contrast(image).enhance(1.12)

            rows: list[tuple[AsciiCell | None, ...]] = []
            for y in range(image.height):
                row: list[AsciiCell | None] = []
                for x in range(image.width):
                    red, green, blue, alpha = image.getpixel((x, y))
                    if alpha < 42:
                        row.append(None)
                        continue

                    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
                    ramp_index = round(
                        luminance / 255 * (len(CHARACTER_RAMP) - 1)
                    )
                    character = CHARACTER_RAMP[max(1, ramp_index)]
                    row.append(AsciiCell(character, (red, green, blue)))
                rows.append(tuple(row))

        return cls(tuple(rows))
