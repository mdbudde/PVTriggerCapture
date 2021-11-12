# PVTriggerCapture

A python script in combination with the LabJack U3 device to record timestamps in MRI sequences on the Paravision platform.

Briefly,
Connect the labjack to the USB of the console and the TTL2 port (BNC)
Within the sequences, functions that use TTL2_HIGH followed by TTL2_LOW will output the appropraite pulses for recording.

Start the captureTriggers.py in a terminal window on the console.

The program will monitor the system for the current status (scanning, idle, etc).
It will record to a text file the timestamps for each TTL2 pulse and the duration between successive pulses.

In our implementation, we used it to record the post-label delays in a arterial spin labelling with cardiac gating prior to image acquisition. Therefore, the PLDs were variable and this tool enabled us to record them for all of the scans.

