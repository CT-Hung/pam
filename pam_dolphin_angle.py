import numpy as np 
import math
from scipy.io import wavfile 
from scipy import signal
from sympy import *
import time
import matplotlib.pyplot as plt

c = 1500.0 #sound speed m/s 
sen = -165 #sensitivy dB
fs, data = wavfile.read('./24k_fs_5k_to_9k.wav') #source wav file 
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
        self.rt = 0.0 #real receive time
        self.tl = 0.0 #transmission lose
        self.rl = 0.0 #receive level
        self.ds = 0.0

def receiveTime(x1, y1, x2, y2):
    t = (pow((x1-x2)**2+(y1-y2)**2, 0.5))
    t = t/c
    return t 

def receiverOrder(t1, t2, t3):
    index = np.argmin([t1, t2, t3])+1
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
    a = math.degrees(math.atan2(y, x))
    a = -a+90
    if a < 0:
        a = a+360
    return round(a, 1)

def addNoise(data, noise, d, t):
    data = data/d**0.5
    print(t)
    noise[t:len(data)+t] += data
    return noise 

def sourceLevel(data):
    gain = 10**((source.sl+sen)/20)
    data = data*gain
    return data
    
def tdoa(x1, y1, t1, x2, y2, t2, x3, y3, t3):
    x, y = symbols('x, y')#, complex=False)
    eq1 = ((x-x1)**2.0+(y-y1)**2.0)**0.5-((x-x3)**2.0+(y-y3)**2.0)**0.5-c*(t1-t3)
    eq2 = ((x-x1)**2.0+(y-y1)**2.0)**0.5-((x-x2)**2.0+(y-y2)**2.0)**0.5-c*(t1-t2)
    eq3 = ((x-x2)**2.0+(y-y2)**2.0)**0.5-((x-x3)**2.0+(y-y3)**2.0)**0.5-c*(t2-t3)
    pos = solve([eq1, eq2, eq3], [x, y])
    print(pos)
    if pos:
        if type(pos[0]) != complex: 
            ang = angle(pos[0])
            source.guessx = pos[0][0]
            source.guessy = pos[0][1]
            source.guessAngle = ang
        else:
            print("pos is complex")
    else:
        print("pos is empty")
    return 0

source = pingerStatus(100, 2000)
A2 = micPosition(550, 0)
A1 = micPosition(0, 500)
A3 = micPosition(-550, 0)
A1.fs, A1.noise = wavfile.read('./A1_noise.wav')
A2.fs, A2.noise = wavfile.read('./A2_noise.wav')
A3.fs, A3.noise = wavfile.read('./A3_noise.wav')
A1.noise = A1.noise/2**(bits-1)
A2.noise = A2.noise/2**(bits-1)
A3.noise = A3.noise/2**(bits-1)
print(len(A1.noise), len(A2.noise), len(A3.noise), len(source_data))

source.sl = float(input('Source Level = '))
source.data = sourceLevel(source_data)

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

    first_index = receiverOrder(A1.idt, A2.idt, A3.idt) 

    if first_index == 1: #mic1 first receive
        A1.ds = 0
        A2.ds = math.ceil(abs(A1.idt-A2.idt)*fs)
        A3.ds = math.ceil(abs(A1.idt-A3.idt)*fs)
        A1.data = addNoise(source.data, A1.noise, A1.d, A1.ds)
        A2.data = addNoise(source.data, A2.noise, A2.d, A2.ds)
        A3.data = addNoise(source.data, A3.noise, A3.d, A3.ds)
        A1.rt = 0
        A2.rt = corrXT(A2.data, A1.data)
        A3.rt = corrXT(A3.data, A1.data)
        tdoa(A1.x, A1.y, A1.rt, A2.x, A2.y, A2.rt, A3.x, A3.y, A3.rt)
    
    plt.figure(1)
    plt.subplot(411)
    plt.plot(source.data)
    plt.subplot(412)
    plt.plot(A1.data)
    plt.subplot(413)
    plt.plot(A2.data)
    plt.subplot(414)
    plt.plot(A3.data)

    plt.figure(2)
    plt.subplot(411)
    f, t, Sxx = signal.spectrogram(source.data, fs)
    plt.pcolormesh(t, f, Sxx)
    plt.subplot(412)
    f, t, Sxx = signal.spectrogram(A1.noise, fs)
    plt.pcolormesh(t, f, Sxx)
   # plt.colorbar()
    plt.subplot(413)
    f, t, Sxx = signal.spectrogram(A1.noise, fs)
    plt.pcolormesh(t, f, Sxx)
    plt.subplot(414)
    f, t, Sxx = signal.spectrogram(A1.noise, fs)
    plt.pcolormesh(t, f, Sxx)
    plt.show()
    print("guess position = ", source.guessx, ", ", source.guessy)
    print("real position = ", source.x, ", ", source.y)
    print("guess angle = ", source.guessAngle)
    print("real angle = ", angle([source.x, source.y]))
    time_end = time.time()
    print("Time use = ", time_end-time_start)
    break

#print(source.guessx, source.guessy)
