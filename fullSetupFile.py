#py -m pip install pyinstaller  ''install pyinstaller if you want to convert this to exe
#python -m PyInstaller --onefile --noconsole --icon=ngPy.ico fullSetupFile.py    ''run this command in terminal to convert to exe''

import subprocess
import ctypes
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import winreg
import base64
import tempfile
import os

TAILSCALE_PATH = r'"C:\Program Files\Tailscale\tailscale.exe"'

#
# Base64-encoded ICO data
icon_b64 = b"""AAABAAEAIAsAAAEAIADUBQAAFgAAACgAAAAgAAAAFgAAAAEAIAAAAAAAgAUAAMAOAADADgAAAAAAAAAAAADV2fT/ubfp/8HD7P+wsOX/7Ov4/8jL7//Avuv/yMnu/72+6v+1tuj/xsXt/8XG7f+rrOX/ycju/7W26f/k4fX/xsnv/7++6v+7ver/trbo/8nJ7v+8u+r/ysru/7m56f+5uen/tLTn/9DP8P+2t+n/tLPn/8rK7v+4t+j/+ff8/8nO8f+amN7/naDi/3p31P+Uld7/d3fU/6ak4v+KjNv/gYHX/3d20/+pqeP/e37X/3Vz0v/Bv+r/kJPe/8G86P+wtOj/qqjj/4KF2f+IhNf/wMHs/46O3P+pqOP/vr3q/7q66f+Zmt//oKHi/2ts0f+Rjtr/wsPs/4eH2f/h3fP//////9rb9P/R0PD/1dXy/87P8P/e3vX/0tLx/87O8P/U1PH/6en4/9na8//a2vT/6en4/8rK7//V1fL/29vz/+bm9//Ky+//3d30/+Hh9v/X1/L/3Nz0/8/P8P/h4fX/7u76/+rq+f/T0/H/3t71/+Tl9//Kye7/19fy/+bl9/+goOH/YGDO/5SU3v+Xl9//cXHT/2Jizv+QkN3/n5/h/3Z11P9RUcn/Xl7N/2do0P9oadD/paTj/4KC2P9cXc3/k5Pd/5ub4P9tbtL/XFzN/19fzv9mZtD/lpbf/5OT3v9dXc3/Tk7I/3Bw0/95edb/aWnQ/56e4f9ubtL/n5/i/yoqvf8cHLn/+Pj9//////9LS8f/CAiy//////+goOH/IyO7/zc3wf9IScb/rKzl/xUUtf/Pz/D/PT3C/3Fw0v//////Tk7I/wYFsv8VFbf/BASy/yMju//y8vv/VlbK/y8vv/8rK73/jY3c/3p61v81NcD//////2Bgzv87O8L/KCi8/xcXtv/19fz//////0ZGxf8HB7H/6+v5/yEhuP9dXcz/rq7m/6Ki4v//////iYna/wAArP89PcL//////4qK2v8AAKr/vr7r//////+iouL/Hx+6/6am4/8ICLD/mprg/52d4f/U1PL/b2/S/zAwvv//////WVnM/zo6wv8oKLz/Fxe3//f3/f//////RkbG/wkJs//j4/b/Ghq3/y0tvv9GRsb/RUXG//Ly+//NzfD/AACm/2tr0P//////QkLE/zQ0wP/+/v//nJzg/1JSyP8lJbn/lpbe/wEBsP9JScf/NDTA/5SU3v93d9X/NTXA//////9hYc7/NzfB/ygovP8XF7f/+Pj9//////9JScf/AwOx//z8/v9QUMn/NTXA/4SE2P+Dg9j/2tr0/yEhuP9sbNH/GBi1/7Cw5v9RUcn/NjbB//f3/f81NcD/Jia8/11dzf/S0vH/FBS2/2tr0f90dNP/uLjp/3h40/8LC7D/iIjb/xUVtP9kZM7/Kyu9/xkZuP/4+Pz//////zc3wf8MDLL/+Pj9/+/v+v92dtX/SkrH/2Jizv+enuH/cXHT//////+iouL/iYnb/39/1v8DA67/5+f4///////9/f///v7////////Bwez/W1vM/0NDxf+UlN7/uLjp/1JSyv9QUMj/e3vW/+vr+f8uLrv/AACr/xQUt/8SErX/AACp/15ezf///////Pz+/////////////////////////////f3+//39/v//////5ub3/yUlu/8PD7T/MDC//yQku/9CQsX/9vb8///////+/v///////////////////////////////////////4uL2/9ra9H/aWnQ/2tr0f+bm+D/8vL7///////9/f7/+/v+//v7/v/7+/7//f3///v7/v///////Pz+//v7/v//////7e35/6Cg4f+Dg9n/gYHY/5KS3f/7+/7//v7///r6/v/7+/7//f3+//39///7+/7/+/v+//v7/v/+/v//AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
"""


