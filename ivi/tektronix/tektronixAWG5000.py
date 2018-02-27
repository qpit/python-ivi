"""

Python Interchangeable Virtual Instrument Library

Copyright (c) 2018 Tobias Gehring

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

Tek Programming Manual: http://download.tek.com/manual/077006105web.pdf
"""

import time
import struct
from numpy import *

from .. import ivi
from .. import fgen


# mapping from AWG return values to IVI specification
SampleClockSourceMap = {'int': 'internal', 'ext': 'external'}
TriggerSlopeMap = {'pos': 'positive', 'neg': 'negative'}
TriggerSourceMap = {'int': 'internal', 'ext': 'external'}


class tektronixAWG5000(ivi.Driver, fgen.Base, fgen.ArbWfm,
                fgen.ArbSeq, fgen.StartTrigger, fgen.SoftwareTrigger, fgen.Burst,
                fgen.ArbChannelWfm):
    """Tektronix AWG5000 series arbitrary waveform generator driver"""
    
    def __init__(self, *args, **kwargs):
        self.__dict__.setdefault('_instrument_id', '')
        
        super(tektronixAWG5000, self).__init__(*args, **kwargs)
        
        self._output_count = 2
        
        self._arbitrary_sample_rate = 0
        self._arbitrary_waveform_number_waveforms_max = 16200
        self._arbitrary_waveform_size_max = 256*1024
        self._arbitrary_waveform_size_min = 64
        self._arbitrary_waveform_quantum = 8
        
        self._arbitrary_sequence_number_sequences_max = 0
        self._arbitrary_sequence_loop_count_max = 0
        self._arbitrary_sequence_length_max = 0
        self._arbitrary_sequence_length_min = 0
        
        self._wfm_catalog = list()
        
        self._arbitrary_waveform_n = 0
        self._arbitrary_sequence_n = 0
        
        self._identity_description = "Tektronix AWG5000 series arbitrary waveform generator driver"
        self._identity_identifier = ""
        self._identity_revision = ""
        self._identity_vendor = ""
        self._identity_instrument_manufacturer = "Tektronix"
        self._identity_instrument_model = ""
        self._identity_instrument_firmware_revision = ""
        self._identity_specification_major_version = 5
        self._identity_specification_minor_version = 0
        self._identity_supported_instrument_models = ['AWG5002a','AWG5002c'] # FIXME
        
        self._init_outputs()
    
    def _initialize(self, resource = None, id_query = False, reset = False, **keywargs):
        """Opens an I/O session to the instrument."""
        
        super(tektronixAWG5000, self)._initialize(resource, id_query, reset, **keywargs)
        
        # interface clear
        if not self._driver_operation_simulate:
            self._clear()
        
        # check ID
        if id_query and not self._driver_operation_simulate:
            id = self.identity.instrument_model
            id_check = self._instrument_id
            id_short = id[:len(id_check)]
            if id_short != id_check:
                raise Exception("Instrument ID mismatch, expecting %s, got %s", id_check, id_short)
        
        # reset
        if reset:
            self.utility_reset()

    def _ask(self, data, num=-1, encoding = 'utf-8'):
        try:
            result = super(tektronixAWG5000, self)._ask(data, num, encoding)
            return result
        except:
            self._check_last_error()

    def _write(self, data, encoding = 'utf-8'):
        try:
            super(tektronixAWG5000, self)._write(data, encoding)
        finally:
            self._check_last_error()

    def _write_ieee_block(self, data, prefix = None, encoding = 'utf-8'):
        try:
            super(tektronixAWG5000, self)._write_ieee_block(data, prefix, encoding)
        finally:
            self._check_last_error()

    def _load_id_string(self):
        if self._driver_operation_simulate:
            self._identity_instrument_manufacturer = "Not available while simulating"
            self._identity_instrument_model = "Not available while simulating"
            self._identity_instrument_firmware_revision = "Not available while simulating"
        else:
            lst = self._ask("*IDN?").split(",")
            self._identity_instrument_manufacturer = lst[0]
            self._identity_instrument_model = lst[1]
            self._identity_instrument_firmware_revision = lst[3]
            self._set_cache_valid(True, 'identity_instrument_manufacturer')
            self._set_cache_valid(True, 'identity_instrument_model')
            self._set_cache_valid(True, 'identity_instrument_firmware_revision')
    
    def _get_identity_instrument_manufacturer(self):
        if self._get_cache_valid():
            return self._identity_instrument_manufacturer
        self._load_id_string()
        return self._identity_instrument_manufacturer
    
    def _get_identity_instrument_model(self):
        if self._get_cache_valid():
            return self._identity_instrument_model
        self._load_id_string()
        return self._identity_instrument_model
    
    def _get_identity_instrument_firmware_revision(self):
        if self._get_cache_valid():
            return self._identity_instrument_firmware_revision
        self._load_id_string()
        return self._identity_instrument_firmware_revision
    
    def _utility_disable(self):
        pass
    
    def _utility_error_query(self):
        error_code = 0
        error_message = "No error"
        if not self._driver_operation_simulate:
            error_code, error_message = self._ask(":evmsg?").split(',')
            error_code = int(error_code.split(' ', 1)[1])
            if error_code == 1:
                self._ask("*esr?")
                error_code, error_message = self._ask(":evmsg?").split(',')
                error_code = int(error_code.split(' ', 1)[1])
            error_message = error_message.strip(' "')
        return (error_code, error_message)
    
    def _utility_lock_object(self):
        pass
    
    def _utility_reset(self):
        if not self._driver_operation_simulate:
            self._write("*RST")
            self.driver_operation.invalidate_all_attributes()
    
    def _utility_reset_with_defaults(self):
        self._utility_reset()
    
    def _utility_self_test(self):
        code = 0
        message = "Self test passed"
        if not self._driver_operation_simulate:
            self._write("*TST?")
            # wait for test to complete
            time.sleep(60)
            code = int(self._read())
            if code != 0:
                message = "Self test failed"
        return (code, message)
    
    def _utility_unlock_object(self):
        pass

    def _check_last_error(self):
        """
        Retrieves the last error code from instrument. If an error occurred raise an IviException.
        """
        result = self._ask(':system:error?')
        if result is None:
            return result
        result = result.split(',')
        code = int(result[0])
        if code != 0:
            message = result[1][1:-1]
            raise ivi.IviException(message)
    
    def _load_wfm_catalog(self):
        """
        Loads all existing waveform names from instrument and saves list as self._wfm_catalog.

        Predefined waveforms have a name starting with *.
        """
        self._wfm_catalog = list()
        if not self._driver_operation_simulate:
            wfm_list_length = int(self._ask("wlist:size?"))
            for ii in range(wfm_list_length):
                name = self._ask('wlist:name? {0:d}'.format(ii))
                self._wfm_catalog.append(name[1:-1])

    # ************************ BASE ****************************************************************

    def _init_outputs(self):
        try:
            super(tektronixAWG5000, self)._init_outputs()
        except AttributeError:
            pass

        self._output_enabled = list()
        for i in range(self._output_count):
            self._output_enabled.append(False)

    def _get_output_operation_mode(self, index):
        index = ivi.get_index(self._output_name, index)
        return self._output_operation_mode[index]
    
    def _set_output_operation_mode(self, index, value):
        index = ivi.get_index(self._output_name, index)
        if value not in OperationMode:
            raise ivi.ValueNotSupportedException()
        self._output_operation_mode[index] = value
    
    def _get_output_enabled(self, index):
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask(":output%d:state?" % (index+1))
            self._output_enabled[index] = bool(int(resp))
            self._set_cache_valid(index=index)
        return self._output_enabled[index]
    
    def _set_output_enabled(self, index, value):
        index = ivi.get_index(self._output_name, index)
        value = bool(value)
        if not self._driver_operation_simulate:
            self._write(":output%d:state %d" % (index+1, value))
        self._output_enabled[index] = value
        self._set_cache_valid(index=index)
    
    def _get_output_impedance(self, index):
        index = ivi.get_index(self._output_name, index)
        self._output_impedance[index] = 50
        return self._output_impedance[index]
    
    def _set_output_impedance(self, index, value):
        index = ivi.get_index(self._output_name, index)
        value = 50
        self._output_impedance[index] = value
    
    def _get_output_mode(self, index):
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask(":awgcontrol:rmode?")
            if resp.lower() == 'seq':
                self._output_mode[index] = 'sequence'
            else:
                self._output_mode[index] = 'arbitrary'
            self._set_cache_valid(index=index)
        return self._output_mode[index]
    
    def _set_output_mode(self, index, value):
        index = ivi.get_index(self._output_name, index)
        if value not in fgen.OutputMode:
            raise ivi.ValueNotSupportedException()
        if value == 'function':
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            if value == 'sequence':
                self._write(":awgcontrol:rmode sequence")
            else:
                #FIXME: leave it as is if it is already != sequence???
                self._write(":awgcontrol:rmode continuous")
        self._output_mode[index] = value
        for k in range(self._output_count):
            self._set_cache_valid(valid=False,index=k)
        self._set_cache_valid(index=index)
    
    def _get_output_reference_clock_source(self, index):
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask(":source1:roscillator:source?")
            value = resp.lower()
            self._output_reference_clock_source[index] = SampleClockSourceMap[value]
            self._set_cache_valid(index=index)
        return self._output_reference_clock_source[index]
    
    def _set_output_reference_clock_source(self, index, value):
        index = ivi.get_index(self._output_name, index)
        if value not in fgen.SampleClockSource:
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            self._write(":source1:roscillator:source %s" % value)
        self._output_reference_clock_source[index] = value
        for k in range(self._output_count):
            self._set_cache_valid(valid=False,index=k)
        self._set_cache_valid(index=index)
    
    def abort_generation(self):
        self._write(":awgcontrol:stop:immediate")
    
    def initiate_generation(self):
        self._write(":awgcontrol:run:immediate")

    # ************************ Extension: ArbWfm ***************************************************
    
    def _get_output_arbitrary_gain(self, index):
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask(":source%d:voltage:amplitude?" % (index+1))
            self._output_arbitrary_gain[index] = float(resp)
            self._set_cache_valid(index=index)
        return self._output_arbitrary_gain[index]
    
    def _set_output_arbitrary_gain(self, index, value):
        index = ivi.get_index(self._output_name, index)
        value = float(value)
        if not self._driver_operation_simulate:
            self._write(":source%d:voltage:amplitude %e" % (index+1, value))
        self._output_arbitrary_gain[index] = value
        self._set_cache_valid(index=index)
    
    def _get_output_arbitrary_offset(self, index):
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask(":source%d:voltage:offset?" % (index+1))
            self._output_arbitrary_offset[index] = float(resp)
            self._set_cache_valid(index=index)
        return self._output_arbitrary_offset[index]
    
    def _set_output_arbitrary_offset(self, index, value):
        index = ivi.get_index(self._output_name, index)
        value = float(value)
        if not self._driver_operation_simulate:
            self._write(":source%d:voltage:offset %e" % (index+1, value))
        self._output_arbitrary_offset[index] = value
        self._set_cache_valid(index=index)
    
    def _get_output_arbitrary_waveform(self, index):
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask(":source%d:waveform?" % (index+1))
            self._output_arbitrary_waveform[index] = resp.strip('"').lower()
            self._set_cache_valid(index=index)
        return self._output_arbitrary_waveform[index]
    
    def _set_output_arbitrary_waveform(self, index, value):
        index = ivi.get_index(self._output_name, index)
        value = str(value).lower()
        # extension must be wfm
        ext = value.split('.').pop()
        if ext != 'wfm':
            raise ivi.ValueNotSupportedException()
        # waveform must exist on arb
        self._load_wfm_catalog()
        if value not in self._wfm_catalog:
            raise ivi.ValueNotSupportedException()
        if not self._driver_operation_simulate:
            self._write(":source%d:waveform \"%s\"" % (index+1, value))
        self._output_arbitrary_waveform[index] = value
    
    def _get_arbitrary_sample_rate(self):
        if not self._driver_operation_simulate and not self._get_cache_valid():
            resp = self._ask(":source1:frequency?")
            self._arbitrary_sample_rate = float(resp)
            self._set_cache_valid()
        return self._arbitrary_sample_rate
    
    def _set_arbitrary_sample_rate(self, value):
        value = float(value)
        if not self._driver_operation_simulate:
            self._write(":source1:frequency %e" % value)
        self._arbitrary_sample_rate = value
        self._set_cache_valid()
    
    def _get_arbitrary_waveform_number_waveforms_max(self):
        return self._arbitrary_waveform_number_waveforms_max
    
    def _get_arbitrary_waveform_size_max(self):
        return self._arbitrary_waveform_size_max
    
    def _get_arbitrary_waveform_size_min(self):
        return self._arbitrary_waveform_size_min
    
    def _get_arbitrary_waveform_quantum(self):
        return self._arbitrary_waveform_quantum
    
    def _arbitrary_waveform_clear(self, handle):
        # reload existing waveforms
        self._load_wfm_catalog()
        # check if handle exists in wfm catalog
        if not handle in self._wfm_catalog:
            raise ivi.InvalidOptionValueException('Handle {0} does not exists.'.format(handle))
        # delete waveform
        self._write(":wlist:waveform:delete \"%s\"" % handle)
        # if waveform was in use the generation was stopped
    
    def _arbitrary_waveform_create(self, data):
        y = None
        x = None
        dtype = 'real'
        if type(data) == list and type(data[0]) == float:
            # list
            y = array(data)
        elif type(data) == ndarray and len(data.shape) == 1:
            # 1D array
            y = data
            if issubdtype(data.dtype, integer):
                dtype = 'int'
        elif type(data) == ndarray and len(data.shape) == 2 and data.shape[0] == 1:
            # 2D array, height 1
            y = data[0]
            if issubdtype(data.dtype, integer):
                dtype = 'int'
        elif type(data) == ndarray and len(data.shape) == 2 and data.shape[1] == 1:
            # 2D array, width 1
            y = data[:,0]
            if issubdtype(data.dtype, integer):
                dtype = 'int'
        else:
            x, y = ivi.get_sig(data)
        
        if len(y) % self._arbitrary_waveform_quantum != 0:
            raise ivi.ValueNotSupportedException()
        
        # get unused handle
        self._load_wfm_catalog()
        have_handle = False
        while not have_handle:
            self._arbitrary_waveform_n += 1
            handle = "wfm%04d" % self._arbitrary_waveform_n
            have_handle = handle not in self._wfm_catalog

        # create waveform
        self._write(':wlist:waveform:new "{0:s}",{1:d},{2:s}'.format(handle, len(y), dtype))

        # transfer data to waveform
        raw_data = b''
        if dtype == 'real':
            for f in y:
                # clip at -1 and 1
                if f > 1.0: f = 1.0
                if f < -1.0: f = -1.0
                # add to raw data, LSB first
                raw_data = raw_data + struct.pack('<f', f)
                # add an empty marker byte
                raw_data = raw_data + b'\x00'
        else:
            for f in y:
                # add to raw data, LSB first
                raw_data = raw_data + struct.data('<h', f) # FIXME signed or unsigned, this is here the question

        # fixme: maybe better to split into chunks to be able to stop transmission?
        self._write_ieee_block(raw_data, ':wlist:waveform:data "{0:s}",{1:d},{2:d},'.format(
            handle, 0, len(y)))
        
        return handle

    # ************************ Extension: ArbSeq ***************************************************
    
    def _get_arbitrary_sequence_number_sequences_max(self):
        return self._arbitrary_sequence_number_sequences_max
    
    def _get_arbitrary_sequence_loop_count_max(self):
        return self._arbitrary_sequence_loop_count_max
    
    def _get_arbitrary_sequence_length_max(self):
        return self._arbitrary_sequence_length_max
    
    def _get_arbitrary_sequence_length_min(self):
        return self._arbitrary_sequence_length_min
    
    def _arbitrary_clear_memory(self):
        pass
    
    def _arbitrary_sequence_clear(self, handle):
        pass
    
    def _arbitrary_sequence_configure(self, index, handle, gain, offset):
        pass
    
    def _arbitrary_sequence_create(self, handle_list, loop_count_list):
        return "handle"

    # ************************ Extension: StartTrigger *********************************************

    def _get_output_start_trigger_delay(self, index):
        # trigger delay is not supported by instrument
        return 0

    def _set_output_start_trigger_delay(self, index, value):
        # setting trigger delay is not supported
        pass

    def _get_output_start_trigger_slope(self, index):
        # for the instrument only one global trigger exists
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask(':trigger:slope?').lower()
            resp = TriggerSlopeMap[resp]
            self._output_start_trigger_slope = [resp for ii in range(self._output_count)]
            self._set_cache_valid(index=index)
        return self._output_start_trigger_slope[index]

    def _set_output_start_trigger_slope(self, index, value):
        index = ivi.get_index(self._output_name, index)
        if value not in TriggerSlope:
            raise ivi.ValueNotSupportedException()
        if value == 'either':
            raise ivi.ValueNotSupportedException()
        self._write(':trigger:slope {0}'.format(value))
        self._output_start_trigger_slope = [value for ii in range(self._output_count)]
        self._set_cache_valid(index=index)

    def _get_output_start_trigger_source(self, index):
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = self._ask(':trigger:source?').lower()
            resp = TriggerSourceMap[resp]
            self._output_start_trigger_source = [resp for ii in range(self._output_count)]
            self._set_cache_valid(index=index)
        return self._output_start_trigger_source[index]

    def _set_output_start_trigger_source(self, index, value):
        index = ivi.get_index(self._output_name, index)
        if value is None:
            value = 'internal'
        if value not in TriggerSource:
            raise ivi.ValueNotSupportedException()
        self._write(':trigger:source {0}'.format(value))
        self._output_start_trigger_source = [value for ii in range(self._output_count)]
        self._set_cache_valid(index=index)

    def _get_output_start_trigger_threshold(self, index):
        # for the instrument only one global trigger exists
        index = ivi.get_index(self._output_name, index)
        if not self._driver_operation_simulate and not self._get_cache_valid(index=index):
            resp = float(self._ask(':trigger:level?'))
            self._output_start_trigger_threshold = [resp for ii in range(self._output_count)]
            self._set_cache_valid(index=index)
        return self._output_start_trigger_threshold[index]

    def _set_output_start_trigger_threshold(self, index, value):
        index = ivi.get_index(self._output_name, index)
        self._write(':trigger:level {0}V'.format(value))
        self._output_start_trigger_threshold = [value for ii in range(self._output_count)]
        self._set_cache_valid(index=index)

    def _start_trigger_send_software_trigger(self):
        self._write('*TRG')

    # ************************ Extension:  ***************************************************

    def send_software_trigger(self):
        if not self._driver_operation_simulate:
            self._write("*TRG")
    
    def _get_output_burst_count(self, index):
        index = ivi.get_index(self._output_name, index)
        return self._output_burst_count[index]
    
    def _set_output_burst_count(self, index, value):
        index = ivi.get_index(self._output_name, index)
        value = int(value)
        self._output_burst_count[index] = value
    
    def _arbitrary_waveform_create_channel_waveform(self, index, data):
        handle = self._arbitrary_waveform_create(data)
        self._set_output_arbitrary_waveform(index, handle)
        return handle
    
    

