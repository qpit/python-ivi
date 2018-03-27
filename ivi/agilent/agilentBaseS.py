"""

Python Interchangeable Virtual Instrument Library

Copyright (c) 2012-2014 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from .agilentBaseInfiniium import *
import struct

AcquisitionModeMapping = {
        'etim': ('normal', 'equivalent_time'),
        'rtim': ('normal', 'real_time'),
        'pdet': ('peak_detect', 'real_time'),
        'hres': ('high_resolution', 'real_time'),
        'segm': ('normal', 'segmented'),
        'segp': ('peak_detect', 'segmented'),
        'segh': ('high_resolution', 'segmented')
}
AcquisitionType = set(['normal', 'peak_detect', 'high_resolution'])
VerticalCoupling = set(['ac', 'dc'])
TriggerTypeMapping['width'] = 'pwidth'
ScreenshotImageFormatMapping = {
        'tif': 'tif',
        'tiff': 'tif',
        'bmp': 'bmp',
        'bmp24': 'bmp',
        'png': 'png',
        'png24': 'png',
        'jpg': 'jpg',
        'jpeg': 'jpg',
        'gif': 'gif'}
SampleMode = set(['real_time', 'equivalent_time', 'segmented'])
MeasurementFunctionMapping = {
        'rise_time': 'risetime',
        'fall_time': 'falltime',
        'frequency': 'frequency',
        'period': 'period',
        'voltage_rms': 'vrms display,ac',
        'voltage_peak_to_peak': 'vpp',
        'voltage_max': 'vmax',
        'voltage_min': 'vmin',
        'voltage_high': 'vtop',
        'voltage_low': 'vbase',
        'voltage_average': 'vaverage display',
        'width_negative': 'nwidth',
        'width_positive': 'pwidth',
        'duty_cycle_positive': 'dutycycle',
        'amplitude': 'vamplitude',
        'voltage_cycle_rms': 'vrms cycle,ac',
        'voltage_cycle_average': 'vaverage cycle',
        'overshoot': 'overshoot',
        'preshoot': 'preshoot',
        'ratio': 'vratio',
        'phase': 'phase',
        'delay': 'delay'}

class agilentBaseS(agilentBaseInfiniium):
    "Agilent Infiniium S series IVI oscilloscope driver"

    def __init__(self, *args, **kwargs):
        self.__dict__.setdefault('_instrument_id', '')
        self._analog_channel_name = list()
        self._analog_channel_count = 4
        self._digital_channel_name = list()
        self._digital_channel_count = 16
        self._channel_count = self._analog_channel_count + self._digital_channel_count
        self._channel_common_mode = list()
        self._channel_differential = list()
        self._channel_differential_skew = list()
        self._channel_display_auto = list()
        self._channel_display_offset = list()
        self._channel_display_range = list()
        self._channel_display_scale = list()

        super(agilentBaseS, self).__init__(*args, **kwargs)

        self._analog_channel_name = list()
        self._analog_channel_count = 4
        self._digital_channel_name = list()
        self._digital_channel_count = 16
        self._channel_count = self._analog_channel_count + self._digital_channel_count
        self._bandwidth = 0.5e9

        self._horizontal_divisions = 10
        self._vertical_divisions = 8

        self._display_color_grade = False

        self._identity_description = "KeySight Infiniium S series IVI oscilloscope driver"
        self._identity_supported_instrument_models = ['DSOS054A','DSOS104A','DSOS204A','DSOS254A','DSOS404A','DSOS604A',
        'DSOS804A','MSOS054A','MSOS104A','MSOS204A','MSOS254A','MSOS404A','MSOS604A','MSOS804A']

        self._add_property('channels[].common_mode',
                        self._get_channel_common_mode,
                        self._set_channel_common_mode,
                        None,
                        ivi.Doc("""
                        Turns on/off common mode for the channel.  Channels 2 and 4 may form a
                        common mode channel and channels 1 and 3 may form a common mode channel.
                        """))
        self._add_property('channels[].differential',
                        self._get_channel_differential,
                        self._set_channel_differential,
                        None,
                        ivi.Doc("""
                        Turns on/off differential mode for the channel.  Channels 2 and 4 may form
                        a differential channel and channels 1 and 3 may form a differential
                        channel.
                        """))
        self._add_property('channels[].differential_skew',
                        self._get_channel_differential_skew,
                        self._set_channel_differential_skew,
                        None,
                        ivi.Doc("""
                        Specifies the skew that is applied to the differential or common mode pair
                        of channels.  Units are seconds.
                        """))
        self._add_property('channels[].display_auto',
                        self._get_channel_display_auto,
                        self._set_channel_display_auto,
                        None,
                        ivi.Doc("""
                        Sets the differential and common mode display scale and offset to track
                        the acquisition scale and offset.
                        """))
        self._add_property('channels[].display_offset',
                        self._get_channel_display_offset,
                        self._set_channel_display_offset,
                        None,
                        ivi.Doc("""
                        Sets the displayed offset of the selected channel.  Setting this parameter
                        disables display_auto.  Units are volts.
                        """))
        self._add_property('channels[].display_range',
                        self._get_channel_display_range,
                        self._set_channel_display_range,
                        None,
                        ivi.Doc("""
                        Sets the full scale vertical range of the selected channel.  Setting this
                        parameter disables display_auto.  Units are volts.
                        """))
        self._add_property('channels[].display_scale',
                        self._get_channel_display_scale,
                        self._set_channel_display_scale,
                        None,
                        ivi.Doc("""
                        Sets the displayed scale of the selected channel per division.  Setting
                        this parameter disables display_auto.  Units are volts.
                        """))

        self._init_channels()


    def _utility_error_query(self):
        error_code = 0
        error_message = "No error"
        if not self._driver_operation_simulate:
            error_code = self._ask(":system:error?")
            error_code = int(error_code)
            if error_code != 0:
                error_message = "Unknown"
        return (error_code, error_message)

    def _init_channels(self):
        try:
            super(agilentBaseS, self)._init_channels()
        except AttributeError:
            pass

        self._channel_common_mode = list()
        self._channel_differential = list()
        self._channel_differential_skew = list()
        self._channel_display_auto = list()
        self._channel_display_offset = list()
        self._channel_display_range = list()
        self._channel_display_scale = list()

        for i in range(self._analog_channel_count):
            self._channel_common_mode.append(False)
            self._channel_differential.append(False)
            self._channel_differential_skew.append(0)
            self._channel_display_auto.append(True)
            self._channel_display_offset.append(0.0)
            self._channel_display_range.append(1.0)
            self._channel_display_scale.append(0.1)


    def _display_fetch_screenshot(self, format='png', invert=False):
        if self._driver_operation_simulate:
            return b''

        if format not in ScreenshotImageFormatMapping:
            raise ivi.ValueNotSupportedException()

        format = ScreenshotImageFormatMapping[format]

        self._write(":display:data? %s, screen, on, %s" % (format, 'invert' if invert else 'normal'))

        return self._read_ieee_block()

    def _get_channel_input_impedance(self, index):
        index = ivi.get_index(self._analog_channel_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            s = self._ask(":%s:input?" % self._channel_name[index]).lower()
            if s in ['dc50', 'dcfifty']:
                self._channel_input_impedance[index] = 50
            else:
                self._channel_input_impedance[index] = 1000000
            self._set_cache_valid(index=index)
        return self._channel_input_impedance[index]

    def _set_channel_input_impedance(self, index, value):
        index = ivi.get_index(self._analog_channel_name, index)
        if value not in [50, 1000000]:
            raise ivi.ValueNotSupportedException()
        # obtain coupling
        coupling = self._get_channel_coupling(index)
        if value == 50 and coupling == 'ac':
            raise ivi.ValueNotSupportedException('AC coupling not supported for 50 Ohm input impedance.')
        if not self._driver_operation_simulate:
            if coupling == 'dc':
                if value == 50:
                    transmitted_value = 'dc50'
                else:
                    transmitted_value = 'dc'
            else:
                transmitted_value = 'ac'
            self._write(":%s:input %s" % (self._channel_name[index], transmitted_value))
        self._channel_input_impedance[index] = value
        self._set_cache_valid(index=index)

    def _get_channel_coupling(self, index):
        index = ivi.get_index(self._analog_channel_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            s = self._ask(":%s:input?" % self._channel_name[index]).lower()
            if s in ['dc', 'dc50', 'dcfifty']:
                self._channel_coupling[index] = 'dc'
            else:
                self._channel_coupling[index] = 'ac'
            self._set_cache_valid(index=index)
        return self._channel_coupling[index]

    def _set_channel_coupling(self, index, value):
        index = ivi.get_index(self._analog_channel_name, index)
        if value not in VerticalCoupling:
            raise ivi.ValueNotSupportedException()
        # obtain impedance
        impedance = self._get_channel_input_impedance(index)
        if impedance == 50 and value == 'ac':
            raise ivi.ValueNotSupportedException('AC coupling not supported for 50 Ohm input impedance.')
        if not self._driver_operation_simulate:
            if value == 'dc':
                if impedance == 50:
                    transmitted_value = 'dc50'
                else:
                    transmitted_value = 'dc'
            else:
                transmitted_value = 'ac'
            self._write(":%s:input %s" % (self._channel_name[index], transmitted_value))
        self._channel_coupling[index] = value
        self._set_cache_valid(index=index)

    def _get_channel_common_mode(self, index):
        index = ivi.get_index(self._analog_channel_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            self._channel_common_mode[index] = bool(int(self._ask(":%s:commonmode?" % self._channel_name[index])))
            self._set_cache_valid(index=index)
        return self._channel_common_mode[index]

    def _set_channel_common_mode(self, index, value):
        index = ivi.get_index(self._analog_channel_name, index)
        value = bool(value)
        if not self._driver_operation_simulate:
            self._write(":%s:commonmode %d" % (self._channel_name[index], int(value)))
        self._channel_common_mode[index] = value
        self._set_cache_valid(index=index)

    def _get_channel_differential(self, index):
        index = ivi.get_index(self._analog_channel_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            self._channel_differential[index] = bool(int(self._ask(":%s:differential?" % self._channel_name[index])))
            self._set_cache_valid(index=index)
        return self._channel_differential[index]

    def _set_channel_differential(self, index, value):
        index = ivi.get_index(self._analog_channel_name, index)
        value = bool(value)
        if not self._driver_operation_simulate:
            self._write(":%s:differential %d" % (self._channel_name[index], int(value)))
        self._channel_differential[index] = value
        self._set_cache_valid(index=index)

    def _get_channel_differential_skew(self, index):
        index = ivi.get_index(self._analog_channel_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            self._channel_differential_skew[index] = float(self._ask(":%s:differential:skew?" % self._channel_name[index]))
            self._set_cache_valid(index=index)
        return self._channel_differential_skew[index]

    def _set_channel_differential_skew(self, index, value):
        index = ivi.get_index(self._analog_channel_name, index)
        value = float(value)
        if not self._driver_operation_simulate:
            self._write(":%s:differential:skew %e" % (self._channel_name[index], value))
        self._channel_differential_skew[index] = value
        self._set_cache_valid(index=index)

    def _get_channel_display_auto(self, index):
        index = ivi.get_index(self._analog_channel_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            self._channel_display_auto[index] = bool(int(self._ask(":%s:display:auto?" % self._channel_name[index])))
            self._set_cache_valid(index=index)
        return self._channel_display_auto[index]

    def _set_channel_display_auto(self, index, value):
        index = ivi.get_index(self._analog_channel_name, index)
        value = bool(value)
        if not self._driver_operation_simulate:
            self._write(":%s:display:auto %d" % (self._channel_name[index], int(value)))
        self._channel_display_auto[index] = value
        self._set_cache_valid(index=index)

    def _get_channel_display_offset(self, index):
        index = ivi.get_index(self._analog_channel_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            self._channel_display_offset[index] = float(self._ask(":%s:display:offset?" % self._channel_name[index]))
            self._set_cache_valid(index=index)
        return self._channel_display_offset[index]

    def _set_channel_display_offset(self, index, value):
        index = ivi.get_index(self._analog_channel_name, index)
        value = float(value)
        if not self._driver_operation_simulate:
            self._write(":%s:display:offset %e" % (self._channel_name[index], value))
        self._channel_display_offset[index] = value
        self._set_cache_valid(index=index)

    def _get_channel_display_range(self, index):
        index = ivi.get_index(self._analog_channel_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            self._channel_display_range[index] = float(self._ask(":%s:display:range?" % self._channel_name[index]))
            self._set_cache_valid(index=index)
        return self._channel_display_range[index]

    def _set_channel_display_range(self, index, value):
        index = ivi.get_index(self._analog_channel_name, index)
        value = float(value)
        if not self._driver_operation_simulate:
            self._write(":%s:display:range %e" % (self._channel_name[index], value))
        self._channel_display_range[index] = value
        self._set_cache_valid(index=index)

    def _get_channel_display_scale(self, index):
        index = ivi.get_index(self._analog_channel_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            self._channel_display_scale[index] = float(self._ask(":%s:display:scale?" % self._channel_name[index]))
            self._set_cache_valid(index=index)
        return self._channel_display_scale[index]

    def _set_channel_display_scale(self, index, value):
        index = ivi.get_index(self._analog_channel_name, index)
        value = float(value)
        if not self._driver_operation_simulate:
            self._write(":%s:display:scale %e" % (self._channel_name[index], value))
        self._channel_display_scale[index] = value
        self._set_cache_valid(index=index)

    def _get_trigger_level(self):
        if not self._driver_operation_simulate and not self._get_cache_valid():
            # find channel source
            source = self.trigger.source
            self._trigger_level = float(self._ask(":trigger:level? %s" % source))
            self._set_cache_valid()
        return self._trigger_level

    def _set_trigger_level(self, value):
        value = float(value)
        if not self._driver_operation_simulate:
            # find channel source
            source = self._trigger_source
            self._write(":trigger:level %s,%e" % (source, value))
        self._trigger_level = value
        self._set_cache_valid()
        for i in range(self._analog_channel_count): self._set_cache_valid(False, 'channel_trigger_level', i)

    def _get_trigger_type(self):
        # FIXME: glitch trigger only triggers to smaller than width values in the s-series oscilloscopes
        if not self._driver_operation_simulate and not self._get_cache_valid():
            value = self._ask(":trigger:mode?").lower()
            if value == 'edge':
                src = self._ask(":trigger:edge:source?").lower()
                if src == 'line':
                    value = 'ac_line'
            else:
                value = [k for k,v in TriggerTypeMapping.items() if v==value][0]
            self._trigger_type = value
            self._set_cache_valid()
        return self._trigger_type

    def _set_trigger_type(self, value):
        if value not in TriggerTypeMapping:
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            self._write(":trigger:mode %s" % TriggerTypeMapping[value])
            if value == 'ac_line':
                self._write(":trigger:edge:source line")
        self._trigger_type = value
        self._set_cache_valid()

    def _get_trigger_source(self):
        if not self._driver_operation_simulate and not self._get_cache_valid():
            type = self._get_trigger_type()
            value = self._ask(":trigger:%s:source?" % TriggerTypeMapping[type]).lower()
            if value.startswith('chan'):
                value = 'channel' + value[4:]
            self._trigger_source = value
            self._set_cache_valid()
        return self._trigger_source

    def _set_trigger_source(self, value):
        # FIXME: what about the external trigger source?
        if hasattr(value, 'name'):
            value = value.name
        value = str(value)
        if value not in self._channel_name:
            raise ivi.UnknownPhysicalNameException()
        if not self._driver_operation_simulate:
            type = self._get_trigger_type()
            self._write(":trigger:%s:source %s" % (TriggerTypeMapping[type], value))
        self._trigger_source = value
        self._set_cache_valid()

    def _measurement_fetch_waveform(self, index):
        index = ivi.get_index(self._channel_name, index)

        if self._driver_operation_simulate:
            return list()

        if sys.byteorder == 'little':
            self._write(":waveform:byteorder lsbfirst")
        else:
            self._write(":waveform:byteorder msbfirst")
        self._write(":waveform:format word")
        self._write(":waveform:streaming on")
        self._write(":waveform:source %s" % self._channel_name[index])

        trace = ivi.TraceYT()

        # Read preamble

        pre = self._ask(":waveform:preamble?").split(',')

        acq_format = int(pre[0])
        acq_type = int(pre[1])
        points = int(pre[2])
        trace.average_count = int(pre[3])
        trace.x_increment = float(pre[4])
        trace.x_origin = float(pre[5])
        trace.x_reference = int(float(pre[6]))
        trace.y_increment = float(pre[7])
        trace.y_origin = float(pre[8])
        trace.y_reference = int(float(pre[9]))
        trace.y_hole = None

        if acq_type == 1:
            raise scope.InvalidAcquisitionTypeException()

        if acq_format != 2:
            raise ivi.UnexpectedResponseException()

        self._write(":waveform:data?")

        # Read waveform data
        raw_data = self._read_ieee_block()

        # Store in trace object
        trace.y_raw = array.array('h', raw_data[0:points * 2])

        return trace

    def _measurement_read_waveform(self, index, maximum_time):
        return self._measurement_fetch_waveform(index)

    def _measurement_initiate(self):
        if not self._driver_operation_simulate:
            self._write(":acquire:complete 100")
            self._write(":digitize")
            self._set_cache_valid(False, 'trigger_continuous')

    def _get_reference_levels(self):
        if not self._driver_operation_simulate and not self._get_cache_valid():
            high, middle, low = self._ask(":measure:thresholds:percent? %s" % self.channels[0].name).split(',')
            self._reference_level_high = float(high)
            self._reference_level_low = float(low)
            self._reference_level_middle = float(middle)
            self._set_cache_valid()
            self._set_cache_valid('reference_level_high')
            self._set_cache_valid('reference_level_low')
            self._set_cache_valid('reference_level_middle')

    def _set_reference_level_high(self, value):
        value = float(value)
        if value < 5: value = 5
        if value > 95: value = 95
        if not self._driver_operation_simulate and not self._get_cache_valid():
            self._get_reference_levels()
        self._reference_level_high = value
        if not self._driver_operation_simulate:
            for ii in range(len(self.channels)):
                self._write(":measure:thresholds percent, %s, %e, %e, %e" %
                            (self.channels[ii].name,
                             self._reference_level_high,
                             self._reference_level_middle,
                             self._reference_level_low))

    def _measurement_fetch_waveform_measurement(self, index, measurement_function, ref_channel = None):
        "just a copy from agilentBaseScope so that the local MeasurementFunctionMapping is used"
        index = ivi.get_index(self._channel_name, index)
        if index < self._analog_channel_count:
            if measurement_function not in MeasurementFunctionMapping:
                raise ivi.ValueNotSupportedException()
            func = MeasurementFunctionMapping[measurement_function]
        else:
            if measurement_function not in MeasurementFunctionMappingDigital:
                raise ivi.ValueNotSupportedException()
            func = MeasurementFunctionMappingDigital[measurement_function]
        if not self._driver_operation_simulate:
            l = func.split(' ')
            l[0] = l[0] + '?'
            if len(l) > 1:
                l[-1] = l[-1] + ','
            func = ' '.join(l)
            query = ":measure:%s %s" % (func, self._channel_name[index])
            if measurement_function in ['ratio', 'phase', 'delay']:
                if hasattr(ref_channel, 'name'):
                    ref_channel = ref_channel.name
                ref_index = ivi.get_index(self._channel_name, ref_channel)
                query += ", %s" % self._channel_name[ref_index]
            return float(self._ask(query))
        return 0

    def _set_working_directory(self,value):
        if not self._driver_operation_simulate:
            self._write(":DISK:CDIRECTORY %s" % '\"'+value+'\"')

    def _get_pwd(self):
        if not self._driver_operation_simulate:
             return self._ask(":DISK:PWD?")

    def _save_waveform(self,filename,source,filtype='BIN',header="ON"):
        if not self._driver_operation_simulate:
            self._write(":DISK:SAVE:WAVEFORM %s" % 'CHANnel'+str(source)+',\"'+filename+'\",'+filtype+','+header)

    def _set_save_waveform_all(self):
        if not self._driver_operation_simulate:
            self._write(":DISK:SEGMented ALL")