# --------------------------
# Admin check
# --------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

# --------------------------
# Run command hidden
# --------------------------
def run_command(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

# --------------------------
# Convert IP to subnet
# --------------------------
def ip_to_subnet(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return None
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return None
    parts[3] = '0'
    return '.'.join(parts) + '/24'

# --------------------------
# Enable IP forwarding (Client mode only)
# --------------------------
def enable_ip_forwarding():
    if role_var.get() != "client":
        return False
    try:
        subprocess.run("sc config RemoteAccess start= auto", shell=True)
        subprocess.run("net start RemoteAccess", shell=True)
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "IPEnableRouter", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)

        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "IPEnableRouter")
        winreg.CloseKey(key)
        return value == 1
    except:
        return False

# --------------------------
# Check Tailscale login status
# --------------------------
def tailscale_status():
    try:
        result = run_command(f'{TAILSCALE_PATH} ip -4')
        ip = result.stdout.strip()
        return bool(ip)
    except:
        return False

# --------------------------
# Update status bar every second
# --------------------------
def update_status_bar():
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "IPEnableRouter")
        winreg.CloseKey(key)
        ip_status = "Enabled" if value == 1 else "Disabled"
    except:
        ip_status = "Disabled"
    ts_status = "Logged In" if tailscale_status() else "Not Logged In"
    status_label.config(text=f"{current_time} | IP-: {ip_status} | Server-: {ts_status}")
    root.after(1000, update_status_bar)

