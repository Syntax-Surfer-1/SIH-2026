# Human Tap Secure Data Transmission - Version 1.2

This version (V1.2) is built **strictly and directly from the legacy working code** (`GUI.ino` and `HCI2.py`), adding the exact requested navigation flow and control buttons without unwanted bloat.

---

## 📁 Directory Contents

```
NEW GUI/V1.2/
├── Arduino_V1_2/
│   └── Arduino_V1_2.ino   # Arduino firmware (open & upload in Arduino IDE)
├── app_v1_2.py            # Python Tkinter GUI
├── run_v1_2.bat           # 1-Click Windows launcher
└── README.md              # Documentation & Guide
```

---

## 🔄 User Workflow in V1.2

1. **Admin Login**:
   - Enter User ID and Password (default: `admin` / `123`).
   - Click **Login** or press **Enter**.

2. **COM Port & Speed Selection**:
   - Select your Arduino's **COM Port** (use the **🔄 Refresh** button if plugged in after launching).
   - Select **Baud Rate** (default: `115200`).
   - Click **Connect & Start Scan ➔**.
   - (Or click **Logout** to go back to Admin Login).

3. **Scanning**:
   - Connection is established in a background worker thread (GUI never freezes or becomes "Not Responding").
   - Status indicates: *"Waiting for Touch on 4-wire resistive matrix & HFC card..."*.
   - Tap the touch screen with authorized HFC/NFC card.

4. **PIN / Password Verification**:
   - When Arduino detects authorized tap and sends `"Touch Found"`, the PIN input box appears.
   - Enter the security PIN (default: `1515`) and click **Submit PIN** (or press **Enter**).
   - Arduino validates the PIN:
     - `"Correct Pin"` ➔ **Access Granted! Welcome!**
     - `"Incorrect Pin"` ➔ **Incorrect PIN! Access Denied.**
     - `"Wrong Touch"` ➔ **Wrong Touch Detected.**

5. **Persistent Action Buttons**:
   - **🔄 Re-Scan**: Resets the scanning view and flushes serial buffers so you can tap again immediately without disconnecting or logging out.
   - **🔌 COM Select**: Closes the serial port cleanly and returns to the COM Port & Baud Rate selection screen.
   - **🚪 Logout**: Closes the serial port, clears credentials, and returns to the Admin Login screen.

---

## ⚙️ Hardware Specifications

- **Arduino Board**: Arduino Uno / Mega / Nano
- **Resistive Touch Screen**: 4-Wire
  - `X1`: Analog Pin `A0`
  - `X2`: Analog Pin `A1`
  - `Y1`: Analog Pin `A2`
  - `Y2`: Analog Pin `A3`
- **HFC / NFC Module**:
  - `RX`: Digital Pin `10`
  - `TX`: Digital Pin `11`
- **Serial Baud Rate**: `115200`
- **Target UID**: `420217022818144`
- **Target PIN**: `1515`

---

## 🚀 How to Run

1. Open `Arduino_V1_2/Arduino_V1_2.ino` in Arduino IDE, select board and port, and click **Upload**.
2. Run the GUI:
   - Double-click `run_v1_2.bat`, or
   - In terminal run:
     ```bash
     python app_v1_2.py
     ```
