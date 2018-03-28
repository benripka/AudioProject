import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import pyaudio
import struct
from scipy.fftpack import fft
# not sure if this next library is the way to go to find harmonics
from scipy.signal import find_peaks_cwt
import time
import peakutils
import math



# Note that it'll take a bit of time to fire up!
#object used to stream HEX values corresponding to the audio signals
class AudioStream(object):
    def __init__(self):

        #chunk is the number of values per frame
        self.CHUNK = 1024 * 2
        #tells it what form to return the signal values (16 bit)
        self.FORMAT = pyaudio.paInt16
        #we only need one stream
        self.CHANNELS = 1
        #frame rate
        self.RATE = 44100
        #TODO: I don't actually have the pausing working yet. should implement some way to pause the graphs (maybe)
        self.pause = False
        self.root = None

        # stream object
        # Object used as a handle on the OS audio stream,
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=True,
            frames_per_buffer=self.CHUNK,
        )
        #get the plots going
        self.init_plots()
        self.start_plot()
        self.findNote()
        self.xf = None

    def init_plots(self):

        # The X values for the plot. xf are the frequencies. Numpy is efficient.
        x = np.arange(0, 2 * self.CHUNK, 2)
        self.xf = np.linspace(0, self.RATE, self.CHUNK)

        # create matplotlib figure and axes
        self.fig, (ax1, ax2) = plt.subplots(2, figsize=(15, 7))
        # a start on the whole pausing thing
        self.fig.canvas.mpl_connect('button_press_event', self.onClick)

        # create a line object with random data
        self.line, = ax1.plot(x, np.random.rand(self.CHUNK), '-', lw=2)

        # semilong to be used as the frequency axis
        self.line_fft, = ax2.semilogx(
            self.xf, np.random.rand(self.CHUNK), '-', lw=2)
        # format waveform axes
        ax1.set_title('Audio Waveform')
        ax1.set_xlabel('Samples')
        ax1.set_ylabel('Volume')
        ax1.set_ylim(0, 300)
        # arbitrary, but this amount seems to work pretty well
        ax1.set_xlim(0, 2 * self.CHUNK)
        plt.setp(
            ax1, yticks=[0, 128, 255],
            xticks=[0, self.CHUNK, 2 * self.CHUNK],
        )
        plt.setp(ax2, yticks=[0, 1],)

        # format freq axis
        ax2.set_xlim(20, self.RATE / 2)

        # show axes
        thismanager = plt.get_current_fig_manager()
        plt.show(block=False)


    def start_plot(self):

        print('stream started')
        frame_count = 0
        start_time = time.time()
        #TODO: Pause doesn't work atm.
        while not self.pause:
            data = self.stream.read(self.CHUNK, exception_on_overflow = False)
            data_int = struct.unpack(str(2 * self.CHUNK) + 'B', data)
            data_np = np.array(data_int, dtype='b')[::2] + 128
            self.line.set_ydata(data_np)

            # compute FFT and update line
            YF = fft(data_int)
            normYF = np.abs(YF[0:self.CHUNK]) / (128 * self.CHUNK)



            self.line_fft.set_ydata(
                normYF
                )
            # update figure canvas
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            frame_count += 1
            peaks = peakutils.indexes(normYF, thres=0.2, min_dist=0)
            points = list(zip(normYF, self.xf))
            if len(peaks) > 0:
                freq_peak = int(points[min(peaks)][1])
                self.findNote(freq_peak)
        else:
            self.fr = frame_count / (time.time() - start_time)
            print('average frame rate = {:.0f} FPS'.format(self.fr))
            self.exit_app()

    def findNote(self, freq):
        base_freq = 430
        n = (math.log(freq)-math.log(base_freq))/math.log(2 ** (1 / 12))
        below = False
        if n < 0:
            bellow = True
            n = math.fabs(n)
        while n >= 12:
            n -= 12
        notes = {
            0 : "A",
            1 : "A#",
            2 : "B",
            3 : "C",
            4 : "C#",
            5 : "D",
            6 : "D#",
            7 : "E",
            8 : "F",
            9 : "F#",
            10 : "G",
            11 : "G#"
        }
        note = notes.get(int(n), None)
        cents = n - int(n)
        print(note, " + ", round(cents, 2)*100, "¢")


    def exit_app(self):
        print('stream closed')
        self.p.close(self.stream)

    def onClick(self, event):
        self.pause = True


if __name__ == '__main__':
    while True:
        AudioStream()