import RPi.GPIO as GPIO
from pn532 import PN532_I2C
import pn532.pn532 as nfc
import time
import requests
from Adafruit_IO import *

#connect to ada fruit dashboard
aio = Client('Kixxie','aio_wZDo830lu7XEfbSOBj6R4lsnXj80')

def send_score(score):
    filename = "test.pdf"  # Replace with actual filename
    #serverIP = "192.168.7.164"
    serverIP = "127.0.0.1"
    url = "http://"+serverIP+":5000/print-score"  # Adjust URL if needed
    data = {"score": score}  # Sending score as JSON data
    params = {'filename': filename}
    response = requests.post(url, json=data, params=params)

    if response.status_code == 201:
        print("printing voucher...")
        return "Score sent successfully!", 200
    else:
        return "Error:", response.json(), response.status_code

# Initialize PN532
try:
  # Initialize PN532 module with appropriate parameters
  pn532 = PN532_I2C(debug=False, reset=20, req=16)

  # Get firmware version of PN532 module
  ic, ver, rev, support = pn532.get_firmware_version()
  print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

  # Configure PN532 for MiFare Classic communication
  pn532.SAM_configuration()

  print('Waiting for RFID/NFC card...')

  # Infinite loop to continuously check for NFC card presence
  while True:
    # Check for card presence with a timeout of 1 second
    uid = pn532.read_passive_target(timeout=1)

    print(uid)  # Print the UID for debugging

    # Attempt to write data to block 6 if card is present
    if uid is not None:
      # Define block number and key (modify if needed)
      block_number = 10
      key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'

      # Ensure string fits within block size
      max_length = 16
      string_to_write = "2200"
      if len(string_to_write) > max_length:
        print("String too long! Max length for block", 10, "is", max_length)
        continue  # Skip writing if string is too long

      # Convert string to byte array and pad with zeros
      data_to_write = bytearray(string_to_write, 'utf-8')
      data_to_write.extend(b'\x00' * (max_length - len(data_to_write)))

      try:
        # Authenticate block using key_a
        pn532.mifare_classic_authenticate_block(
            uid, block_number=block_number, key_number=nfc.MIFARE_CMD_AUTH_A, key=key_a)

        # Write data to block
        pn532.mifare_classic_write_block(block_number, data_to_write)

        # Verify successful write by reading back
        if pn532.mifare_classic_read_block(block_number) == data_to_write:
          print(f'Wrote {string_to_write} to block %d successfully' % block_number)

      except nfc.PN532Error as e:
        print(e.errmsg)

    # Read the written block and print the contents
    data_read = pn532.mifare_classic_read_block(block_number)
    string_read = data_read.rstrip(b'\x00').decode('utf-8')
    #send_score(score = string_read)
    #send data to ada fruit
    aio.send("discount",string_read)
    print("Read from block", block_number, ":", string_read)

    time.sleep(2)  # Wait for 2 seconds before next loop iteration

except Exception as e:
  print(e)  # Print any errors

finally:
  GPIO.cleanup()  # Ensure GPIO cleanup
