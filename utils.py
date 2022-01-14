



def decodeDataType(dataTypeStr):
    dictDataType = {"power":1, "current":2, "alarm":3, "temperature":4,
                    "SSPA volts":5, "volts dir":6, "volts rev":7,
                    "-8 volts":8
                    }
    return dictDataType[dataTypeStr]

def decodeAlarm(type):
    dictaAlarm={"temp":1, "vswr":2, "sum":3}

    return dictaAlarm[type]

'''
Numeración de Paneles 1 al 14
Panel 1 -> R01-C01
Panel 2 -> R02-C01
Panel 3 -> R03-C01
Panel 4 -> R04-C01
...
Panel 6 -> R06-C01
Panel 7 -> R07-C01
Panel 8 -> R01-C02
...
Panel 12 -> R05-C02
Panel 13 -> R06-C02
Panel 14 -> R07-C02
'''

def rc_to_aeu(row, col, n):
    pos_p = ((col-1)*7 +(row-1))*32
    pos_p = pos_p + n  # position from 1 to 448
    return pos_p

def aeu_to_rc(aeu):
    col = int(aeu//225) + 1
    if col == 2 :
        aeu = aeu - 224
    row = int(aeu//32) + 1
    n = aeu%32
    if n == 0:
        n = 32
        row -= 1
    return row, col, n
