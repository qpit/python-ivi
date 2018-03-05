import time
import numpy
import matplotlib.pyplot as plt
import ivi.tektronix.tektronixAWG5000 as awg5000
import ivi.agilent.agilentDSOS204A as dsos204a

fs_awg = 500e6
fs_dso = 1e9
number_of_points_minimum = 1e6
time_per_record_DSO = 50e-6

awg = awg5000.tektronixAWG5000('TCPIP::10.54.4.47::INSTR')
scope = dsos204a.agilentDSOS204A('TCPIP0::WINDOWS-6TBN82B.local::hislip0::INSTR')


# setup awg
t = numpy.arange(0,1e-3,1/fs_awg)
data = numpy.sin(2*numpy.pi*1e6*t)
marker = numpy.ones(len(t))
marker[:100000] = 0
marker[-100000:] = 0
data = numpy.column_stack((data, marker)) # using marker1 only

awg.arbitrary.sample_rate = fs_awg
awg.outputs[1].enabled = False
print('create waveform')
wfm_handle = awg.arbitrary.waveform.create(data)
awg.outputs[0].arbitrary.waveform.handle = wfm_handle
awg.outputs[0].arbitrary.offset = 0.5
awg.outputs[0].arbitrary.gain = 0.5
awg.outputs[0].enabled = True

# setup oscilloscope
scope.acquisition.type = 'normal'
scope.acquisition.input_frequency_max = 500e6
scope.acquisition.number_of_points_minimum = number_of_points_minimum
scope.acquisition.time_per_record = time_per_record_DSO
print('Sample rate: {0} GHz'.format(scope.acquisition.sample_rate/1e9))

scope.channels[0].input_impedance = 1e6
scope.channels[0].coupling = 'dc'
scope.channels[0].offset = 0
scope.channels[0].range = 10
scope.channels[0].enabled = True

scope.channels[1].enabled = False

scope.channels[2].input_impedance = 1e6
scope.channels[2].coupling = 'dc'
scope.channels[2].offset = 0
scope.channels[2].range = 4
scope.channels[2].enabled = True

scope.channels[3].enabled = False


# start awg
awg.initiate_generation()

time.sleep(0.5)

# start scope acquisition
scope.measurement.initiate()
# wait until scope is ready
while scope.measurement.status == 'in_progress':
    time.sleep(0.1)
measured_data = scope.channels[0].measurement.fetch_waveform()
measured_marker = scope.channels[2].measurement.fetch_waveform()

# stop awg
awg.abort_generation()
awg.arbitrary.waveform.clear(wfm_handle)

# plot measured results
plt.plot(measured_data.t, measured_data.y)
plt.plot(measured_marker.t, measured_marker.y)
plt.show()