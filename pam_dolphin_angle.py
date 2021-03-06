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
leng = int(fs*1.5+1)

class pingerStatus:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.guessAngle = 0
        self.realAngle = 0
        self.sl = 0.0
        self.guessx = np.array([])
        self.guessy = np.array([])
        self.guessx1 = np.array([])
        self.guessy1 = np.array([])

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
        self.data = np.zeros(leng)

def receiveTime(x1, y1, x2, y2):
    t = (pow((x1-x2)**2+(y1-y2)**2, 0.5))
    t = t/c
    return t 

def receiverOrder(t1, t2, t3):
    index = np.argmin([t1, t2, t3])+1
    return index

def corrXT2(a_data, b_data, x1, y1, x2, y2):
    a = a_data.copy()
    b = b_data.copy()
    r = (pow((x1-x2)**2+(y1-y2)**2, 0.5))
    d = math.ceil(r/c*fs)+10
    tmp = np.zeros(d)
    for i in range(d):
        tmp[i] = np.sum(a[i:]*b[:(len(b)-i)])
    maxArgu = np.argmax(tmp)
    #real_recevie_t = (maxArgu)/fs
    real_recevie_t = round((maxArgu)/fs, 10)
    return real_recevie_t
'''
def sourceToBoat(t1, t2):
    dt = t1-t2
    print("dt = ", dt)
    l = 2*boat_mic
    theta = 90-math.acos(c*dt/l)*180/np.pi
    print("cal angle = ", theta)
    print("realAngle = ", angle([source.x, source.y]))
'''

def angle(pos):
    x, y = pos
    a = math.degrees(math.atan2(y, x))
    a = -a+90
    if a < 0:
        a = a+360
    return round(a, 1)

def addNoise(data, noise, d, t):
    tmp_data = data.copy()
    tmp_noise = np.hstack((noise.copy(), np.zeros(int(0.5*fs))))
    #tmp_noise = noise.copy()
    tmp_data = tmp_data/d**0.5
    tmp_noise[t:len(tmp_data)+t] += tmp_data
    return tmp_noise 

def sourceLevel(d):
    data = d.copy()
    gain = 10**((source.sl+sen)/20)
    data = data*gain
    return data
    
def tdoa(x1, y1, t1, x2, y2, t2, x3, y3, t3):
    x, y = symbols('x, y')
    eq1 = ((x-x1)**2.0+(y-y1)**2.0)**0.5-((x-x3)**2.0+(y-y3)**2.0)**0.5-c*(t1-t3)
    eq2 = ((x-x1)**2.0+(y-y1)**2.0)**0.5-((x-x2)**2.0+(y-y2)**2.0)**0.5-c*(t1-t2)
    eq3 = ((x-x2)**2.0+(y-y2)**2.0)**0.5-((x-x3)**2.0+(y-y3)**2.0)**0.5-c*(t2-t3)
    pos = solve([eq1, eq2, eq3], [x, y])
    if pos:
        print("roots = ", pos)
        if pos[0][0].is_Float:
            if len(pos) > 1:
                droot = 1
                source.guessx = np.append(source.guessx, pos[0][0])
                source.guessy = np.append(source.guessy, pos[0][1])
                source.guessx1 = np.append(source.guessx1, pos[1][0])
                source.guessy1 = np.append(source.guessy1, pos[1][1])
                source.px1 = pos[0][0]
                source.py1 = pos[0][1]
                source.px2 = pos[1][0]
                source.py2 = pos[1][1]
            else:
                droot = 0
                source.guessx = np.append(source.guessx, pos[0][0])
                source.guessy = np.append(source.guessy, pos[0][1])
                source.px1 = pos[0][0]
                source.py1 = pos[0][1]
            #ang = angle(pos[0])
            #source.guessAngle = ang
        else:
            droot = 3
            print("root is complex")
    else:
        droot = 3
        print("root is empty")
    return droot

def printData(droot):
    if droot == 0:
        print("guess position 1 = ", source.px1, ", ", source.py1)
    elif droot == 1:
        print("guess position 1 = ", source.px1, ", ", source.py1)
        print("guess position 2 = ", source.px2, ", ", source.py2)
    elif droot == 3:
        print("There is no real root.")
    print("real position = ", source.x, ", ", source.y)
    #print("guess angle = ", source.guessAngle)
    #print("real angle = ", angle([source.x, source.y]))
    print("----------------------------------------------------")
    
def dataVisual(droot):
    plt.plot([A1.x, A2.x, A3.x], [A1.y, A2.y, A3.y], 'r*', label='Hydrophone')
    plt.plot(s_x, s_y, 'bv', label='Source')
    plt.plot(source.guessx, source.guessy, 'go', label='Guess position')
    plt.plot(source.guessx1, source.guessy1, 'go')
    msg = str(source.sl)+'dB_5k_9k Chrip x='+str(source.x)+'m_'+str(i)
    plt.title(msg)
    plt.xlabel('X (m)')
    plt.ylabel('Y (m)')
    plt.legend(loc=2, borderaxespad=0.)
    plt.xlim((-700, 700))
    plt.ylim((-1500, 1500))
    msg = msg+'.png'
    plt.savefig(msg)
    #plt.show()
    plt.clf()

