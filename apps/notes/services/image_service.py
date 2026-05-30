from PIL import Image
import os

class ImageService:
    def resize(self, input_path: str, output_path: str, width: int, height: int):
        with Image.open(input_path) as img:
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            img.save(output_path)

    def create_thumbnail(self, input_path: str, output_path: str, size: tuple = (200, 200)):
        with Image.open(input_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path)

    def compress(self, input_path: str, output_path: str, quality: int = 85):
        with Image.open(input_path) as img:
            img.save(output_path, optimize=True, quality=quality)
