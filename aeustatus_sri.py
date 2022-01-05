#!/usr/bin/env python

################################################################
#
#   AEU Status Word
#
#   Parse the raw status output from an AEU. This object is
#   nearly a direct translation of the aeu_status.c file in
#   the paneltools package.
#
#   1.0.0   2004-07-16  Todd Valentic
#           Initial implementation
#
#   1.0.1   2006-02-09  Todd Valentic
#           Added support for Ver 3 status format
#
#   1.0.2   2006-03-13  Todd Valentic
#           Added computation of power forward (pfwd)
#               and peak power (V*I)
#
#   1.0.3   2006-05-04  Todd Valentic
#           Added suppoed for Ver 4 status format
#
#   1.0.4   2006-10-26  Todd Valentic
#           Added pref to power computation
#
#   1.0.5   2007-03-15  Todd Valentic
#           Added alarm_summary (applies to Comtech SSPAs)
#
################################################################

AEU_ALARM_PULSEWIDTH        = 0x02
AEU_ALARM_OVERDRIVE         = 0x04
AEU_ALARM_OVERTEMP_LATCH    = 0x08
AEU_ALARM_DEWSENSOR         = 0x10
AEU_ALARM_OVERCURRENT       = 0x20
AEU_ALARM_EXTENDED          = 0x40
AEU_ALARM_OVERTEMP          = 0x80

AEU_ENABLE_INTERRUPT        = 0x01
AEU_ENABLE_BYPASS           = 0x02
AEU_ENABLE_OFFSET           = 0x04
AEU_ENABLE_FORCED           = 0x08
AEU_ENABLE_BROWNOUT         = 0x10
AEU_ENABLE_SSPAPOWER        = 0x20
AEU_ENABLE_SSPAGATE         = 0x40

AEU_SIGNAL_POWER_FWD        = 0
AEU_SIGNAL_POWER_REF        = 1
AEU_SIGNAL_ANTA_REF_I       = 2
AEU_SIGNAL_ANTA_REF_Q       = 3
AEU_SIGNAL_ANTA_FWD_I       = 4
AEU_SIGNAL_ANTA_FWD_Q       = 5
AEU_SIGNAL_ANTB_FWD_I       = 6
AEU_SIGNAL_ANTB_REF_Q       = 7
AEU_SIGNAL_ANTB_FWD_I       = 8
AEU_SIGNAL_ANTB_REF_Q       = 9

AEU_ALARM_STATE_OK          = 0
AEU_ALARM_STATE_TEMP        = 1
AEU_ALARM_STATE_VSWR        = 2
AEU_ALARM_STATE_SUMMARY     = 3

