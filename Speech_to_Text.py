import pyaudio
import wave
import sphinxbase
import os
import pocketsphinx
import audioop
import math
from pocketsphinx import Pocketsphinx
try:
    from pocketsphinx.pocketsphinx import *
except ValueError:
    import pocketsphinx

# These will need to be modified according to where the pocketsphinx folder is
MODELDIR = os.path.dirname(os.path.realpath(__file__))

# Create a decoder with certain model

config = Decoder.default_config()
config.set_string('-hmm', os.path.join(MODELDIR, 'hmm'))
config.set_string('-lm', os.path.join(MODELDIR, 'lm/cmusphinx-5.0-en-us.lm.dmp'))
config.set_string('-dict', os.path.join(MODELDIR, 'dict/cmu07a.dic'))

# Creaders decoder object for streaming data.
decoder = Decoder(config)

CHUNK = 1024
FORMAT = pyaudio.paInt16 #paInt8
CHANNELS = 1 
RATE = 16000 #sample rate
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"
SILENCE_LIMIT = 1  # Silence limit in seconds. The max ammount of seconds where
                           # only silence is recorded. When this time passes the
                           # recording finishes and the file is decoded
PREV_AUDIO = 0.5  # Previous audio (in seconds) to prepend. When noise
                          # is detected, how much of previously recorded audio is
                          # prepended. This helps to prevent chopping the beginning
                          # of the phrase.
THRESHOLD = 4500

# Listens to Microphone, Stream audio from an input device and save it

def save_audio(wav_file):
    """
    Stream audio from an input device and save it.
    """

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK) #buffer

print "* Mic set up and listening. "

frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data) # 2 bytes(16 bits) per channel

print("* done recording")

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

# Microphone set up:

def setup_mic(num_samples):
        """ Gets average audio intensity of your mic sound. You can use it to get
            average intensities while you're talking and/or silent. The average
            is the avg of the .2 of the largest intensities recorded.
        """
        print "Getting intensity values from mic."
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, 
                        channels=CHANNELS,
                        rate=RATE, 
                        input=True, 
                        frames_per_buffer=CHUNK)

        values = [math.sqrt(abs(audioop.avg(stream.read(CHUNK), 4)))
                  for x in range(num_samples)]
        values = sorted(values, reverse=True)
        r = sum(values[:int(num_samples * 0.2)]) / int(num_samples * 0.2)
        print " Finished "
        print " Average audio intensity is ", r
        stream.close()
        p.terminate()

        if r < 3000:
            THRESHOLD = 3500
        else:
            THRESHOLD = r + 100

# Extract phrases from audio file and calls pocketsphinx to decode the sound

def decode_phrase(WAVE_OUTPUT_FILENAME):
        decoder.start_utt()
        stream = open(WAVE_OUTPUT_FILENAME, "rb")
        while True:
          buf = stream.read(1024)
          if buf:
            decoder.process_raw(buf, False, False)
          else:
            break
        decoder.end_utt()
        words = []
        [words.append(seg.word) for seg in decoder.seg()]
        return words

# Run the thing!
if __name__ == '__main__':
    setup_mic(5)
    save_audio(WAVE_OUTPUT_FILENAME)
    r = decode_phrase(WAVE_OUTPUT_FILENAME)
    print "DETECTED: ", r