# --------------------------
# Install & configure Tailscale
# --------------------------
def install_and_configure_thread():
    install_btn.config(state="disabled")
    progress_bar['value'] = 0
    root.update_idletasks()

    key_suffix = auth_entry.get().strip()
    role = role_var.get()
    ip_input = ip_entry.get().strip()

    if not key_suffix:
        messagebox.showerror("Error", "login key is required")
        install_btn.config(state="normal")
        return

    # Keep original logic: remove second-last 2 chars, keep last char
    full_key = f"tskey-auth-{key_suffix}"
    full_key = full_key[:-3] + full_key[-1]

    if role == "client":
        if not ip_input:
            messagebox.showerror("Error", "IP is required in client mode")
            install_btn.config(state="normal")
            return
        subnet = ip_to_subnet(ip_input)
        if subnet is None:
            messagebox.showerror("Error", "Invalid IP format")
            install_btn.config(state="normal")
            return

    try:
        # Install Tailscale silently
        progress_label.config(text="Installing Requirements...")
        progress_bar.start(10)
        run_command(
            "winget install --id=Tailscale.Tailscale -e --source=winget "
            "--silent --accept-package-agreements --accept-source-agreements"
        )
        progress_bar.stop()
        progress_bar['value'] = 30
        root.update_idletasks()

        # Start service
        progress_label.config(text="Starting services...")
        run_command("powershell Start-Service Tailscale")
        time.sleep(2)
        progress_bar['value'] = 50
        root.update_idletasks()

        # Authenticate only if not already logged in
        if not tailscale_status():
            progress_label.config(text="Authenticating with login key...")
            result = run_command(f'{TAILSCALE_PATH} up --auth-key {full_key}')
            if result.returncode != 0:
                messagebox.showerror("Error", "Key invalid or expired.")
                install_btn.config(state="normal")
                progress_label.config(text="")
                progress_bar['value'] = 0
                return
        progress_bar['value'] = 70
        root.update_idletasks()

        # Client mode: advertise subnet + enable IP forwarding
        if role == "client":
            progress_label.config(text="Enabling IP subnets...")
            run_command(f'{TAILSCALE_PATH} up --advertise-routes={subnet} --accept-dns=false')
            progress_bar['value'] = 85
            root.update_idletasks()

            progress_label.config(text="Enabling IP...")
            if not enable_ip_forwarding():
                messagebox.showwarning("Warning", "IP could not be enabled.")
            progress_bar['value'] = 95
            root.update_idletasks()

        # Admin mode: remove subnet advertisement
        elif role == "admin":
            progress_label.config(text="Removing IP subnet advertisement...")
            run_command(f'{TAILSCALE_PATH} up --advertise-routes= --accept-dns=false')
            progress_bar['value'] = 95
            root.update_idletasks()

        progress_label.config(text="Completed")
        progress_bar['value'] = 100
        messagebox.showinfo("Success", "configuration completed successfully!")

    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        install_btn.config(state="normal")
        progress_label.config(text="")
        progress_bar['value'] = 0

def install_and_configure():
    threading.Thread(target=install_and_configure_thread, daemon=True).start()

# --------------------------
# GUI Setup
# --------------------------
root = tk.Tk()
root.title("Nexgen Support setup")
root.geometry("520x360")

# Auth key
tk.Label(root, text="").pack(pady=5)
frame1 = tk.Frame(root)
frame1.pack(pady=5)

frame2 = tk.Frame(root, pady=5)
frame2.pack()

frame3 = tk.Frame(root, pady=5)
frame3.pack()

frame4 = tk.Frame(root, pady=5)
frame4.pack()

tk.Label(frame1, text="Enter Login Key-").pack(side="left")
auth_entry = tk.Entry(frame1, width=35)
auth_entry.pack(side="left")

# Role selection
role_var = tk.StringVar(value="client")
tk.Label(frame2, text="Select User Type:").pack(side="left", padx=5)
tk.Radiobutton(frame2, text="Client", variable=role_var, value="client",
               command=lambda: ip_entry.config(state="normal")).pack(side="left", padx=5)
tk.Radiobutton(frame2, text="Engineering", variable=role_var, value="admin",
               command=lambda: ip_entry.config(state="disabled")).pack(side="left", padx=5)

# IP entry
tk.Label(frame3, text="Enter plc IP in subnet (e.g., 192.168.0.15):").pack(side="left", padx=5)
ip_entry = tk.Entry(frame3, width=30)
ip_entry.pack(side="left", padx=5)
ip_entry.config(state="normal")  # default client

# Install button
install_btn = tk.Button(frame4, text="Install & Configure", command=install_and_configure)
install_btn.pack(pady=10)

# Progress bar
progress_label = tk.Label(root, text="")
progress_label.pack()
progress_bar = ttk.Progressbar(root, length=450, mode='determinate')
progress_bar.pack(pady=10)

# Status bar
status_label = tk.Label(root, text="", relief="sunken", anchor="w")
status_label.pack(side="bottom", fill="x")
update_status_bar()

# Write the icon to a temporary file at runtime
tmp_fd, tmp_path = tempfile.mkstemp(suffix=".ico")
with os.fdopen(tmp_fd, "wb") as f:
    f.write(base64.b64decode(icon_b64))
root.iconbitmap(tmp_path)  # Set the window icon
root.mainloop()