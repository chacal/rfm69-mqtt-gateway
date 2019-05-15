from RFM69 import Radio, FREQ_433MHZ
import time

node_id = 1
network_id = 50

with Radio(FREQ_433MHZ, node_id, network_id, isHighPower=True,
           power=50, interruptPin=15, resetPin=16, spiBus=0, spiDevice=1,
           autoAcknowledge=False) as radio:
    print ("Starting loop...")

    while True:
        for packet in radio.get_packets():
            radio.send_ack(packet.sender)
            print (packet)
        delay = 0.010
        time.sleep(delay)
