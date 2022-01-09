"""
Raspberry Pi Pico (MicroPython) exercise:
work with SIM868 GSM/GPRS/GNSS Module
"""
import machine
import os
import utime
import binascii

class Sim868:
    def __init__(self):
        # using pin defined
        self.led_pin = 25  # onboard led
        self.pwr_en = 14  # pin to control the power of the module
        self.uart_port = 0
        self.uart_baute = 115200

        self.APN = "CMNET"

        self.reading = 0
        self.temperature = 0

        # uart setting
        self.uart = machine.UART(self.uart_port, self.uart_baute)
        print(os.uname())

        # LED indicator on Raspberry Pi Pico
        self.led_onboard = machine.Pin(self.led_pin, machine.Pin.OUT)

        # HTTP Get Post Parameter
        self.http_get_server = ['http://api.seniverse.com', '/v3/weather/now.json?key=SwwwfskBjB6fHVRon&location=shenzhen&language=en&unit=c']
        self.http_post_server = ['http://pico.wiki', '/post-data.php', 'api_key=tPmAT5Ab3j888']
        self.http_post_tmp = 'api_key=tPmAT5Ab3j888&value1=26.44&value2=57.16&value3=1002.95'
        self.http_content_type = 'application/x-www-form-urlencoded'

        # MQTT Server info
        self.mqtt_host = '47.89.22.46'
        self.mqtt_port = '1883'

        self.mqtt_topic1 = 'testtopic'
        self.mqtt_topic2 = 'testtopic/led'
        self.mqtt_topic3 = 'testtopic/temp'
        self.mqtt_topic4 = 'testtopic/adc'
        self.mqtt_topic5 = 'testtopic/tempwarning'
        self.mqtt_topic6 = 'testtopic/warning'
        self.mqtt_topic7 = 'testtopic/gpsinfo'

        self.mqtt_msg = 'on'


    def led_blink(self):
        self.led_onboard.value(1)
        utime.sleep(1)
        self.led_onboard.value(0)
        utime.sleep(1)
        self.led_onboard.value(1)
        utime.sleep(1)
        self.led_onboard.value(0)


    # power on/off the module
    def power_on_off(self):
        pwr_key = machine.Pin(self.pwr_en, machine.Pin.OUT)
        pwr_key.value(1)
        utime.sleep(2)
        pwr_key.value(0)


    def hexstr_to_str(self, hex_str):
        hex_data = hex_str.encode('utf-8')
        str_bin = binascii.unhexlify(hex_data)
        return str_bin.decode('utf-8')


    def str_to_hexstr(self, string):
        str_bin = string.encode('utf-8')
        return binascii.hexlify(str_bin).decode('utf-8')


    def wait_resp_info(self, timeout=2000):
        prvmills = utime.ticks_ms()
        info = b""
        while (utime.ticks_ms()-prvmills) < timeout:
            if self.uart.any():
                info = b"".join([info, self.uart.read(1)])
        print(info.decode())
        return info


    # Send AT command
    def send_at(self, cmd, back, timeout=2000):
        rec_buff = b''
        self.uart.write((cmd+'\r\n').encode())
        prvmills = utime.ticks_ms()
        while (utime.ticks_ms()-prvmills) < timeout:
            if self.uart.any():
                rec_buff = b"".join([rec_buff, self.uart.read(1)])
        if rec_buff != '':
            if back not in rec_buff.decode():
                print(cmd + ' back:\t' + rec_buff.decode())
                return 0
            else:
                print(rec_buff.decode())
                return 1
        else:
            print(cmd + ' no responce')


    # Send AT command and return response information
    def send_at_wait_resp(self, cmd, back, timeout=2000):
        rec_buff = b''
        self.uart.write((cmd + '\r\n').encode())
        prvmills = utime.ticks_ms()
        while (utime.ticks_ms() - prvmills) < timeout:
            if self.uart.any():
                rec_buff = b"".join([rec_buff, self.uart.read(1)])
        if rec_buff != '':
            if back not in rec_buff.decode():
                print(cmd + ' back:\t' + rec_buff.decode())
            else:
                print(rec_buff.decode())
        else:
            print(cmd + ' no responce')
        # print("Response information is: ", rec_buff)
        return rec_buff


    # Module startup detection
    def check_start(self):
        while True:
            # simcom module uart may be fool,so it is better to send much times when it starts.
            self.uart.write(bytearray(b'ATE1\r\n'))
            utime.sleep(2)
            self.uart.write(bytearray(b'AT\r\n'))
            rec_temp = self.wait_resp_info()
            if 'OK' in rec_temp.decode():
                print('SIM868 is ready\r\n' + rec_temp.decode())
                break
            else:
                self.power_on_off()
                print('SIM868 is starting up, please wait...\r\n')
                utime.sleep(8)


    # Check the network status
    def check_network(self):
        for i in range(1, 3):
            if self.send_at("AT+CGREG?", "0,1") == 1:
                print('SIM868 is online\r\n')
                break
            else:
                print('SIM868 is offline, please wait...\r\n')
                utime.sleep(5)
                continue
        self.send_at("AT+CPIN?", "OK")
        self.send_at("AT+CSQ", "OK")
        self.send_at("AT+COPS?", "OK")
        self.send_at("AT+CGATT?", "OK")
        self.send_at("AT+CGDCONT?", "OK")
        self.send_at("AT+CSTT?", "OK")
        self.send_at("AT+CSTT=\""+self.APN+"\"", "OK")
        self.send_at("AT+CIICR", "OK")
        self.send_at("AT+CIFSR", "OK")


    # Get the gps info
    def get_gps_info(self):
        count = 0
        print('Start GPS session...')
        self.send_at('AT+CGNSPWR=1', 'OK')
        utime.sleep(2)
        for i in range(1, 10):
            self.uart.write(bytearray(b'AT+CGNSINF\r\n'))
            rec_buff = self.wait_resp_info()
            if ',,,,' in rec_buff.decode():
                print('GPS is not ready')
    #           print(rec_buff.decode())
                if i >= 9:
                    print('GPS positioning failed, please check the GPS antenna!\r\n')
                    self.send_at('AT+CGNSPWR=0', 'OK')
                else:
                    utime.sleep(2)
                    continue
            else:
                if count <= 3:
                    count += 1
                    print('GPS info:')
                    print(rec_buff.decode())
                else:
                    self.send_at('AT+CGNSPWR=0', 'OK')
                    break


    # Bearer Configure
    def bearer_config(self):
        self.send_at('AT+SAPBR=3,1,\"Contype\",\"GPRS\"', 'OK')
        self.send_at('AT+SAPBR=3,1,\"self.APN\",\"'+self.APN+'\"', 'OK')
        self.send_at('AT+SAPBR=1,1', 'OK')
        self.send_at('AT+SAPBR=2,1', 'OK')
    #   send_at('AT+SAPBR=0,1', 'OK')


    # HTTP GET TEST
    def http_get(self):
        self.send_at('AT+HTTPINIT', 'OK')
        self.send_at('AT+HTTPPARA=\"CID\",1', 'OK')
        self.send_at('AT+HTTPPARA=\"URL\",\"'+self.http_get_server[0]+self.http_get_server[1]+'\"', 'OK')
        if self.send_at('AT+HTTPACTION=0', '200', 5000):
            self.uart.write(bytearray(b'AT+HTTPREAD\r\n'))
            rec_buff = self.wait_resp_info(8000)
            print("resp is :", rec_buff.decode())
        else:
            print("Get HTTP failed, please check and try again\n")
        self.send_at('AT+HTTPTERM', 'OK')


    # HTTP POST TEST
    def http_post(self):
        self.send_at('AT+HTTPINIT', 'OK')
        self.send_at('AT+HTTPPARA=\"CID\",1', 'OK')
        self.send_at('AT+HTTPPARA=\"URL\",\"'+self.http_post_server[0]+self.http_post_server[1]+'\"', 'OK')
        self.send_at('AT+HTTPPARA=\"CONTENT\",\"' + self.http_content_type + '\"', 'OK')
        if self.send_at('AT+HTTPDATA=62,8000', 'DOWNLOAD', 3000):
            self.uart.write(bytearray(self.http_post_tmp))
            utime.sleep(5)
            rec_buff = self.wait_resp_info()
            if 'OK' in rec_buff.decode():
                print("UART data is read!\n")
            if self.send_at('AT+HTTPACTION=1', '200', 8000):
                print("POST successfully!\n")
            else:
                print("POST failed\n")
            self.send_at('AT+HTTPTERM', 'OK')
        else:
            print("HTTP Post failed，please try again!\n")


    # Get the gps info
    def phone_call(self, phone_num='10000', keep_time=10):
        self.send_at('AT+CHFA=1', 'OK')
        self.send_at('ATD'+phone_num+';', 'OK')
        utime.sleep(keep_time)
        self.send_at('AT+CHUP;', 'OK')


    # SMS test
    def sms_test(self, phone_num='10000', sms_info=""):
        self.send_at('AT+CMGF=1:', 'OK')
        if self.send_at('AT+CMGS=\"'+phone_num+'\"', '>'):
            self.uart.write(bytearray(sms_info))
            self.uart.write(bytearray(self.hexstr_to_str("1A")))


    # Bluetooth scan
    def bluetooth_scan(self):
        self.send_at('AT+BTPOWER=1', 'OK', 3000)
        self.send_at('AT+BTHOST?', 'OK', 3000)
        self.send_at('AT+BTSTATUS?', 'OK', 3000)
        self.send_at('AT+BTSCAN=1,10', 'OK', 8000)
        self.send_at('AT+BTPOWER=0', 'OK')


    # AT test
    def at_test(self):
        print("---------------------------SIM868 TEST---------------------------")
        while True:
            try:
                command_input = str(input('Please input the AT command,press Ctrl+C to exit: '))
                self.send_at(command_input, 'OK', 2000)
            except KeyboardInterrupt:
                print("\r\nExit AT command test!\n")
                self.power_on_off()
                print("Power off the module!\n")
                break