source = pingerStatus(400, 1400)
A2 = micPosition(550, 0)
A1 = micPosition(0, 500)
A3 = micPosition(-550, 0)
A1.fs, A1.noise = wavfile.read('./A1_noise.wav')
A2.fs, A2.noise = wavfile.read('./A2_noise.wav')
A3.fs, A3.noise = wavfile.read('./A3_noise.wav')
A1.noise = A1.noise/2**(bits-1)
A2.noise = A2.noise/2**(bits-1)
A3.noise = A3.noise/2**(bits-1)
source.sl = float(input('Source Level = '))
#source.sl = 150
source.data = sourceLevel(source_data)
s_x = np.array([])
s_y = np.array([])
i = 1
while(1):

    A1.data = np.zeros(leng)
    A2.data = np.zeros(leng)
    A3.data = np.zeros(leng)
    time_start = time.time()

    source.y = source.y-100
    s_x = np.append(s_x, source.x)
    s_y = np.append(s_y, source.y)

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
    print("index = ", first_index)

    if first_index == 1: #mic1 first receive
        A1.ds = 0
        A2.ds = math.ceil(abs(A1.idt-A2.idt)*fs)
        A3.ds = math.ceil(abs(A1.idt-A3.idt)*fs)
        A1.data = addNoise(source.data, A1.noise, A1.d, A1.ds)
        A2.data = addNoise(source.data, A2.noise, A2.d, A2.ds)
        A3.data = addNoise(source.data, A3.noise, A3.d, A3.ds)
        A1.rt = 0
        A2.rt = corrXT2(A2.data, A1.data, A2.x, A2.y, A1.x, A1.y)
        A3.rt = corrXT2(A3.data, A1.data, A3.x, A3.y, A1.x, A1.y)
        print(A2.rt, A3.rt)
        droot = tdoa(A1.x, A1.y, A1.rt, A2.x, A2.y, A2.rt, A3.x, A3.y, A3.rt)
    elif first_index == 2: #mic2 first receive
        A2.ds = 0
        A1.ds = math.ceil(abs(A2.idt-A1.idt)*fs)
        A3.ds = math.ceil(abs(A2.idt-A3.idt)*fs)
        A1.data = addNoise(source.data, A1.noise, A1.d, A1.ds)
        A2.data = addNoise(source.data, A2.noise, A2.d, A2.ds)
        A3.data = addNoise(source.data, A3.noise, A3.d, A3.ds)
        A2.rt = 0
        A1.rt = corrXT2(A1.data, A2.data, A1.x, A1.y, A2.x, A2.y)
        A3.rt = corrXT2(A3.data, A2.data, A3.x, A3.y, A2.x, A2.y)
        droot = tdoa(A1.x, A1.y, A1.rt, A2.x, A2.y, A2.rt, A3.x, A3.y, A3.rt)
    elif first_index == 3: #mic3 first receive
        A3.ds = 0
        A1.ds = math.ceil(abs(A3.idt-A1.idt)*fs)
        A2.ds = math.ceil(abs(A3.idt-A2.idt)*fs)
        A1.data = addNoise(source.data, A1.noise, A1.d, A1.ds)
        A2.data = addNoise(source.data, A2.noise, A2.d, A2.ds)
        A3.data = addNoise(source.data, A3.noise, A3.d, A3.ds)
        A3.rt = 0
        A1.rt = corrXT2(A1.data, A3.data, A1.x, A1.y, A3.x, A3.y)
        A2.rt = corrXT2(A2.data, A3.data, A2.x, A2.y, A3.x, A3.y)
        droot = tdoa(A1.x, A1.y, A1.rt, A2.x, A2.y, A2.rt, A3.x, A3.y, A3.rt)

    time_end = time.time()
    print("Time use = ", time_end-time_start)
    printData(droot)
    dataVisual(droot)
    if source.y <= -1300:
        break

    i = i+1
    '''    
    plt.figure(1)
    plt.subplot(411)
    plt.plot(source.data)
    plt.subplot(412)
    plt.plot(A1.data)
    plt.subplot(413)
    plt.plot(A2.data)
    plt.subplot(414)
    plt.plot(A3.data)
    '''
    '''
    plt.figure(2)
    plt.subplot(411)
    f, t, Sxx = signal.spectrogram(source.data, fs)
    plt.pcolormesh(t, f, Sxx)
    plt.subplot(412)
    f, t, Sxx = signal.spectrogram(A1.data, fs)
    plt.pcolormesh(t, f, Sxx)
   # plt.colorbar()
    plt.subplot(413)
    f, t, Sxx = signal.spectrogram(A2.data, fs)
    plt.pcolormesh(t, f, Sxx)
    plt.subplot(414)
    f, t, Sxx = signal.spectrogram(A3.data, fs)
    plt.pcolormesh(t, f, Sxx)
    plt.show()
    '''    
