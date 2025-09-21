import requests

print("Testing image upload...")

# Create session
session_resp = requests.post("http://localhost:8001/api/session")
print(f"Session: {session_resp.status_code}")
cookies = session_resp.cookies

# Test image upload
with open("test/coaster_pen_mouse.jpg", "rb") as f:
    files = {"file": ("coaster_pen_mouse.jpg", f, "image/jpeg")}
    upload_resp = requests.post("http://localhost:8001/api/chat/image", files=files, cookies=cookies)
    print(f"Upload: {upload_resp.status_code}")
    print(f"Response: {upload_resp.text}")
