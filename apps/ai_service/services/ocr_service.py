import subprocess
import tempfile
import os

class OCRService:
    def extract_text(self, image_path: str) -> str:
        """Extract text from an image using Tesseract OCR."""
        try:
            result = subprocess.run(
                ['tesseract', image_path, 'stdout', '-l', 'eng'],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip()
        except Exception as e:
            raise RuntimeError(f"OCR failed: {str(e)}")
