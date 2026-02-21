import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

# --------------------------
# Get list of network adapters
# --------------------------
def get_network_adapters():
    adapters = []
    try:
        result = subprocess.run("netsh interface show interface", 
                                shell=True, capture_output=True, text=True)
        lines = result.stdout.splitlines()
        for line in lines:
            line = line.strip()
            # Skip headers and empty lines
            if line.startswith("Admin") or not line:
                continue
            # Columns: Admin State, State, Type, Interface Name
            parts = line.split(None, 3)
            if len(parts) == 4:
                adapters.append(parts[3])
    except Exception as e:
        messagebox.showerror("Error", str(e))
    return adapters

# --------------------------
# Apply IP + subnet to adapter
# --------------------------
def set_ip(adapter, ip, subnet):
    try:
        cmd = f'netsh interface ipv4 set address name="{adapter}" static {ip} {subnet}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            messagebox.showinfo("Success", f"IP set for {adapter}")
        else:
            messagebox.showerror("Error", result.stderr)
    except Exception as e:
        messagebox.showerror("Error", str(e))

# --------------------------
# GUI
# --------------------------
def refresh_adapters():
    adapters = get_network_adapters()
    adapter_combo['values'] = adapters
    if adapters:
        adapter_combo.current(0)

def apply_ip():
    adapter = adapter_combo.get()
    ip = ip_entry.get().strip()
    subnet = subnet_entry.get().strip()
    if not adapter or not ip or not subnet:
        messagebox.showwarning("Warning", "All fields are required")
        return
    set_ip(adapter, ip, subnet)

root = tk.Tk()
root.title("Set Static IP")
root.geometry("450x250")

tk.Label(root, text="Select Network Adapter:").pack(pady=5)
adapter_combo = ttk.Combobox(root, width=40)
adapter_combo.pack()

tk.Button(root, text="Refresh Adapters", command=refresh_adapters).pack(pady=5)

tk.Label(root, text="Enter IP Address (e.g., 192.168.1.100):").pack(pady=5)
ip_entry = tk.Entry(root, width=30)
ip_entry.pack()

tk.Label(root, text="Enter Subnet Mask (e.g., 255.255.255.0):").pack(pady=5)
subnet_entry = tk.Entry(root, width=30)
subnet_entry.pack()

tk.Button(root, text="Apply IP", command=apply_ip).pack(pady=15)

# Initial load
refresh_adapters()

root.mainloop()