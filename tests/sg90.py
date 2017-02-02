from gpiozero import Servo
from time import sleep

s = Servo(18, initial_value=None, min_pulse_width=0.64/1000, max_pulse_width=1.2/1000, frame_width=100.0/1000)
print "trying min()"
s.min()
sleep(5)
print "trying mid()"
s.mid()
sleep(5)
print "trying max()"
s.max()
sleep(5)
#print "setting custom"
#s.value = 0.6
#sleep(2)
