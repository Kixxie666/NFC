import tkinter as tk
from tkinter import PhotoImage
import threading
import queue
import RPi.GPIO as GPIO
from pn532 import PN532_I2C
import pn532.pn532 as nfc
import requests
from Adafruit_IO import *
from PCP import send_score_to_mysql

# connect to adafruit
aio = Client('Kixxie','aio_wZDo830lu7XEfbSOBj6R4lsnXj80')

# Queue to communicate between threads
message_queue = queue.Queue()

# Function to continuously read messages from the queue and update the console window
def update_console(console):
    while True:
        message = message_queue.get()
        console.config(state=tk.NORMAL)
        console.insert(tk.END, message + "\n")
        console.config(state=tk.DISABLED)
        console.see(tk.END)
        message_queue.task_done()

# Function to print message to console and put it in the message queue
def print_to_console(*args):
    message = " ".join(map(str, args))
    print(message)
    message_queue.put(message)

def send_score(score):
    filename = "test.pdf"  # Replace with actual filename
    #serverIP = "192.168.141.231"
    serverIP = "127.0.0.1"
    url = f"http://" + serverIP + ":5000/print-score"  # Adjust URL if needed
    data = {"score": score}  # Sending score as JSON data
    params = {'filename': filename}
    response = requests.post(url, json=data, params=params)

    if response.status_code == 201:
        print("printing voucher...")
        return "Score sent successfully!", 200
    else:
        return "Error:", response.json(), response.status_code

# Function to start the program
def start_program():
    print_to_console("Program started!")
    try:
        # Initialize PN532 module with appropriate parameters
        pn532 = PN532_I2C(debug=False, reset=20, req=16)

        # Get firmware version of PN532 module
        ic, ver, rev, support = pn532.get_firmware_version()
        #print_to_console('Found PN532 with firmware version:', ver, rev)

        # Configure PN532 for MiFare Classic communication
        pn532.SAM_configuration()

        #print_to_console('Waiting for RFID/NFC card...')

        # Function to continuously check for NFC card presence
        def check_card_presence():
            while True:
                # Check for card presence with a timeout of 1 second
                uid = pn532.read_passive_target(timeout=1)

                #print_to_console("UID:", uid)  # Print the UID for debugging

                # Attempt to write data to block 6 if card is present
                if uid is not None:
                    # Define block number and key (modify if needed)
                    block_number = 10
                    key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'

                    # Ensure string fits within block size
                    max_length = 16
                    string_to_write = "Kamil, 1900"
                    if len(string_to_write) > max_length:
                        print_to_console("String too long! Max length for block", 10, "is", max_length)
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
                        # if pn532.mifare_classic_read_block(block_number) == data_to_write:
                        #     print_to_console('Wrote', string_to_write, 'to block %d successfully' % block_number)

                    except nfc.PN532Error as e:
                        print_to_console(e.errmsg)

                # Read the written block and print the contents
                data_read = pn532.mifare_classic_read_block(block_number)
                string_read = data_read.rstrip(b'\x00').decode('utf-8')
                data_to_db = string_read.split(",")
                # send data to ada fruit
                print_to_console("printing voucher...")
                aio.send("discount",string_read)
                send_score(score=string_read)
                print_to_console("Voucher printed!")
                send_score_to_mysql(user_name = data_to_db[0] , score = data_to_db[1])
                #print_to_console("Read from block", block_number, ":", string_read)

                break

        # Start the thread to check for card presence
        card_presence_thread = threading.Thread(target=check_card_presence)
        card_presence_thread.daemon = True
        card_presence_thread.start()

    except Exception as e:
        print_to_console(e)  

    def cleanup_gpio():
        GPIO.cleanup()

# GUI
root = tk.Tk()
root.title("RFID/NFC Reader")
root.geometry("278x600")

banner_image = PhotoImage(file="banner.png") 
banner_label = tk.Label(root, image=banner_image)
banner_label.pack()

console_frame = tk.Frame(root)
console_frame.pack(fill=tk.BOTH, expand=True)

console = tk.Text(console_frame, state=tk.DISABLED)
console.pack(fill=tk.BOTH, expand=True)

print_to_console("Insert card and press 'PRINT'")
print_button = tk.Button(root, text="PRINT", command=start_program)
print_button.pack()

console_update_thread = threading.Thread(target=update_console, args=(console,))
console_update_thread.daemon = True
console_update_thread.start()

root.mainloop()
