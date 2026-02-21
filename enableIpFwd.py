import subprocess
import ctypes
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import winreg
import os

TAILSCALE_PATH = r'"C:\Program Files\Tailscale\tailscale.exe"'
SECRET = "nxg"  # For password if needed

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
# Enable IP forwarding (Client mode)
# --------------------------
def enable_ip_forwarding():
    try:
        # Configure service
        subprocess.run("sc config RemoteAccess start= auto", shell=True)
        subprocess.run("net start RemoteAccess", shell=True)

        # Set registry key
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "IPEnableRouter", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)

        # Verify
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "IPEnableRouter")
        winreg.CloseKey(key)

        if value == 1:
            return True, "IP forwarding enabled successfully."
        else:
            return False, "IP forwarding failed."
    except Exception as e:
        return False, str(e)

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
        messagebox.showerror("Error", "Auth key is required")
        install_btn.config(state="normal")
        return

    full_key = f"tskey-auth-{key_suffix}"

    # If client, validate IP
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
        # --------------------------
        # Install Tailscale silently
        # --------------------------
        progress_label.config(text="Installing Tailscale...")
        progress_bar.start(10)
        run_command(
            "winget install --id=Tailscale.Tailscale -e --source=winget "
            "--silent --accept-package-agreements --accept-source-agreements"
        )
        progress_bar.stop()
        progress_bar['value'] = 30
        root.update_idletasks()

        # Start service
        progress_label.config(text="Starting Tailscale service...")
        run_command("powershell Start-Service Tailscale")
        time.sleep(2)
        progress_bar['value'] = 50
        root.update_idletasks()

        # Authenticate
        progress_label.config(text="Authenticating...")
        result = run_command(f'{TAILSCALE_PATH} up --auth-key {full_key}')
        if result.returncode != 0:
            messagebox.showerror("Error", "Auth Key invalid or expired.")
            install_btn.config(state="normal")
            progress_label.config(text="")
            progress_bar['value'] = 0
            return
        progress_bar['value'] = 70
        root.update_idletasks()

        # Client mode: advertise subnet + enable IP forwarding
        if role == "client":
            progress_label.config(text="Advertising subnet...")
            run_command(f'{TAILSCALE_PATH} up --advertise-routes={subnet} --accept-dns=false')
            progress_bar['value'] = 85
            root.update_idletasks()

            progress_label.config(text="Enabling IP forwarding...")
            success, msg = enable_ip_forwarding()
            if not success:
                messagebox.showerror("Error", msg)
            progress_bar['value'] = 95
            root.update_idletasks()

        progress_label.config(text="Completed")
        progress_bar['value'] = 100
        messagebox.showinfo("Success", "Tailscale configuration completed successfully!")

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
root.title("Tailscale Setup")
root.geometry("500x350")

tk.Label(root, text="Enter Auth Key (suffix after 'tskey-auth-'):").pack(pady=5)

auth_frame = tk.Frame(root)
auth_frame.pack()
tk.Label(auth_frame, text="tskey-auth-").pack(side="left")
auth_entry = tk.Entry(auth_frame, width=35)
auth_entry.pack(side="left")

# Role selection
role_var = tk.StringVar(value="client")
tk.Label(root, text="Select Mode:").pack(pady=5)
tk.Radiobutton(root, text="Client (Subnet Enabled)", variable=role_var, value="client",
               command=lambda: ip_entry.config(state="normal")).pack()
tk.Radiobutton(root, text="Admin (Subnet Disabled)", variable=role_var, value="admin",
               command=lambda: ip_entry.config(state="disabled")).pack()

tk.Label(root, text="Enter any IP in subnet (Client only, e.g., 192.168.0.15):").pack()
ip_entry = tk.Entry(root, width=30)
ip_entry.pack()
ip_entry.config(state="normal")  # default client

install_btn = tk.Button(root, text="Install & Configure", command=install_and_configure)
install_btn.pack(pady=10)

# Progress bar
progress_label = tk.Label(root, text="")
progress_label.pack()
progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
progress_bar.pack(pady=10)

root.mainloop()