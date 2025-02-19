# ignoreShadowedImports
from utime import *
from micropython import const

_TS_YEAR = const(0)
_TS_MON = const(1)
_TS_MDAY = const(2)
_TS_HOUR = const(3)
_TS_MIN = const(4)
_TS_SEC = const(5)
_TS_WDAY = const(6)
_TS_YDAY = const(7)
_TS_ISDST = const(8)

_WDAY = const(("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"))
_MDAY = const(
    (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
)


from io import StringIO
# allocate reusable string io buffer for constructing format strings
__ft_buf = StringIO(30) 
def strftime(datefmt, ts):
    fmtsp = False
    # ftime = StringIO()
    __ft_buf.seek(0)
    # ftime.buffer.truncate()
    for k in datefmt:
        if fmtsp:
            if k == "a":
                __ft_buf.write(_WDAY[ts[_TS_WDAY]][0:3])
            elif k == "A":
                __ft_buf.write(_WDAY[ts[_TS_WDAY]])
            elif k == "b":
                __ft_buf.write(_MDAY[ts[_TS_MON] - 1][0:3])
            elif k == "B":
                __ft_buf.write(_MDAY[ts[_TS_MON] - 1])
            elif k == "d":
                __ft_buf.write("%02d" % ts[_TS_MDAY])
            elif k == "H":
                __ft_buf.write("%02d" % ts[_TS_HOUR])
            elif k == "I":
                __ft_buf.write("%02d" % (ts[_TS_HOUR] % 12))
            elif k == "j":
                __ft_buf.write("%03d" % ts[_TS_YDAY])
            elif k == "m":
                __ft_buf.write("%02d" % ts[_TS_MON])
            elif k == "M":
                __ft_buf.write("%02d" % ts[_TS_MIN])
            elif k == "P":
                __ft_buf.write("AM" if ts[_TS_HOUR] < 12 else "PM")
            elif k == "S":
                __ft_buf.write("%02d" % ts[_TS_SEC])
            elif k == "w":
                __ft_buf.write(str(ts[_TS_WDAY]))
            elif k == "y":
                __ft_buf.write("%02d" % (ts[_TS_YEAR] % 100))
            elif k == "Y":
                __ft_buf.write(str(ts[_TS_YEAR]))
            else:
                __ft_buf.write(k)
            fmtsp = False
        elif k == "%":
            fmtsp = True
        else:
            __ft_buf.write(k)
    length = __ft_buf.tell()
    __ft_buf.seek(0)
    val = __ft_buf.read(length)
    # val = ftime.getvalue()
    # ftime.close()
    return val
