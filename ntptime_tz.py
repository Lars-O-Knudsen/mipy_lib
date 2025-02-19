try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct

from asyncio import sleep
import math
import machine
import time # type: ignore


# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 3155673600

# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
host = "servante"
# host = "ntp.pool.org"


def ntptime():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(10)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    return val - NTP_DELTA



"""
    Determins the EU 'daylight saving time' period of the year of dt
    Then returns the number of seconds to add for correct adjustment
    of dt to dst (0 or 3600)
"""
def eu_dst_offset(dt): 
    cur = time.gmtime(dt)
    if cur[1] == 3 and cur[1] == 10:
        cest_day_of_mar = 31 - math.trunc(5*cur[0]/4 + 4) % 7
        cest_day_of_oct = 31 - math.trunc((5*cur[0]/4 + 1)) % 7
        cest_start = time.mktime( (cur[0], 3, cest_day_of_mar,2,0,0,None,None))
        cest_end = time.mktime( (cur[0], 10, cest_day_of_oct,2,0,0,None,None))
        # print("Year",cur[0], "cest start:", time.gmtime(cest_start),"end:",time.gmtime(cest_end) )
        if cest_start <= dt and cest_end >= dt:
            return 3600
    elif cur[1] > 3 and cur[1] < 10:
        return 3600
    else:
        return 0


"""
    Calculates number of seconds to add/subtract for a given timezone
    format of timezone specifier:
        [GMT] [+]|-<number>
        'gmt -1', 'gmt +1','gmt-7','-6','+1','1'
"""
def timezone_offset(tz_str: str):
    try:
        s:str=tz_str.upper()
        s = s.replace(' ', '')
        s= s.replace('GMT','')
        if s == '': 
            mult = 0
        else:
            mult = eval(s)
        return mult*3600
    except Exception as ex:
        print("Invalid timezone string:", tz_str)
        print(ex)
    return 0


# without tz adjustment, There's currently no timezone support in MicroPython, and the RTC is set in UTC time.
def settime():
    t = ntptime()
    tm = time.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))


def settime_tz( tz:str, adjust_eu_dst: bool = False):
    t = ntptime() + timezone_offset(tz)
    if adjust_eu_dst: 
        t += eu_dst_offset(t)
    tm = time.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))    


async def settime_tz_async( tz:str, adjust_eu_dst: bool = False):
    while True:
        try:
            settime_tz(tz,adjust_eu_dst)
            return time.time
        except:
            await sleep(1)
