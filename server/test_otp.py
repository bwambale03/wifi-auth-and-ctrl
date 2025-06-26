import pyotp
import time

# The otp_secret from the database
otp_secret = "OKZSKZ7WRFI3R56KSCPFIZ2Y6P3G54TN"

# Generate a TOTP code
totp = pyotp.TOTP(otp_secret)
current_code = totp.now()
print(f"Current TOTP code (server): {current_code}")

# Print the current timestamp for reference
print(f"Current server timestamp: {int(time.time())}")
