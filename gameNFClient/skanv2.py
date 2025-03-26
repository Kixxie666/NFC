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

message_queue = queue.Queue()


def update_console(console):
    while True:
        message = message_queue.get()
        console.config(state=tk.NORMAL)
        console.insert(tk.END, message + "\n")
        console.config(state=tk.DISABLED)
        console.see(tk.END)
        message_queue.task_done()


def print_to_console(*args):
    message = " ".join(map(str, args))
    print(message)
    message_queue.put(message)

def send_score(score):
    filename = "test.pdf"  
    #serverIP = "192.168.141.231"
    serverIP = "127.0.0.1"
    url = f"http://" + serverIP + ":5000/print-score" 
    data = {"score": score} 
    params = {'filename': filename}
    response = requests.post(url, json=data, params=params)

    if response.status_code == 201:
        print("printing voucher...")
        return "Score sent successfully!", 200
    else:
        return "Error:", response.json(), response.status_code

def start_program():
    print_to_console("Program started!")
    try:
        pn532 = PN532_I2C(debug=False, reset=20, req=16)

        ic, ver, rev, support = pn532.get_firmware_version()

        pn532.SAM_configuration()


        def check_card_presence():
            while True:
                uid = pn532.read_passive_target(timeout=1)


                if uid is not None:
                    block_number = 10
                    key_a = b'\xFF\xFF\xFF\xFF\xFF\xFF'

                    max_length = 16
                    string_to_write = "Kamil, 1900"
                    if len(string_to_write) > max_length:
                        print_to_console("String too long! Max length for block", 10, "is", max_length)
                        continue 

                    data_to_write = bytearray(string_to_write, 'utf-8')
                    data_to_write.extend(b'\x00' * (max_length - len(data_to_write)))

                    try:
                        
                        pn532.mifare_classic_authenticate_block(
                            uid, block_number=block_number, key_number=nfc.MIFARE_CMD_AUTH_A, key=key_a)

                       
                        pn532.mifare_classic_write_block(block_number, data_to_write)

                        # if pn532.mifare_classic_read_block(block_number) == data_to_write:
                        #     print_to_console('Wrote', string_to_write, 'to block %d successfully' % block_number)

                    except nfc.PN532Error as e:
                        print_to_console(e.errmsg)

                data_read = pn532.mifare_classic_read_block(block_number)
                string_read = data_read.rstrip(b'\x00').decode('utf-8')
                data_to_db = string_read.split(",")
                print_to_console("printing voucher...")
                aio.send("discount",string_read)
                send_score(score=string_read)
                print_to_console("Voucher printed!")
                send_score_to_mysql(user_name = data_to_db[0] , score = data_to_db[1])

                break

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