class AEUStatus:

    def __init__(self):
        self.reset()


    def reset(self):
        self.pulse_width_alarm      = False
        self.sspa_overdrive_alarm   = False
        self.sspa_overtemp_alarm    = False
        self.sspa_overtemp_alarm_latch=False
        self.dew_sensor_alarm       = False
        self.extended_funcs         = False
        self.sspa_overcurrent_alarm = False
        self.signal_voltage         = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.brownout_alarm         = False
        self.alarm_state            = 0
        self.sspa_voltage_monitor   = 0.0
        self.sspa_current_monitor   = 0.0  # Amps
        self.controller_temp        = 0.0  # deg C
        self.sspa_temp              = 0.0  # deg C

    def update(self,raw):

        try:
            raw = [int(x,16) for x in raw.split()]
        except:
            raw = [90, 4, 2, 0, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
             0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.dataIn = raw
        self.board_id       = raw[0]
        self.status_format  = raw[1]
        self.firmware_major = raw[2]
        self.firmware_minor = raw[3]
        self.firmware_patch = raw[4]

        if self.board_id != 0x5A:
            raise IOError('Unknown board type: 0x#X' % self.board_id)

        if self.status_format==0:
            self.parse_0(raw[5:])
        elif self.status_format==1:
            self.parse_1(raw[5:])
        elif self.status_format==2:
            self.parse_2(raw[5:])
        elif self.status_format==3:
            self.parse_3(raw[5:])
        elif self.status_format==4:
            self.parse_4(raw[5:])
        else:
            raise IOError('Unknown status_format: %d' % self.status_format)

        self.compute_power()
        self.compute_alarms()

    def compute_alarms(self):

        if not self.sspa_overdrive_alarm and not self.sspa_overtemp_alarm:
            self.alarm_state = AEU_ALARM_STATE_OK
        elif not self.sspa_overdrive_alarm and self.sspa_overtemp_alarm:
            self.alarm_state = AEU_ALARM_STATE_TEMP
        elif self.sspa_overdrive_alarm and not self.sspa_overtemp_alarm:
            self.alarm_state = AEU_ALARM_STATE_VSWR
        else:
            self.alarm_state = AEU_ALARM_STATE_SUMMARY

    def compute_power(self):

        vfwd_cal = 215*(2.5/255)      # typical forward power (57dBm) in V
        m = 0.045                     # V/dBm (?)

        self.pfwd = 57 - (vfwd_cal - self.signal_voltage[0])/m
        self.pref = 57 - (vfwd_cal - self.signal_voltage[1])/m
#        print 'Signal Voltage',self.signal_voltage
        if  self.sspa_power_enabled         and \
            self.sspa_gating_enabled        and \
            self.sspa_current_monitor>0.3   and \
            self.pfwd>45:

            I = self.sspa_current_monitor
            V = self.sspa_voltage_monitor
            power = I*V
        else:
            power = 0

        self.pwatts = power

    def parse_0(self,args):

        adcscale = 5./1023

        self.pulse_width_alarm      = bool(args[0] & AEU_ALARM_PULSEWIDTH)
        self.sspa_overdrive_alarm   = bool(args[0] & AEU_ALARM_OVERDRIVE)
        self.sspa_overtemp_alarm    = bool(args[0] & AEU_ALARM_OVERTEMP)
        self.sspa_overtemp_alarm_latch=bool(args[0]&AEU_ALARM_OVERTEMP_LATCH)
        self.dew_sensor_alarm       = bool(args[0] & AEU_ALARM_DEWSENSOR)
        self.extended_funcs         = not bool(args[0] & AEU_ALARM_EXTENDED)
        self.sspa_overcurrent_alarm = bool(args[0] & AEU_ALARM_OVERCURRENT)

        self.signal_select          = (args[1]>>5) & 0x07
        self.signal_count           = args[2:4]
        self.signal_voltage         = [v*2.5/255 for v in args[2:4]]

        self.sspa_power_enabled     = bool(args[4])
        self.sspa_gating_enabled    = bool(args[5])
        self.interrupt_enabled      = bool(args[6])

        self.p5v_voltage_monitor    = 2*adcscale*args[7]
        self.p8v_voltage_monitor    = 2*adcscale*args[13]

        c = 5.11/(5.11+2)
        v = (self.p8v_voltage_monitor*c - (adcscale*args[8]))/(c-1)
        self.m8v_voltage_monitor    = v

        self.sspa_voltage_monitor   = 11*adcscale*args[9]

        c = 2./(20+2)
        self.sspa_current_monitor   = (adcscale*args[10])/0.8592  # Amps

        self.controller_temp        = (adcscale*args[11]-0.5)/0.01  # deg C
        self.sspa_temp              = (adcscale*args[12]-0.5)/0.01  # deg C

        self.interrupt_count        = args[15]
        self.power_sample_delay     = args[16]/4.0  # usecs
        self.power_sample_counts    = args[16]

        self.bypass_enabled         = False
        self.offset_enabled         = False
        self.forced_enabled         = False

    def parse_1(self,args):
        self.parse_0(args)

        self.bypass_enabled         = bool(args[17])
        self.offset_enabled         = False
        self.forced_enabled         = False

    def parse_2(self,args):
        self.parse_1(args)

        self.offset_enabled         = bool(args[18])
        self.forced_enabled         = False

    def parse_3(self,args):

        adcscale = 5./1023

        self.pulse_width_alarm      = bool(args[0] & AEU_ALARM_PULSEWIDTH)
        self.sspa_overdrive_alarm   = bool(args[0] & AEU_ALARM_OVERDRIVE)
        self.sspa_overtemp_alarm    = bool(args[0] & AEU_ALARM_OVERTEMP)
        self.sspa_overtemp_alarm_latch=bool(args[0]&AEU_ALARM_OVERTEMP_LATCH)
        self.dew_sensor_alarm       = bool(args[0] & AEU_ALARM_DEWSENSOR)
        self.extended_funcs         = not bool(args[0] & AEU_ALARM_EXTENDED)
        self.sspa_overcurrent_alarm = bool(args[0] & AEU_ALARM_OVERCURRENT)

        self.signal_select          = (args[1]>>5) & 0x07
        self.signal_count           = args[2:4]
        self.signal_voltage         = [v*2.5/255 for v in args[2:4]]

        self.interrupt_enabled      = bool(args[4] & AEU_ENABLE_INTERRUPT)
        self.bypass_enabled         = bool(args[4] & AEU_ENABLE_BYPASS)
        self.offset_enabled         = bool(args[4] & AEU_ENABLE_OFFSET)
        self.forced_enabled         = bool(args[4] & AEU_ENABLE_FORCED)
        self.sspa_power_enabled     = bool(args[4] & AEU_ENABLE_SSPAPOWER)
        self.sspa_gating_enabled    = bool(args[4] & AEU_ENABLE_SSPAGATE)
        self.brownout_alarm         = bool(args[4] & AEU_ENABLE_BROWNOUT)

        self.p5v_voltage_monitor    = 2*adcscale*args[5]
        self.p8v_voltage_monitor    = 2*adcscale*args[11]

        c = 5.11/(5.11+2)
        v = (self.p8v_voltage_monitor*c - (adcscale*args[6]))/(c-1)
        self.m8v_voltage_monitor    = v

        self.sspa_voltage_monitor   = 11*adcscale*args[7]

        c = 2./(20+2)
        self.sspa_current_monitor   = (adcscale*args[8])/0.8592  # Amps

        self.controller_temp        = (adcscale*args[9]-0.5)/0.01  # deg C
        self.sspa_temp              = (adcscale*args[10]-0.5)/0.01  # deg C

        self.interrupt_count        = args[13]
        self.power_sample_delay     = args[14]/4.0  # usecs
        self.power_sample_counts    = args[14]

    def parse_4(self,args):
        #print("args", len(args),args)
        adcscale = 5./1023

        self.pulse_width_alarm      = bool(args[0] & AEU_ALARM_PULSEWIDTH)
        self.sspa_overdrive_alarm   = bool(args[0] & AEU_ALARM_OVERDRIVE)
        self.sspa_overtemp_alarm    = bool(args[0] & AEU_ALARM_OVERTEMP)
        self.sspa_overtemp_alarm_latch=bool(args[0]&AEU_ALARM_OVERTEMP_LATCH)
        self.dew_sensor_alarm       = bool(args[0] & AEU_ALARM_DEWSENSOR)
        self.extended_funcs         = not bool(args[0] & AEU_ALARM_EXTENDED)
        self.sspa_overcurrent_alarm = bool(args[0] & AEU_ALARM_OVERCURRENT)

        self.signal_count           = args[1:11]
        self.signal_voltage         = [v*2.5/255 for v in self.signal_count]

        self.interrupt_enabled      = bool(args[11] & AEU_ENABLE_INTERRUPT)
        self.bypass_enabled         = bool(args[11] & AEU_ENABLE_BYPASS)
        self.offset_enabled         = bool(args[11] & AEU_ENABLE_OFFSET)
        self.forced_enabled         = bool(args[11] & AEU_ENABLE_FORCED)
        self.sspa_power_enabled     = bool(args[11] & AEU_ENABLE_SSPAPOWER)
        self.sspa_gating_enabled    = bool(args[11] & AEU_ENABLE_SSPAGATE)
        self.brownout_alarm         = bool(args[11] & AEU_ENABLE_BROWNOUT)

        self.p5v_voltage_monitor    = 2*adcscale*args[12]
        self.p8v_voltage_monitor    = 2*adcscale*args[18]
        try:
            c = 5.11/(5.11+2)
            v = (self.p8v_voltage_monitor*c - (adcscale*args[13]))/(c-1)
            self.m8v_voltage_monitor    = v
            c = 2./(20+2)
            self.sspa_current_monitor   = (adcscale*args[15])/0.8592  # Amps
            self.controller_temp        = (adcscale*args[16]-0.5)/0.01  # deg C
            self.sspa_temp              = (adcscale*args[17]-0.5)/0.01  # deg C

            self.power_sample_delay     = args[29]/4.0  # usecs
            self.power_sample_counts    = args[29]
        except:
            pass
        self.interrupt_count        = args[20]
        self.beamcodes              = args[21:29]
        self.sspa_voltage_monitor   = 11*adcscale*args[14]
if __name__ == '__main__':

    raw = '5A 02 01 01 1A 51 00 C4 93 01 01 01  01FF 0292 0263 0182 00BA 00BA 02EE 0000 01AE8F8B FF 01 FF'
    raw = '5A 02 01 01 1A 51 00 C4 93 01 01 01  01FF 0292 0263 0182 00BA 00BA 02EE 0000 01AE8F8B FF 01 FF'
    raw = '5A 02 01 01 1A 51 00 C4 93 01 01 01  01FF 0292 0263 0182 00BA 00BA 02EE 0000 01AE8F8B FF 01 FF'
    raw = '5A 02 01 01 1A 51 00 C4 93 01 01 01  01FF 0292 0263 0182 00BA 00BA 02EE 0000 01AE8F8B FF 01 FF'
    raw = '5A 04 02 00 0C 00 00 C7 7B CF 40 D3 4B 53 6C 90 65 01FF 01C6 025F 01A4 00BA 00C1 026A 0000 00810207 680A 680A 680A 680A 680A 67E6 67E6 67E6 3C'
    raw = []
    status = AEUStatus()
    status.update(raw)
    print (round(status.signal_voltage[0],1))
    for key,value in status.__dict__.items():
        print(key,'=',value)
