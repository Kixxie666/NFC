import RPi.GPIO as GPIO
from pn532 import PN532_I2C
import pn532.pn532 as nfc
import time
import requests
from Adafruit_IO import *


def send_score(score):
    filename = "test.pdf"  
    #serverIP = "192.168.7.164"
    serverIP = "127.0.0.1"
    url = "http://"+serverIP+":5000/print-score" 
    data = {"score": score}  
    params = {'filename': filename}
    response = requests.post(url, json=data, params=params)

    if response.status_code == 201:
        print("printing voucher...")
        return "Score sent successfully!", 200
    else:
        return "Error:", response.json(), response.status_code

try:
  pn532 = PN532_I2C(debug=False, reset=20, req=16)

  ic, ver, rev, support = pn532.get_firmware_version()
  print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

  pn532.SAM_configuration()

  print('Waiting for RFID/NFC card...')

  while True:
    uid = pn532.read_passive_target(timeout=1)

    print(uid) 

    if uid is not None:
      block_number = 10
      key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'

      max_length = 16
      string_to_write = "2200"
      if len(string_to_write) > max_length:
        print("String too long! Max length for block", 10, "is", max_length)
        continue 

      data_to_write = bytearray(string_to_write, 'utf-8')
      data_to_write.extend(b'\x00' * (max_length - len(data_to_write)))

      try:

        pn532.mifare_classic_authenticate_block(
            uid, block_number=block_number, key_number=nfc.MIFARE_CMD_AUTH_A, key=key_a)


        pn532.mifare_classic_write_block(block_number, data_to_write)

 
        if pn532.mifare_classic_read_block(block_number) == data_to_write:
          print(f'Wrote {string_to_write} to block %d successfully' % block_number)

      except nfc.PN532Error as e:
        print(e.errmsg)

 
    data_read = pn532.mifare_classic_read_block(block_number)
    string_read = data_read.rstrip(b'\x00').decode('utf-8')
    aio.send("discount",string_read)
    print("Read from block", block_number, ":", string_read)

    time.sleep(2) 

except Exception as e:
  print(e) 

finally:
  GPIO.cleanup()  
