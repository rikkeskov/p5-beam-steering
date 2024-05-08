"""
@date: 07 March 2024

@author: Rikke Udengaard <rudeng20@student.aau.dk

@project: beam steering

"""

import logging
from rohdeschwarz.instruments.vna import Vna, TraceFormat, Channel
logger = logging.getLogger(__name__)

class NetworkAnalyzer(object):
    def __init__(self, trace_id: str, s_param: str, freq: float, ip_address = '172.0.0.1', port: int = 5025, channel = 1) -> None:
        """ Initalize instance variables and connect.
        Instrument Type: ZVB8 with 2 Ports
        Part Number: 1145.1010k08
        Serial Number: 100113
        Device ID: 1145.1010K08-100113-DD
        IEC Bus Address: 20
        IP Adresses: IP Address 172.0.0.1 (Localhost) Subnet Mask: 255.0.0.0 """
        self.port: int = port
        out: tuple = self.connect(ip_address, port, channel)
        self.vna: Vna = out[0]
        self.ch: Channel = out[1]
        self.trace_id = trace_id
        self.s_param = s_param
        self.ch.start_frequency_Hz = freq, 'GHz'
        self.ch.stop_frequency_Hz = freq, 'GHz'
        self.ch.points = 1
        self.ch.if_bandwidth_Hz = 1, 'Hz'

    def connect(self, ip_address: str, port: int, ch: int) -> Vna:
        """ Try to connect to VNA with TCP. """
        try:
            sock = Vna()
            sock.open_tcp(ip_address, port)
        except Exception as e:
            logger.error(f'Cannot connect to VNA because {e}.')
            exit()
        else:
            logger.info(f'Connection established to VNA. Creating channel {ch}.')
            channel = sock.channel(ch)
            return sock, channel

    def run(self) -> tuple:
        """Measure S-Parameters for [trace_id]."""
        x, y = self.vna.trace(self.trace_id).measure_formatted_data()
        return x, y

    def reset(self):
        """ Preset the VNA. MUST manually redo setup from file on VNA. 
        Consider valibration. Done manually: Press cal -> start cal -> 
        two port -> normalize both directions -> choose ideal kit, 
        check in box 'through' -> apply"""
        self.vna.preset()

    def set(self):
        """ Establish trace for VNA. """
        self.vna.create_trace(self.trace_id, 1, self.s_param)
        self.vna.trace(self.trace_id).format = TraceFormat.magnitude_dB
        
    def stop(self) -> None:
        """Close connection."""
        try:
            self.vna.close()
        except Exception as e:
            logger.error(f'Cannot disconnect from VNA because {e}.')
        finally:
            exit()

    def get_settings(self) -> dict:
        settings = {}
        settings['sweep type'] = str(self.ch.sweep_type)
        settings['start freq'] = str(self.ch.start_frequency_Hz)
        settings['stop freq'] = str(self.ch.stop_frequency_Hz)
        settings['points'] = str(self.ch.points)
        settings['meas bw'] = str(self.ch.if_bandwidth_Hz)
        settings['power dbm'] = str(self.ch.power_dBm)
        return settings
