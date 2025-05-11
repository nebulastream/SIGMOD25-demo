import serial
import time
import struct
import yaml
import logging
import traceback

from publishing_workers import make_message

# logging config
def load_config(path="config/script/config.yaml"):
    with open(path, "r") as file:
        return yaml.safe_load(file)

config = load_config()
signals_config = config["signals"]

log_level = getattr(logging, config["log_level"].upper(), logging.INFO)
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")


def run():
    ser = serial.Serial(port=config["serial_port"], baudrate=19200, bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

    # Send break message to wake the server up
    ser.send_break()

    # Send MSG 50h
    ser.write(bytes([0xA5, 0x02, 0x00, 0x50, 0xF7]))

    # Allow time for the server to respond
    time.sleep(0.3)

    # Read and parse MSG 50h response
    data = ser.read(ser.in_waiting)
    logging.debug(f"Received MSG 50h response: {data.hex()}")
    parseMsg50(data)

    while True:
        # Send MSG 57h
        ser.write(bytes([0xA5, 0x02, 0x00, 0x57, 0xFE]))

        # Change this value to adjust request frequency
        time.sleep(0.35) # 0.35 seems to be the lowest we can go before gibberish is returned

        # Read response
        data = ser.read(ser.in_waiting)
        if data:
            logging.debug(f"Received MSG 57h response: {data.hex()}")
            parseMsg57(data)
        else: break

    #client.disconnect()


def parseMsg50(data):
    # Format:
    # B: sync byte
    # B: lenlo
    # B: lenhi
    # B: transaction_code
    # B: device_code
    # B: language
    # B: support_level
    # 8s: server_status
    # 8s: server_datetime
    # 8s: software_version
    # 6s: protocol_rev
    # B: checksum
    fmt = 'B B B B B B B B 8s 8s 6s B'  # 28-byte response

    try:
        unpacked_data = struct.unpack(fmt, data)

        sync_byte = unpacked_data[0]
        lenlo = unpacked_data[1]
        lenhi = unpacked_data[2]
        transaction_code = unpacked_data[3]
        device_code = unpacked_data[4]
        language = unpacked_data[5]
        support_level = unpacked_data[6]
        server_status = unpacked_data[7]
        server_datetime = unpacked_data[8]
        software_version = unpacked_data[9].decode().strip('\x00')
        protocol_rev = unpacked_data[10].decode().strip('\x00')
        checksum = unpacked_data[11]

        logging.debug("=== MSG 50h Response ===")
        logging.debug(f"Sync Byte: {hex(sync_byte)}")
        logging.debug(f"Message Length: {lenlo + (lenhi << 8)} bytes")
        logging.debug(f"Transaction Code: {hex(transaction_code)}")
        logging.debug(f"Device Code: {device_code} ({decodeDevice(device_code)})")
        logging.debug(f"Language: {language} ({decodeLanguage(language)})")
        logging.debug(f"Support Level: {support_level}")
        logging.debug(f"Server Status: {server_status} ({decodeServerStatus(server_status)})")
        logging.debug(f"Server Date/Time: {parseDatetime(server_datetime)}")
        logging.debug(f"Software Version: {software_version}")
        logging.debug(f"Protocol Revision: {protocol_rev}")
        logging.debug(f"Checksum: {hex(checksum)}")
        logging.debug("=========================")

    except struct.error as e:
        logging.warning(f"Error parsing MSG 50h: {e}")


def parseMsg57(data):
    # Format:
    # B: sync byte
    # B: lenlo
    # B: lenhi
    # B: transaction code
    # B: reserved
    # B: shutdown_flag
    # 8s: waveform_ids
    # 8s: reserved
    # B: reserved
    # B: Number of Parameter subpackets
    fmt_header = "B B B B B B 8s 8s B B"  # Parsing the header before subpackets

    try:
        #unpack the fixed-length header
        header_size = struct.calcsize(fmt_header)
        unpacked_data = struct.unpack(fmt_header, data[:header_size])

        sync_byte = unpacked_data[0]
        low_len = unpacked_data[1]
        high_len = unpacked_data[2]
        transaction_code = unpacked_data[3]
        reserved_1 = unpacked_data[4]
        shutdown_flag = unpacked_data[5]
        waveform_ids = unpacked_data[6]
        reserved_2 = unpacked_data[7]
        reserved_3 = unpacked_data[8]
        pmnumb = unpacked_data[9]

        params_data = data[header_size:]

        logging.debug("=== MSG 57h Response ===")
        logging.debug(f"Sync Byte: {hex(sync_byte)}")
        logging.debug(f"Low Len: {hex(low_len)}")
        logging.debug(f"High Len: {hex(high_len)}")
        logging.debug(f"Transaction Code: {hex(transaction_code)}")
        logging.debug(f"Number of PARAM subpackets to follow: {pmnumb}")

        parse_subpackages(params_data, pmnumb)

        logging.debug("=========================")

    except struct.error as e:
        logging.warning(f"Error parsing MSG 57h. Could just be because a sensor was taken off. Error: {e}. ")
    except Exception as e:
        logging.error(f"Error parsing MSG57h: {e}")
        logging.error(traceback.format_exc())

def parse_subpackages(packages_data, pmnumb):
    #logging.debug("data_raw: ", packages_data.hex())

    index = 0
    # the subpackets
    for i in range(pmnumb):
        subpackage_data = {}

        logging.debug(f"subpackage {i+1}")

        #logging.debug("data raw: ", packages_data[index:].hex())
        #logging.debug("hex data raw:", " ".join(packages_data[index:].hex()[i:i + 2] for i in range(0, len(packages_data[index:].hex()), 2)))
        logging.debug("hex data raw: %s", " ".join(packages_data[index:].hex()[i:i + 2] for i in range(0, len(packages_data[index:].hex()), 2)))
        #logging.debug("data raw: ", packages_data[index:])

        # Format:
        # B: subpackage length
        # B: PARAM COUNT
        # 6s: some stuff we ignore (3-8)
        fmt_subpackage = 'B B 6s'
        subpackage_length, param_count, ignored = struct.unpack_from(fmt_subpackage, packages_data[index:])

        subpackage_data["param_count"] = param_count & 0x07  # Extract bits 0-2

        logging.debug(f"    subpackage length: {subpackage_length}, [hex: {hex(subpackage_length)}]")
        logging.debug(f"    PARAM COUNT: {param_count & 0x07}, [hex: {hex(param_count & 0x07)}]") # extract only bit 0, 1, 2
        #logging.debug(f"    if bit 3 is 1, then has timestamp: {param_count:08b}")
        has_timestamp = param_count & 0x08 != 0 # determines if there is a timestamp (true if bit 3 is set)
        logging.debug(f"    has_timestamp: {has_timestamp}")
        logging.debug(f"    ignored: {ignored}")

        offset = subpackage_length - 8 # tracks the timestamp and other bytes after the param bytes
        index += 8

        #the parameters
        for j in range(param_count & 0x07):
            # Format:
            # B: Paramater Code for 1st Parameter
            # B: Status for 1st parameter
            fmt_param = 'B B'
            #logging.debug("data raw: ", packages_data[index:].hex())
            param_code, param_status = struct.unpack_from(fmt_param, packages_data[index:])
            param_status_1_2 = param_status & 0x03 #TODO: check if correct
            param_status_3_4 = (param_status >> 3) & 0x03 #TODO: check if correct
            #logging.debug(param_status_1_2)
            #logging.debug(param_status_3_4)

            index += 2
            offset -= 2

            #read all values in ASCII until null value (0x00)
            param_value_str = ""
            while True:
                param_value = struct.unpack_from('B', packages_data[index:])[0]
                #logging.debug(chr(param_value))
                index += 1
                offset -= 1
                if param_value == 0x00:
                    break
                param_value_str += chr(param_value)

            logging.debug(f"        Param {j+1}: {{code: {hex(param_code)}, status: {{{param_status_1_2} ({decodeParamStatus_1_2(param_status_1_2)}), {param_status_3_4} ({decodeParamStatus_3_4(param_status_3_4)})}}, value: {param_value_str} [hex: {param_value_str.encode().hex()}]}}")

            make_message(param_code, param_value_str, signals_config)

        checksum = struct.unpack('B', packages_data[index:index+1])[0] #TODO: calculate and check message for correctness
        logging.debug(f"    checksum: {hex(checksum)}")

        #has_timestamp = struct.unpack('B', packages_data[index:index+1])[0]
        #first_value = struct.unpack('B', data[:1])[0]
        #logging.debug("has_timestamp: ", hex(has_timestamp))
        #logging.debug("INDEX: ", index)

        if has_timestamp:
            day, hour = struct.unpack("B B", packages_data[index + 1:index + 3])  # 2 bytes
            minute, second = struct.unpack("B B", packages_data[index + 3:index + 5])  # 2 bytes
            logging.debug(f"timestamp: {{day: {day}, hour: {hour}, minute: {minute}, second: {second}}}")

        #logging.debug("OFFSET: ", offset)
        index += offset

    return None

def parseDatetime(data):
    century, year, month, day, hour, minute, second, _ = struct.unpack('BBBBBBBB', data)
    return f"{century}{year:02}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}"


def decodeDevice(device_code):
    device_map = {
        0x01: "Modular Monitor",
        0x02: "Configured Monitor",
        0x09: "Reserved"
    }
    return device_map.get(device_code, "Unknown")


def decodeLanguage(language_code):
    language_map = {
        0x01: "English",
        0x02: "German",
        0x03: "French",
        0x04: "Spanish",
        0x05: "Italian",
        0x06: "Dutch"
    }
    return language_map.get(language_code, "Unknown")


def decodeServerStatus(status_code):
    status_map = {
        0x00: "Active",
        0x01: "Standby",
        0x02: "Patient Discharged"
    }
    return status_map.get(status_code, "Unknown")

def decodeParamStatus_1_2(status_code):
    status_map = {
        0x00: "No Alarm",
        0x01: "Advisory Alarm",
        0x02: "Serious Alarm",
        0x03: "Life Threatening Alarm",
    }
    return status_map.get(status_code, "Unknown")

def decodeParamStatus_3_4(status_code):
    status_map = {
        0x00: "No Alarm",
        0x01: "Active Alarm",
        0x02: "Latched Alarm",
        0x03: "Silenced Alarm",
    }
    return status_map.get(status_code, "Unknown")


