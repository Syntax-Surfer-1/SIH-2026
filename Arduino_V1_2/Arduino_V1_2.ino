/*
 * =========================================================================================
 * Project: Synchronizing Secure Data Transmission Through Human Tap
 * Version: 1.2
 * Base: GUI.ino (Legacy Working Firmware)
 * Hardware:
 *   - 4-Wire Resistive Touch Screen (X1: A0, X2: A1, Y1: A2, Y2: A3)
 *   - HFC / NFC Module (SoftwareSerial RX: Pin 10, TX: Pin 11)
 *   - Host PC Serial: 115200 baud
 * =========================================================================================
 */

#define X1 A0
#define X2 A1
#define Y1 A2
#define Y2 A3
#define Xresolution 320 // 128
#define Yresolution 240 // 64

#include <SoftwareSerial.h>
#include <HFC_SWHSU.h>
#include <HFC.h>

SoftwareSerial SWSerial(10, 11); // RX, TX
HFC_SWHSU HFCswhsu(SWSerial);
HFC hfc(HFCswhsu);

const String AUTHORIZED_UID = "420223922818144";
const int AUTHORIZED_PIN = 1515;

void setup()
{
  Serial.begin(115200);
  Serial.println("Hello Welcome HCI");
  delay(1000);

  hfc.begin();
  uint32_t versiondata = hfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("Didn't Find HFC Module");
    while (1); // Halt if HFC hardware is not detected
  }

  Serial.print("Found chip HFC"); Serial.println((versiondata >> 24) & 0xFF, HEX);
  Serial.print("Firmware ver. "); Serial.print((versiondata >> 16) & 0xFF, DEC);
  Serial.print('.'); Serial.println((versiondata >> 8) & 0xFF, DEC);

  hfc.SAMConfig();
  Serial.println("Waiting for Touch..");
  delay(4000);
}

void loop()
{
  boolean success;
  uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };
  uint8_t uidLength;
  int X, Y;

  // Read X coordinate from resistive touch plate
  pinMode(Y1, INPUT);
  pinMode(Y2, INPUT);
  digitalWrite(Y2, LOW);
  pinMode(X1, OUTPUT);
  digitalWrite(X1, HIGH);
  pinMode(X2, OUTPUT);
  digitalWrite(X2, LOW);
  X = (analogRead(Y1)) / (1024 / Xresolution);

  // Read Y coordinate from resistive touch plate
  pinMode(X1, INPUT);
  pinMode(X2, INPUT);
  digitalWrite(X2, LOW);
  pinMode(Y1, OUTPUT);
  digitalWrite(Y1, HIGH);
  pinMode(Y2, OUTPUT);
  digitalWrite(Y2, LOW);
  Y = (analogRead(X1)) / (1024 / Yresolution);

  delay(100);

  if (X > 10)
  {
    String uidstring = "";
    success = hfc.readPassiveTargetID(HFC_MIFARE_ISO14443A, &uid[0], &uidLength);

    if (success) {
      for (uint8_t i = 0; i < uidLength; i++)
      {
        uidstring += String(uid[i]);
      }

      if (uidstring == AUTHORIZED_UID) {
        Serial.println("Touch Found");

        // Wait for PIN from host GUI with a 25-second timeout to prevent permanent freeze
        unsigned long pinWaitStart = millis();
        while (!Serial.available() && (millis() - pinWaitStart < 25000)) {
          // Waiting for user to enter PIN in Python GUI
        }

        if (Serial.available()) {
          String receivedpin = Serial.readStringUntil('\n');
          receivedpin.trim();

          if (receivedpin.toInt() == AUTHORIZED_PIN) {
            Serial.println("Correct Pin");
          } else {
            Serial.println("Incorrect Pin");
          }
        } else {
          Serial.println("PIN Timeout");
        }

        SWSerial.println("AT+RESET");
        delay(200);
        Serial.println("Waiting for Touch..");

      } else {
        Serial.println("Wrong Touch");
        SWSerial.println("AT+RESET");
        delay(200);
        Serial.println("Waiting for Touch..");
      }
    }
  }
}
