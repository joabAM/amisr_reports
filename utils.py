from scipy.optimize import curve_fit
import numpy as np
import math

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

def aeu_to_panel(aeu):
    row, col, n = aeu_to_rc(aeu)
    panel = rc_to_panel(row, col)
    return panel, n

def rc_to_panel(row, col):
    panel = (col-1)*7 + row
    return panel

def panel_to_rc(panel):
    col = 0
    row = 0
    if panel > 14 or panel< 1:
        print("error invalid panel number")
        return
    if panel>7:
        row = panel-7
        col = 2
    else:
        row = panel
        col = 1
    return row, col


def parabolic(x, a, c):
	return a*np.sqrt(x) + c

def parabolic_dev(x,a,c):
    return (a/2)*(1/np.sqrt(x))

def get_rate(serie, func="parabolic", order=1):
    """
    func-> "parabolic", "polynomial"
    """
    data = serie
    med = len(data.index)/(2*60) #valor medio hrs
    y = data.values
    x = data.index
    if func == "polynomial":
        pol = np.polyfit(x, y, order)
        poly = np.poly1d(pol)
        data_fit = poly(x)
        vel = poly.deriv()  #velocidad
        rate = vel(med)
    else:
        f = eval(func)
        popt, pcov = curve_fit(f, x, y)
        data_fit = f(x,*popt)
        rate = (f(med,*popt) - f((med-1),*popt))

    #AEU/min
    r = rate* 60        # AEU/hrs
    #print(r)
    if math.isinf(r) or r < 0 or r==0:
        return (data_fit), 0
    r = 1/r             # hrs/AEU
    if r > 1000:
        r = 1000
    r = int(r*10)
    return (data_fit), r/10
