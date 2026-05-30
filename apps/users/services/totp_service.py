import pyotp
import qrcode
import base64
from io import BytesIO

class TOTPService:
    def generate_secret(self, user) -> str:
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save(update_fields=['totp_secret'])
        return secret

    def get_qr_code(self, user) -> str:
        if not user.totp_secret:
            raise ValueError("TOTP not configured")
        totp = pyotp.TOTP(user.totp_secret)
        uri = totp.provisioning_uri(name=user.email, issuer_name="Memora")
        img = qrcode.make(uri)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
