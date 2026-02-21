import base64

with open("ngPy.ico", "rb") as f:
    data = f.read()
b64 = base64.b64encode(data)
print(b64.decode())