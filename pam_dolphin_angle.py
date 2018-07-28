import numpy as np 
import math
from scipy.io import wavfile 
from sympy import *
import time

c = 1500.0 #sound speed m/s 
fs, data = wavfile.read('./pinger`.wav') #source wav file 
mic_fs, mic_data = wavfile.read('') #noise wav file
bits = 16
source_data = data/2**(bits-1)
source_data.astype('float64')
print("FS = ",fs)

class pingerStatus:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.guessx = 99.0
        self.guessy = 99.0
        self.guessAngle = 0
        self.realAngle = 0
        self.sl = 0.0

class micPosition:
    def __init__(self, x, y):
        self.x = x #mic position x  
        self.y = y #mic position y
        self.d = 0.0 #degree of mic 
        self.idt = 0.0 #ideal receive time 
        self.rt = 0.0 #ideal receive time
        self.tl = 0.0 #transmission lose
        self.rl = 0.0 #receive level

def receiveTime(x1, y1, x2, y2):
    t = (pow((x1-x2)**2+(y1-y2)**2, 0.5))
    t = t/c
    return t 

def receiverOrder(t1, t2):
    index = np.argmin([t1, t2])+1
    print("index = ", index)
    return index

def corrXT(a, b): 
    maxArgu = np.argmax(np.correlate(a, b, "full"))-b.size+1
    #print('maxArgu = ', maxArgu)
    real_recevie_t = round((maxArgu)/fs, 10)
    return real_recevie_t

def sourceToBoat(t1, t2):
    dt = t1-t2
    print("dt = ", dt)
    l = 2*boat_mic
    theta = 90-math.acos(c*dt/l)*180/np.pi
    print("cal angle = ", theta)
    print("realAngle = ", angle([source.x, source.y]))

def angle(pos):
    x, y = pos
    a = math.degrees(math.atan2(y-b.y, x-b.x))
    a = -a+90
    if a < 0:
        a = a+360
    return round(a, 1)

def addNoise(data):
    noise = (np.random.rand(data.size)*2-1)*0.25
    data = data + noise 
    return data 

source = pingerStatus(1500, 0)
A1 = micPosition(550, 0)
A2 = micPosition(0, 500)
A3 = micPosition(-550, 0)
while(1):
#    xx = float(input('x of boat = '))
#    yy = float(input('y of boat = '))
    time_start = time.time()
    A1.idt = receiveTime(source.x, source.y, A1.x, A1.y)
    A2.idt = receiveTime(source.x, source.y, A2.x, A2.y)
    A3.idt = receiveTime(source.x, source.y, A3.x, A3.y)
    A1.d = A1.idt*c
    A2.d = A2.idt*c
    A3.d = A3.idt*c
    A1.tl = 10*math.log(A1.d)
    A2.tl = 10*math.log(A2.d)
    A3.tl = 10*math.log(A3.d)

    first_index = receiverOrder(b.m1.idt, b.m2.idt) 

    if first_index == 1: #mic1 first receive
        m1_m2_ds = math.ceil(abs(b.m1.idt-b.m2.idt)*fs)
        b.m2.data = np.hstack((np.zeros(m1_m2_ds),source_data))
        b.m1.data = source_data
        b.m1.data = addNoise(b.m1.data)
        b.m2.data = addNoise(b.m2.data)
        b.m2.rt = corrXT(b.m2.data, b.m1.data)
        sourceToBoat(b.m1.rt, b.m2.rt)

    elif first_index == 2: #mic2 first receive
        m2_m1_ds = math.ceil(abs(b.m2.idt-b.m1.idt)*fs)
        b.m1.data = np.hstack((np.zeros(m2_m1_ds),source_data))
        b.m2.data = source_data
        b.m1.data = addNoise(b.m1.data)
        b.m2.data = addNoise(b.m2.data)
        b.m1.rt = corrXT(b.m1.data, b.m2.data)
        sourceToBoat(b.m1.rt, b.m2.rt)
    
    time_end = time.time()
    print("Time use = ", time_end-time_start)

#print(source.guessx, source.guessy)
