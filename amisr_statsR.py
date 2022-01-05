#!/usr/bin/env python3
'''
Created on pandemic :v

@author: Oper - Joab Apaza
'''
import datetime
import time
import os,glob,stat
import os.path
import bz2
import xml.etree.ElementTree as ET
import csv
import numpy as np
import paramiko
import smtplib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import math
from pytz import timezone
import matplotlib.ticker as plticker
from matplotlib.ticker import FuncFormatter
import aeustatus_sri as aeuST


################################################################################
read_xmls = False   #leer xmls y crear o añadir datos al archivo csv
plot_pow = True  #mostrar gráficos en base a los parámetros lineas abajo
'''
 online añade datos al archivo anterior segun se generen,
 en offline se busca en un rango de fechas y los acomoda
 en el archivo en caso de existir, sino crea uno
'''
# 1 = Potencia, 2 = Corriente
# 3 = alarmas, 4 = temperaturas
# 5 = SSPA volt,  6 = Voltajes dir,
# 7 = volt rev
DataType =1
#*****************
#para guardar y visualizar temperatura
temperatureType = 1 # 1 = temp SSPAs, 2 = temp CTRL
############################## GENERAL ###########################################
##################################################################################
online = 0 # True or False 1 o 0
startdate = '2021/05/05'  #formato yyyy/mm/dd para offline
enddate = '2021/11/21'   #para offline
hostname = '127.0.0.1 '
# mainpath = "/home/joab/Documents/XML_AMISR/"
# bz2path = "/home/joab/Documents/XML_AMISR/bz2dir/"
# username = 'joab'
# password = 'joab'
# xml_path = '/home/joab/Documents/XML_AMISR/xmls/'
username = 'soporte'
password = 'soporte'
xml_path = '/home/soporte/Documentos/XML_AMISR/xmls/'
mainpath = "/home/soporte/Documentos/XML_AMISR/"
bz2path = "/home/soporte/Documentos/XML_AMISR/bz2dir/"
pkey = 'pathkey' #añadir la llave al conectar al servidor, agregar esto en el código

###########################GRAFICOS######################################################
########################################################################################
'''
Los gráficos trabajan con datos anteriores, en caso Online, no toma el día actual
el formato es 'yyyy-mm-dd' no usar 03, 01 o similares, usar 3 o 1
'''
plot_format = '1' #1 plot equal date distance, fill no worked days, 2 plot only all points
#formato yyyy-mm-dd
#status_day = '2020-11-16' #descartado
#alarmas
status_range = [1,448] # ragno de aeu a visualizar 1 a 448
start_plot_date = '2021-08-15'
end_plot_date = '2021-10-20'
# 1 = mostrat, 0 = ocultar
show_plot = [0, 0, 0, 1] # grafico total, de panel, de aeu, n_pows, intervalos de potencia
#cada AEU en la lista [row, col, n#]
#row: 1 a 7, col: 1 a 2, n: 1 a 32
#[[1, 1, 21],[1, 1, 22],[1, 1, 23], [1, 1, 24],[1, 1, 25],[1, 1, 26],[1, 1, 27],[1, 1, 28],[1, 1, 29],[1, 1, 30]]
#aeus_plot_list = [[1, 1, 8],[1, 1, 12],[1, 1, 18],[1, 1, 20], [1, 1, 21],[1, 1, 32]]
aeus_plot_list = [[1, 1, 0],[1, 2, 20],[1, 2, 30]]
#aeus_plot_list = [[1, 1, 18],[1, 1, 22],[4, 1, 15],[1, 2, 29],[6, 2, 4],[7, 2, 30],[2, 1, 29],[3, 1, 4],[5, 1, 25],[6, 1,29 ]]
#aeus_plot_list = [[1,1,16],[1,2,4],[2,2,16],[2,2,24],[2,2,27],[7,2,25]]
aeus_plot_list = [[2,2,13],[2,2,20],[2,2,21],[2,2,24],[2,2,27]]#,[5,1,1],[5,1,11],[5,1,21],[5,1,31]]
aeus_plot_list = [[4,2,-1]]
aeus_plot_range =[1, 10] #rango de aeus, solo para funciona con -1
aeus_plot_range =[11,20]
aeus_plot_range =[21,32]

#cada panel en la lista [row, col]
#[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[7,1]
#[1,2],[2,2],[3,2],[4,2],[5,2],[6,2],[7,2]
panels_plot_list = [[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[7,1]]
#panels_plot_list = [[4,1],[3,2]]
panel_average = False    #muestra una gŕafica adicional con la potencia promedio de los paneles
show_plot_bar = True   #muestra barra de Gráficos en el último grafico
#plot_interval = '0.5'    # valores validos 0 0.1 0.5  1  2  6 12 24 horas
plot_interval = '1' #hours


plot_interval_panel_list = [[1, 2], [2, 2], [7,2], [7,1]] # al estar vacio se omiten los gráficos
plot_interval_panel_list = [[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[7,1]] #
plot_interval_panel_list = [[7,2]]
##############################################################################################################
################### VARIABLES del programa, no modificar######################################################
##############################################################################################################
aeuStatus = False
csvpathfile1 = mainpath +'dataPower.csv'
csvpathfile2 = mainpath +'dataCurrent.csv'
csvpathfile3 = mainpath +'dataAlarm.csv'
csvpathfile4_1 = mainpath +'dataTemperatureSSPA.csv'
csvpathfile4_2 = mainpath +'dataTemperatureCRTL.csv'
csvpathfile5 = mainpath +'dataSSPAvolts.csv'
csvpathfile6 = mainpath +'dataFWDvolts.csv'
csvpathfile7 = mainpath +'dataREVvolts.csv'
csvrepairfile = mainpath +'data_rep.csv.csv'
csvpathfile = ""
if DataType == 1:       #potencias
    csvpathfile = csvpathfile1
elif DataType == 2:     #Corrientes
    csvpathfile = csvpathfile2
    show_plot[3] = 0
elif DataType == 3:     # Alarmas
    csvpathfile = csvpathfile3
    aeuStatus = True
elif DataType == 4:     #Temperaturas
    if temperatureType == 1:
        csvpathfile = csvpathfile4_1
    if temperatureType == 2:
        csvpathfile = csvpathfile4_2
    show_plot[3] = 0
    panel_average = True #siempre mostrar promedios en temperatura x panel
elif DataType == 5:     # voltaje SSPA
    csvpathfile = csvpathfile5
    show_plot[3] = 0
    panel_average = True
elif DataType == 6:     # voltajes Dir
    csvpathfile = csvpathfile6
    show_plot[3] = 0
    panel_average = True
elif DataType == 7:     # voltajes Rev
    csvpathfile = csvpathfile7
    show_plot[3] = 0
    panel_average = True
else:
    csvpathfile = csvpathfile1
    DataType = 1

read_l_date = 0 #si ya se ha léido la ultima fecha o no
'''
En el caso de gráfico total y por panel se grafica las potencias, y la cantidad por niveles
de potencia son los intervalos siguientes
###plot_pow_list = "0", "0 a 100", "100 a 200", " 200 a 300", "300 a 400", "400 a 500", ">500","good", "bad"
'''
prom_day = 1  # 1 minuto, por cada xml, permite trabajar mejor ante fallas, y las alarmas no se pueden promediar

day = datetime.date.today()
today = day.strftime("%Y%m%d%H%M")
doyear = datetime.datetime.now().timetuple().tm_yday
year = day.year

pow_var=['good', 'numtx', 'bad', 'ugly', 'rf', 'peak', 'total', 'numrx']
last_day = None #ultima fecha en el archvo inicia en hoy por defecto
n_empty_files = 0
tot_xml = 0         # total de archivos validos en 1 día
aeu_plot_list = [] #lista de AEUs se almacenan en formato 1 a 448
panel_plot_list = []    #lista de paneles se almacenan en formato 1 a 14

#############################################################################################################
#############################################################################################################
def find_new_bz2(s_year, s_doy):

    ''' Agregar en el futuro paramiko para traer los archivos
     desde el servidor y dejar en la carpeta bz2dir'''

    source = xml_path+str(s_year)+'/'+str(s_doy).zfill(3)+'/'
    #print(source)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=hostname, port=22, username=username, password=password)
    sftp_client = client.open_sftp()

    for sftp_file in sftp_client.listdir(source):
        #print(sftp_file)
        sftp_client.get(source+sftp_file,  bz2path+sftp_file)
    sftp_client.close()

    #/224/20170812-165300-umet.xml.bz2

    #last file name

    listbz2 =  os.listdir(bz2path)      #read all files
    listbz2.sort()
    print("decompressing...",s_year,s_doy)
    for filebz2 in listbz2:
        if filebz2.endswith(".bz2"):
            decompress(bz2path + filebz2)
            os.remove(bz2path + filebz2)

def decompress(filepath):
    try:
        with bz2.BZ2File(filepath) as zipfile:
            data = zipfile.read() # get the decompressed data
            newfilepath = filepath[:-4] # assuming the filepath ends with .bz2
            xml = open(newfilepath, 'wb')
            xml.write(data)  # write a uncompressed file
            xml.close() #close the file
    except:
        print ("\nError on reading compressed file")
        pass

def check_aeu_status():

    '''
    Realiza un promedio diario con la penultima fecha, ya que la última podría corresponder
    al dia actual, si el promedio diario es cero, lo califica como averiado.
        Devuelve un string compuesto con los datos del módulo
    códigos de averías
    0 -> no reparado
    1 -> driver
    2 -> PA
    3 -> res 50
    4 -> desconocido
    '''
    status = ''

    with open(csvpathfile) as datafile:
        lines = csv.reader(datafile)
        lines = list(lines)
        last_line = lines[-1] #string
        final_date = datetime.datetime.strptime(last_line[0],"%Y-%m-%d").date()
        m = len(lines)
        i = 1
        idx = False
        acum = [0]*448
        S_prom = [0]*448
        k = 0
        while i < m :
            line = lines[-1*i]
            eval_date = datetime.datetime.strptime(line[0],"%Y-%m-%d").date()
            if eval_date < final_date: #Si cambia a un día menor
                if not idx:
                    final_date = eval_date
                    #print("f date",final_date)
                    idx = True
                else:
                    break
            if idx :
                k += 1
                for n in range(448):
                    #Suma la AEUs
                    acum[n] += float(line[10 + n])
            i += 1
        #print("acum: ", acum, k)
        #quitados 1, 4, 443
        list_aeu_except = [18,29,45,98, 110, 115,116,119, 123,124,133,160,180, 189,\
            194,204, 208,210,249,250, 257,277,307,322,329,338,343,349,352,389,405,415,418,\
            420,425,428,433,442]

        for aeu in range(448):
            S_prom[aeu] = acum[aeu]/k # PROMEDIO de penultimo día

            if S_prom[aeu] < 50: #esta a cero
                if not (aeu+1) in list_aeu_except:
                    print("\nFail detect in AEU #: ", aeu+1, ", power: ", S_prom[aeu])
                    #send_alert(0, ind)

    return status


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


def send_alert(typem,n):
    '''type 0 for AEU fail
        type 1 for total Power Alert
    '''
    dest_mail = 'joab.apaza@gmail.com'
    if typem:    #mensaje alerta en caída de potencia o % de AEUs
        message = 'Drop in AMISR Power, transmiting with '+ str(n/1000)+ ' KWatts or '+ str(n/224000) + '%\ of eficiency'
    else:
        ant = ''
        ant = check_aeu_status(n) #ver los registros del módulo
        r,c,num = aeu_to_rc(n)
        message = 'Failure in AEU #: '+ str(num)+ '  from R'+str(r)+'-C'+str(c)+'\n'+ant


    subject = 'AMISR ALERT'
    message = 'Subject: {}\n\n{}'.format(subject, message)

    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    print("Sending alert to ", dest_mail)
    server.login('roj-op01@igp.gob.pe','joab48401863')
    server.sendmail('roj-op01@igp.gob.pe', dest_mail, message)
    server.quit()
    pass


def update_data(_AEU, _date,_time, _pow_panel, _npow, amperes, volsSSPA, alarms, temSSPA, tempCTRL,dirVolt,revVolts):
    '''
        Escribe en el csv solo si no existe el día, caso contrario lo omite
        data: 'date' 'time' 'good', 'numtx', 'bad', 'ugly', 'rf', 'peak', 'total', 'numrx',AEU[1], AEU[2]..
        ... AEU[448], npow[],amp[1:448], volts[1:448], alarms[1:448], temSS[1:448], tempCT[1:448]
        visto como 1 hasta 14 el número de paneles, la columna 2 completan del 8 al 14
    '''
    global read_l_date, last_day
    last_row = []
    #old_csv_d  ata = []

    if os.path.isfile(csvpathfile):
        modecsv = 'a'
        #print("l_date",read_l_date)
        if read_l_date == 0:
            print("reading last date...")
            with open(csvpathfile, 'r') as file_reader:
                f_reader = csv.reader(file_reader)
                for row in f_reader:
                    last_row = row
                last_day = datetime.datetime.strptime(last_row[0]+" "+last_row[1],"%Y-%m-%d %H:%M:%S")
            read_l_date = 1
    else:
        modecsv = 'w'


    with open(csvpathfile,modecsv) as csvfile:
        file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        #if online:
        #    file = csv.reader(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        #print(AEU)
        # ind = 1
        # #numero de modulos que se sabe no transmiten y no se puede reparar: (se quito 4 y 180)
        # list_aeu_except = [18,45,115,116,123,124,133,160,189,194,208,210,232,249,257,322,329,338,352,389,415,420,433,443]
        #
        #
        #
        # for aeu in AEU:
        #     if int(aeu) < 100 and modecsv=='a':#ie equal to 100 in day promed
        #         #print(ind)
        #         if not ind in list_aeu_except:
        #             print("\nFail detect in AEU #: ", ind)
        #             #print(check_aeu_status(ind))
        #             send_alert(0, ind)
        #
        #         # if aeu_stat[0]:
        #         #
        #     ind += 1

        #file.writerow(['date',pow_var[0],pow_var[1],pow_var[2], pow_var[3], pow_var[4], pow_var[5], pow_var[6], pow_var[7]])
        act_day = datetime.datetime.strptime(_date +" "+ _time,"%Y-%m-%d %H:%M:%S")
        s_pow = []
        for n in _npow:
            for x in n:
                s_pow.append(x)

        if DataType == 1:
            data = [_date, _time] + _pow_panel + _AEU + s_pow
        elif DataType == 2:
            data = [_date, _time] +  amperes
        elif DataType == 3:
            data = [_date, _time] +  alarms
        elif DataType == 4:
            if temperatureType == 1:
                data = [_date, _time] + temSSPA
            elif temperatureType == 2:
                data = [_date, _time] + tempCTRL
            else:
                print("ERROR invalid temperatureType")
                return
        elif DataType == 5:
            data = [_date, _time] + volsSSPA
        elif DataType == 6:
            data = [_date, _time] + dirVolt
        elif DataType == 7:
            data = [_date, _time] + revVolts

        if online == 0 and modecsv=='a' and read_l_date == 1:
            if act_day > last_day :
                print("writing csv... Date: ", act_day)
                #print(data)
                file.writerow(data)
            else:
                print("The data in these files has already been processed.")
        else:
            file.writerow(data)

# def plot_aeu(N):            #descartado, funcion obsoleta
#     dates=[]
#     power=[]
#     if os.path.isfile(csvpathfile1):
#         with open(csvpathfile1) as fr:
#             reader = csv.reader(fr)
#             for row in reader:
#                 #dates.append(datetime.datetime.strptime(row[0],"%Y-%m-%d").date())
#                 dates.append(row[0])
#                 power.append(float(row[9+ (N -1)]))
#
#         print("\nPlotting AEU ",N)
#         plt.plot_date(dates,power,linestyle='-')
#     else:
#         print("No previous data to plot")
#     return



def plot_radar():
    global aeu_plot_list
    global panel_plot_list
    global plot_interval_panel_list
    global show_plot
    global aeus_plot_range
    show_all_panel = []  #número panel
    valid_interval = [0, 0.1, 0.5, 1, 2, 6, 12, 24] #el doble de lo ingresado
    interval = float(plot_interval)  #
    if not(interval in valid_interval):
        print("Invalid time interval for plot, use 0, '0.1', '0.5', '1', '2', '6', '12' or '24' hours")
        return
    interval *=60 # ahora interval en minutos interval = 2*15*plot_interval
    if interval == 0:
        interval = 1
    print("data Prom: {:2d} min".format(int(interval)))
    YmaxT = 0
    YmaxP = 0
    YmaxAEU = 0
    if DataType == 1:
        startIndex = 10
        TitleLabel = "Power"
        unitLabel = "kW"
        YmaxT = 235.2
        YmaxP = 16.8
        YmaxAEU = 750
    elif DataType == 2:
        startIndex = 2
        TitleLabel = "Current"
        unitLabel = "A"
        YmaxT = 1500
        YmaxP = 150
        YmaxAEU = 5
    elif DataType == 3:
        TitleLabel = "Alarms"
        show_plot = [0,0,0,0]
        startIndex = 2
    elif DataType == 4:
        if temperatureType == 1:#temp SSPAs
            TitleLabel = "Temperature SSPA"
        elif temperatureType == 2:      #temp CTRL
            TitleLabel = "Temperature CTRL"
        unitLabel = "°C"
        startIndex = 2
        YmaxT = 65
        YmaxP = 65
        YmaxAEU = 65
    elif DataType == 5:
        TitleLabel = "Volts SSPA"
        unitLabel = "V"
        YmaxT = 40
        YmaxP = 40
        YmaxAEU = 40
        startIndex = 2
    elif DataType == 6:
        startIndex = 2          #
        TitleLabel = "Volts FWD"
        YmaxT = 3
        YmaxP = 3
        YmaxAEU = 3
        unitLabel = "V"

    elif DataType == 7:
        startIndex = 2
        TitleLabel = "Volts REV"
        YmaxT = 3
        YmaxP = 3
        YmaxAEU = 3
        unitLabel = "V"
    else :
        print("ERROR, no Power or Current plot select")
        return

    datelist = []
    csvData = []
    day_lines = []
    x = []
    y_p_total = []      #potencia de la suma de todas las
    y_p_total_xml = []

    plot_pow_list = [] #lista de paneles, para mostrar intervalos de potencia

    s_date = ''
    e_date = ''
    #Cambiar los datos de las AEUS a una solo lista
    #verificar el rango
    for r,c,n in aeus_plot_list:
        if r > 7 or r < 1:
            print("Invalid value to row number /aeu_list")
            return
        if c > 2 or c < 1:
            print("Invalid value to colum number /aeu_list")
            return

        if n > 32 or n < -1:
            print("Invalid value to AEU number /aeu_list")
            return

        if n == 0:      ###plot all panel
            for i in range(32):
                aeu_plot_list.append(rc_to_aeu(r,c,(i+1)))
            show_all_panel.append([r,c])
            aeus_plot_range = [1,32]
        elif n == -1:      ###plot block panel
            for i in range(aeus_plot_range[0],aeus_plot_range[1]+1):
                aeu_plot_list.append(rc_to_aeu(r,c,i))
            show_all_panel.append([r,c])
        else:
            aeu_plot_list.append(rc_to_aeu(r,c,n))
    #print(aeu_plot_list)
    #cambiar y verificar la lista de entrada para
    #graficar paneles
    for r,c in panels_plot_list:
        if r > 7 or r < 1:
            print("Invalid value to row number /panel_list")
            return
        if c > 2 or c < 1:
            print("Invalid value to colum number /panel_list")
            return
        panel_plot_list.append(rc_to_aeu(r,c,32)/32)


    for r,c in plot_interval_panel_list:
        if r > 7 or r < 1:
            print("Invalid value to row number /interval_panel_list")
            return
        if c > 2 or c < 1:
            print("Invalid value to colum number /interval_panel_list")
            return
        plot_pow_list.append(int(rc_to_aeu(r,c,32)/32))

    y_panel = [[] for i in range(len(panel_plot_list))]
    y_aeu = [[] for i in range(len(aeu_plot_list))]
    y_nInt = [[] for i in range(9)] # 9 = intervals(7)+ good + bad
    y_nInt_panel = [[[] for i in range(7)] for k in range(14)]
    aeu_alarms = [[] for i in range(448)]
    alarm_date = []
    if os.path.isfile(csvpathfile):
        with open(csvpathfile) as csvFile:
            lines = csv.reader(csvFile)
            lines = list(lines)
            startdate_csv = lines[0][0]
            enddate_csv = lines[-1][0]

            if start_plot_date < startdate_csv and end_plot_date > enddate_csv:
                print("Changing dates to valid data: ")
                s_date = startdate_csv
                e_date = enddate_csv
            elif start_plot_date < startdate_csv and end_plot_date < enddate_csv:
                print("Changing dates to valid data: ")
                s_date = startdate_csv
                e_date = end_plot_date
            elif start_plot_date > startdate_csv and end_plot_date > enddate_csv:
                print("Changing dates to valid data: ")
                s_date = start_plot_date
                e_date = enddate_csv
            else:
                s_date = start_plot_date
                e_date = end_plot_date

            print(s_date, e_date)
            s_date = datetime.datetime.strptime(s_date,"%Y-%m-%d").date()
            e_date = datetime.datetime.strptime(e_date,"%Y-%m-%d").date() + datetime.timedelta(days=1)
            day_date = s_date
            flag_remnantData = False
            #plot_status_day =  datetime.datetime.strptime(status_day,"%Y-%m-%d").date()
            #print("last date", lines[-1][0])
            # end_date = datetime.datetime.strptime(lines[-1][0]+lines[-1][1],"%Y-%m-%d%H:%M:%S")
            index_line = 1   #  Nro de linea
            valid_lines = 0
            M = 0
            #print("tot lines",len(lines))
            for line in lines:          #cada línea de la lista son muestras cada 1 min
                date = datetime.datetime.strptime(line[0]+line[1],"%Y-%m-%d%H:%M:%S")

                if index_line == len(lines) and len(day_lines)>1 :
                    flag_remnantData = True
                if (date.date() >= s_date and date.date() <= e_date) or flag_remnantData:       #Rango de fechas validos
                    #print(index_line)
                    #-----------------------------------------------------------------------------------------
                    ## if index_line == 0:              #índice de línea
                    ##     date = datetime.datetime.strptime(line[0]+line[1],"%Y-%m-%d%H:%M:%S")
                    ## datelist.append(line[0])
                    new_date = date.date()
                    if new_date > day_date or index_line == len(lines): #hasta aquí se tiene una lista de todo 1 día

                        #print(new_date)
                        k = 0
                        S_acum_1 = 0  #suma de AEUs
                        S_acum_2 = 0  #potencia pico xml
                        S_p_acum = [0]*len(panel_plot_list)
                        S_aeu_acum = [0]*len(aeu_plot_list)
                        S_n_acum = [0]*9
                        S_n_acum_panel = [[0 for x in range(7)] for n in range(14)]
                        #print("daylines", len(day_lines))

                        for _l in day_lines:    #todas las lineas del día
                            k += 1
                            #*********************************************************************************
                            if show_plot[0] == 1: # potencia total
                                S = sum(float(j) for j in _l[startIndex:(startIndex+448)])#Suma todas las AEUs
                                S_acum_1 += S
                                S_acum_2 += float(_l[7])
                            #*********************************************************************************
                            if show_plot[1] == 1: # potencia panel
                                #N_panel  del 1 al 14
                                m = 0
                                for pl in panel_plot_list:
                                    init_panel = startIndex + (int(pl)-1)*32
                                    end_panel =  startIndex + int(pl)*32
                                    S = sum(float(j) for j in _l[init_panel:end_panel]) #suma de panel
                                    #S = sum(float(j) for j in _l[init_panel:end_panel])/32 #promedio de panel
                                    S_p_acum[m] += S
                                    m += 1
                            #*********************************************************************************
                            if show_plot[2] == 1: # potencia aeu
                                m = 0
                                #print(aeu_plot_list)
                                for nAeu in aeu_plot_list:
                                    #print(_l[startIndex + int(nAeu)-1])
                                    S = float(_l[startIndex + int(nAeu)-1]) #Suma la AEUs
                                    S_aeu_acum[m] += S
                                    m += 1
                            #*********************************************************************************
                            if show_plot[3] == 1: # potencia stat [458]
                                i = 7
                                i_0 = 458
                                for l in range(14):#para cada panel
                                    nt = _l[i_0:i_0+i] #avanza de 7 en 7
                                    i_0 = i_0 + 7 #nuevo inicio
                                    m = 0
                                    for q in nt:
                                        S = float(q)
                                        S_n_acum_panel[l][m] += S
                                        S_n_acum[m] += S
                                        m += 1
                                        M += S
                                S_n_acum[7] += float(_l[2])    #good
                                S_n_acum[8] += float(_l[4])    #bad
                                #print("total: ", sum(S_n_acum))

                            #*********************************************************************************
                            ###if aeuStatus and (new_date == plot_status_day) : #para 1 solo día
                            if aeuStatus:
                                i = 0
                                for v in _l[startIndex:(startIndex+448)+1]:  #.split(","):
                                    #print(aeu_alarms)
                                    aeu_alarms[i].append(v)
                                    i += 1
                                alarm_date.append(datetime.datetime.strptime(_l[0]+'_'+_l[1][:5],"%Y-%m-%d_%H:%M"))

                            #*********************************************************************************
                            #*********************************************************************************
                            #*********************************************************************************
                            #******************************* WRITE AND RESET**********************************
                            if k == interval:
                                #********act Pot total
                                q =datetime.datetime.strptime(_l[0]+'_'+_l[1][:5],"%Y-%m-%d_%H:%M")
                                x.append(q)
                                #print(k, q)
                                y_p_total.append(S_acum_1/interval)
                                y_p_total_xml.append(S_acum_2/interval)

                                for n in range(len(panel_plot_list)):
                                    y_panel[n].append(S_p_acum[n]/interval)


                                for n in range(len(aeu_plot_list)):
                                    y_aeu[n].append(S_aeu_acum[n]/interval)

                                for n in range(9):
                                    y_nInt[n].append(S_n_acum[n]/interval)

                                for p in range(14):#para cada panel
                                    for n in range(7):
                                        y_nInt_panel[p][n].append(S_n_acum_panel[p][n]/interval)
                                k = 0
                                S_acum_1 = 0
                                S_acum_2 = 0
                                S_p_acum = [0]*len(panel_plot_list)
                                S_aeu_acum = [0]*len(aeu_plot_list)
                                S_n_acum = [0]*9
                                S_n_acum_panel = [[0 for x in range(7)] for n in range(14)]

                        if k != 0: #en caso se termine los datos sin completar el nro requerido para promediar
                            x.append(datetime.datetime.strptime(_l[0]+'_'+_l[1][:5],"%Y-%m-%d_%H:%M"))

                            y_p_total.append(S_acum_1/k)
                            y_p_total_xml.append(S_acum_2/k)

                            for n in range(len(panel_plot_list)):
                                y_panel[n].append(S_p_acum[n]/k)

                            for n in range(len(aeu_plot_list)):
                                y_aeu[n].append(S_aeu_acum[n]/k)

                            for n in range(9):
                                y_nInt[n].append(S_n_acum[n]/k)

                            for p in range(14):#para cada panel
                                for n in range(7):
                                    y_nInt_panel[p][n].append(S_n_acum_panel[p][n]/k)


                        #reinicia las variables para leer otro día

                        day_lines = []
                        day_date = new_date
                        #NO olvidar quitar la siguiente linea fuera del bucle:
                        day_lines.append(line) #la primera linea del nuevo día
                        flag_remnantData = False
                    else:
                        day_lines.append(line)  #acumulamos las listas del mismo día
                        #print("->",new_date)
                        pass
                    valid_lines += 1

                index_line += 1


        titles = ["AMISR Total "+TitleLabel, "Panel "+TitleLabel, "AEU "+TitleLabel, "AEUs / Power Intervals", "Panel Average "+TitleLabel]


        x = [n.replace(tzinfo=timezone('UTC')) - datetime.timedelta(hours=5) for n in x]   #to localTime
        x_dates = x
        #print(len(x))
        x_label = [n.strftime("%Y/%m/%d, %H:%M:%S") for n in x]
        #print(x)
        x_g = []
        x_labels = x_label
        # if plot_format == '2':
        #     for n in range(0,len(x)):
        #         if (n % spacing)!=0:
        #             x_labels[n]=" "
        #     x_g = range(len(x_label))
        x = mdates.date2num(x)

        numrows, numcols = len(x), len(y_p_total)
        names = np.array(list(x_label))

        def fmt(x, y):
            #print(len(x_label))
            #print(x_label)
            try:
                z = x_label[int(x)]
            except:
                z = "---"
            return z

        #*******************************************************************++*
        #*************

        #********************************* TOTAL ******************************************
        if show_plot[0] == 1:
            factor = 1
            fig1, ax = plt.subplots()
            ax_2 = ax.twinx()

            if DataType == 1:
                y_t = [x/1000 for x in y_p_total]
                y_t_xml = [x/1000 for x in y_p_total_xml]# kilo Watts
            elif DataType == 2:
                y_t =  y_p_total
            if DataType == 4 or DataType == 5 or DataType == 6:
                y_t = [x/448 for x in y_p_total] #valores promedio(estimado)

            print(y_t)
            if plot_format == '1':
                line, = ax.plot_date(x, y_t, fmt = '', drawstyle='default', linestyle='-'
                                                ,label = 'Radar '+TitleLabel+' (AEUs)')
                #ax.callbacks.connect('xlim_changed', on_xlims_change(ax,line))
                if DataType == 1: #solo potencia
                    ax.plot_date(x,y_t_xml,fmt = '', linestyle='-',label = 'peak '
                                                                +TitleLabel+' (xml)')


            elif plot_format == '2':

                ax.plot(y_t,label = 'Radar '+TitleLabel+' (AEUs)')

                if DataType == 1: #solo potencia
                    ax.plot(y_t_xml,label = 'peak '+TitleLabel+' (xml)')

            else:
                print("Error, plot_format invalid value...")


            plt.gca().format_coord = fmt
            #print(x,y_t)
            ax.set_xlabel('dates')
            ax.set_ylabel(TitleLabel+' ('+unitLabel+')')
            if DataType == 1:
                ax_2.set_ylabel('percent (%)')
                ax.axhline(y=224, color='r', linestyle='--',label = 'ideal')
            ax.set_ylim(0, YmaxT) #igual a 105%
            #ax_2.set_ylim(0, 105)
            ax.legend(bbox_to_anchor=(-0.02,0.2), loc="upper right", fontsize = "x-small", title = "legend")
            ax.minorticks_on()
            ax.grid()
            ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black')
            plt.title(titles[0], fontsize=16)
            #print(labels)
            plt.setp(ax.get_xticklabels(), rotation=40, ha='right')


        #**************************************PANEL*************************************
        if show_plot[1] == 1 :
            panel_label_list = ["R0"+str(k[0])+"-C"+str(k[1])  for k in panels_plot_list]
            if  DataType==1 or DataType==2: #Solo en potencia y corriente interesa el total
                fig2, ax = plt.subplots()
                ax2 = ax.twinx()
                #fig2 =  plt.figure(nf)
                l = 0
                for y in y_panel:
                    if  DataType==1 :
                        y_k = [k/ 1000 for k in y]     # kilo Watts
                    else:
                        y_k = y
                    if plot_format == '1':
                        ax.plot_date(x,y_k,fmt = '',linestyle='-',label = panel_label_list[l])
                    elif plot_format == '2':
                        ax.plot(y_k,label = panel_label_list[l])
                    else:
                        print("Error, plot_format invalid value...")
                    l += 1
                if  DataType==1 :
                    ax2.set_ylabel('percent (%)')
                    ax2.set_ylim(0,105)
                    ax.axhline(y=16, color='r', linestyle='--',label = 'ideal')
                plt.gca().format_coord = fmt
                ax.set_xlabel('dates')
                ax.set_ylabel(TitleLabel+'('+unitLabel+')')
                ax.set_ylim(0, YmaxP)# 16.8 = 105%
                ax.legend(bbox_to_anchor=(-0.06,1), loc="upper right", fontsize = "x-small", title = "legend")
                ax.grid()
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black')
                plt.title(titles[1], fontsize=16)




                plt.setp(ax.get_xticklabels(), rotation=30, ha='right')

            if panel_average: # grafica para la potencia promedio, amperaje, y solo Temperatura
                fig2_a, ax_a = plt.subplots()
                ax2_a = ax_a.twinx()
                if DataType ==1:
                    ax2_a.set_ylabel('percent (%)')
                    ax2_a.set_ylim(0,106)
                l = 0

                for y in y_panel:
                    y_prom = [ k/32 for k in y]
                    if plot_format == '1':
                        ax_a.plot_date(x,y_prom,fmt = '',linestyle='-',label = panel_label_list[l])
                    elif plot_format == '2':
                        ax_a.plot(y_prom,label = panel_label_list[l])
                    else:
                        print("Error, plot_format invalid value...")
                    l += 1

                if DataType == 1:
                    ax_a.axhline(y=500, color='r', linestyle='--',label = 'ideal')
                ax_a.set_xlabel('dates')
                ax_a.set_ylabel(TitleLabel+'('+unitLabel+')')
                plt.gca().format_coord = fmt
                ax_a.set_ylim(0, YmaxP)
                ax_a.legend(bbox_to_anchor=(-0.06,1), loc="upper right", fontsize = "x-small", title = "legend")
                ax_a.grid()
                ax_a.grid(which='minor', linestyle=':', linewidth='0.5', color='black')
                plt.title(titles[4], fontsize=16)
                plt.setp(ax_a.get_xticklabels(), rotation=30, ha='right')

        #**************************************AEU*************************************
        if show_plot[2] == 1:
            aeu_label_list = []
            for k in aeus_plot_list:
                r = k[0]
                c = k[1]
                n = k[2]

                if len(show_all_panel) > 0:

                    for R,C in show_all_panel:
                        if r == R and c == C:
                            for i in range(aeus_plot_range[0], aeus_plot_range[1]+1):
                                aeu_label_list.append("R0"+str(r)+"-C"+str(c)+" #"+str(i))
                        else:
                            aeu_label_list.append("R0"+str(r)+"-C"+str(c)+" #"+str(n))
                else:
                    aeu_label_list.append("R0"+str(r)+"-C"+str(c)+" #"+str(n))
            #print(aeu_label_list)
            fig2 =  plt.figure()
            l = 0
            arrayToPd = []
            for y in y_aeu:

                plt.plot_date(x,y,fmt = ' ',linestyle='-',label = aeu_label_list[l])
                l += 1

            if DataType == 1:
                plt.axhline(y=500, color='r', linestyle='--',label = 'ideal')
            plt.xlabel('dates')
            plt.xticks(rotation=30)
            plt.minorticks_on()
            plt.grid(which='minor', color='#444444', linestyle='-', alpha=0.2)
            plt.title(titles[2], fontsize=16)
            plt.ylim(0, YmaxAEU)
            plt.ylabel(TitleLabel+ '('+unitLabel+')')
            plt.legend(bbox_to_anchor=(-0.06,1), loc="upper right", fontsize = "x-small", title = "legend")

        #**************************************INTERVAL POWER*************************************
        if show_plot[3] == 1:
            label_list = ["0", "0 to 100", "100 to 200", " 200 to 300", "300 to 400", "400 to 500", ">500","Good","Bad"]
            fig4, ax1 = plt.subplots(2,1)
            ax2 = ax1[0].twinx()
            print(y_nInt[0])
            l = 0
            for y in y_nInt:
                line, = ax1[0].plot_date(x,y,fmt = '',linestyle='-',label = label_list[l], picker=True)
                l += 1
            ax1[0].set_xlabel('date')

            if show_plot_bar:
                cid = fig4.canvas.mpl_connect('button_press_event',  lambda event: on_click(event, fig4, ax1, x, y_nInt))
            else:
                ax1[1].set_visible(False)
                ax1[0].change_geometry(1,1,1)
            ax1[0].set_ylabel('Number of AEUs')
            ax2.set_ylabel('percent (%)')

            ax1[0].set_ylim(0, 470.4) #igual a 105%
            ax2.set_ylim(0, 105)
            ax1[0].legend(bbox_to_anchor=(-0.06,1), loc="upper right", fontsize = "x-small", title = "legend")
            ax1[0].grid()
            ax1[0].grid(which='minor', linestyle=':', linewidth='0.5', color='black')
            ax2.grid()
            ax2.grid(which='minor', linestyle=':', linewidth='0.5', color='black')
            plt.title(titles[3], fontsize=16)
            plt.setp(ax1[0].get_xticklabels(), rotation=30, ha='right')

            n_plots_i = len(plot_pow_list)

            i_j = 0
            l_colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
            for panel in plot_pow_list:
                y_u = y_nInt_panel[panel-1]
                print("Power 0: ",panel, y_u[0])
                l = 0
                rf, cf = plot_interval_panel_list[i_j]
                # # s = sum( n[0] for n in y_u)
                # # print("suma:", s)     #acumulado de 32 por panel
                # print(s,t)
                plt.figure()
                for y in y_u: #cada nivel de potencia
                    line, = plt.plot_date(x,y,fmt = '',color=l_colors[l],linestyle='-',label = label_list[l])
                    l += 1
                plt.legend(bbox_to_anchor=(-0.05,1), loc="upper right", fontsize = "x-small", title = "legend")
                plt.grid()
                plt.ylabel('# AEUs')
                plt.title('AEUs per power Interval Panel R'+ str(rf)+"-C"+str(cf))
                plt.xticks(rotation=60)
                i_j += 1
        #**************************************STATUS DAYs (ALARMAS)*************************************
        ## para cada valor de alarma se asigna un colorbar
        ## 0= OK, 1 = TEMP, 2= VSWR, 3 = SUMMARY ()
        if aeuStatus:
            #print(alarm_date)
            alarm_date = [n.replace(tzinfo=timezone('UTC'))- datetime.timedelta(hours=5) for n in alarm_date]   #to localTime
            alarm_date_label = [n.strftime("%Y/%m/%d, %H:%M:%S") for n in alarm_date]

            minAEU = status_range[0]
            maxAEU = status_range[1]
            aeuRange = maxAEU - minAEU
            aeu_alarms = aeu_alarms[minAEU-1:maxAEU][:]
            data_status = np.zeros((len(aeu_alarms),len(aeu_alarms[0])))

            n = 0
            for k in aeu_alarms:
                data_status[n] = np.array(k)
                n += 1

            fig_s, ax = plt.subplots()
            img = ax.imshow(data_status,aspect='auto', interpolation='none', cmap='jet',vmin=0, vmax=3)

            cbar = fig_s.colorbar(img, ticks=[0, 1, 2, 3])
            cbar.ax.set_yticklabels(['OK', 'TEMP', 'VSWR','SUMM'])  # vertically oriented colorbar

            ylabel_aeu = ["R0%d-C%d %02d"%(aeu_to_rc(n)) for n in range(status_range[0],status_range[1]+1)]
            plt.xticks(np.arange(1,len(aeu_alarms[0])+1, dtype=np.int),alarm_date_label,rotation=30)
            plt.yticks(np.arange(0,(maxAEU-minAEU)+1, dtype=np.int),ylabel_aeu)
            plt.autoscale(enable=True, axis='x', tight=False)



        plt.show()

    else:
        print("There is no data to plot")

def on_xlims_change(event_ax,line):
    #print("updated xlims: ", event_ax, line)
    x,y = line.get_data(orig=False)
    fit = np.polyfit(x, y, 10)
    pf = np.poly1d(fit)
    event_ax.plot(x, pf(x), 'r')

def on_click(event, fig, ax, xdate, yint):
    try:
        label= ["0", "0 to 100", "100 to 200", " 200 to 300", "300 to 400", "400 to 500", ">500"]
        ax[1].clear()
        # print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
        #       ('double' if event.dblclick else 'single', event.button,
        #        event.x, event.y, event.xdata, event.ydata))
        #print(event.xdata)
        x_date = mdates.num2date(event.xdata)
        dates  = mdates.num2date(xdate)
        i = 0
        #y = [yint[k][560] for k in range(7)]
        #print(xdate)
        while x_date.date() > dates[i].date(): #compara la fecha seleccionada desde la mínima
            i += 1
            #print(i)
        y = [yint[k][i] for k in range(7)] #extrae los datos para la fecha del "i"
        print(label)
        print(y)
        ax[1].bar(label,y)
        ax[1].set_xlabel(x_date.strftime("%Y-%m-%d"))
        ax[1].grid()
        ax1[1].grid()
        ax1[1].grid(which='minor', linestyle=':', linewidth='0.5', color='black')
        plt.draw()
        plt.show()
    except:
        return


    #print(xdate)


def read_xml():
    '''Lee los xmls, filtra los archivos con datos validos, ademas de poder sacar un
        promedio mínimo de 30 minutos. Añade el conteo de intervalos de potencia
        100 a 200, 200 a 300, etc
    '''
    readStatus = aeuST.AEUStatus()
    global tot_xml,n_empty_files
    xml_list = os.listdir(bz2path)
    #xml_list = glob.glob('*.xml')
    filepath = xml_list
    #print(xml_list)
    '''
    xml file name = 20140822-000000-umet.xml, date + time + umet+ext
    '''
    #print(xml_list, ":.........................")
    xml_list.sort(key=lambda date: datetime.datetime.strptime(date, "%Y%m%d-%H%M%S-umet.xml"))
    #print(xml_list, "#####################3")
    AEU = [0] * 448 # 448 = 32 x 14
    pow_panel = [0]*8   #datos de pie de xml
    #n_pows = [0]*7      #intervalos de potencia
    count_xml = 0      # contador a 30 min
    Amperes =  [0.0] * 448 #almacena datos del corriente
    SSPA_Volts = [0.0] * 448 #almacena el voltaje de SSPA
    DIR_Volts = [0.0] * 448 #almacena el voltaje directo
    REV_Volts = [0.0] * 448 #almacena el voltaje reverso
    Alarms  = [0] * 448  # almacena las alarmas en formato decimal
    SSPA_temp  = [0.0] * 448
    Contr_temp  = [0.0] * 448
    n_pows = [[0 for i in range(7)] for n in  range(14)]
    #date_toWrite = None
    #time_toWrite = None
    #print("lista", xml_list)
    for i in range(len(xml_list)):
        filepath =  bz2path + xml_list[i]
        tree=ET.parse(filepath)
        root=tree.getroot()
        date_time = root.get('timestamp')
        date_ = date_time[:10]
        time_=date_time[11:19]  #"2014-09-02 00:06:00.011163+00:00"
        #print(time[3:5])
        panel = root.find('panel')
        power = root.find('power').attrib
        tot_xml = tot_xml + 1
        #print("power: ",power)
        nAeusTx = (448/2 +1) #mas de la mitad transmitiendo para considerarlo útil
	    #hay casos que se transmite con medio arreglo o solo 1 panel, eso para pruebas
        if panel != None and int(power.get('numtx')) > nAeusTx : # and power.get('rf')==1:
            #print(date_time, power)
            count_xml = count_xml + 1
            time_toWrite = time_
            date_toWrite = date_
            #print("count", count_xml)
            #panel              "panel-R06-C01.umet"
            for panel in root.iter('panel'):
                panelID = panel.get('id')
                row = int(panelID[7:9])
                col = int(panelID[11:13])
                #print(row, col)
                for aeu in panel.iter('aeu'):
                    #print("HEXA CODE",aeu.text)
                    hexa_data = aeu.text #pasa los datos hexa
                    pos_aeu = int(rc_to_aeu(row, col,int(aeu.get('position')))-1) #posicion de la AEU leida
                    if hexa_data != None :
                        readStatus.update(hexa_data)
                    else:
                        readStatus.reset()
                    Amperes[pos_aeu]    = round(readStatus.sspa_current_monitor,2)
                    SSPA_Volts[pos_aeu] = round(readStatus.sspa_voltage_monitor,2)
                    Alarms[pos_aeu]     = int(readStatus.alarm_state)
                    SSPA_temp[pos_aeu]  = round(readStatus.sspa_temp,1)
                    Contr_temp[pos_aeu] = round(readStatus.controller_temp,1)
                    DIR_Volts[pos_aeu]  = round(readStatus.signal_voltage[0],1)
                    REV_Volts[pos_aeu]  = round(readStatus.signal_voltage[1],1)
                    #print(Amperes)
                    pwatts = int(float((aeu.get('pwatts'))))
                    AEU[pos_aeu] = pwatts #acumula datos de AEUs

                    n_panel = int(rc_to_aeu(row,col,32)/32)-1
                    if pwatts == 0: n_pows[n_panel][0] +=1
                    elif pwatts <=100: n_pows[n_panel][1]+=1
                    elif pwatts <=200: n_pows[n_panel][2]+=1
                    elif pwatts <=300: n_pows[n_panel][3]+=1
                    elif pwatts <=400: n_pows[n_panel][4]+=1
                    elif pwatts <=500: n_pows[n_panel][5]+=1
                    elif pwatts >500: n_pows[n_panel][6]+=1
            j = 0
            for var in pow_var:
                pow_panel[j]+=int(power.get(var)) #Acumula datos de Potencia
                #print(var,pow_panel[j])
                j = j + 1
        else:
            #print("No data in xml file...")
            n_empty_files = n_empty_files + 1


        if count_xml > (prom_day-1):
            pow_panel = [float(x/count_xml) for x in pow_panel] #datos cada 1 min totales por panel
            AEU[:] = [float(x/count_xml) for x in AEU] # datos  cada 1 min x aeu
            _n_pows = n_pows
            m = 0
            for panel in n_pows:
                _n_pows[m] = [float(x/count_xml) for x in panel] # proemdio de n tx
                m += 1
            #update_data(AEU, date_,time_, pow_panel, _n_pows)
            update_data(AEU, date_toWrite,time_toWrite, pow_panel, _n_pows, Amperes
                                            ,SSPA_Volts,Alarms,SSPA_temp,Contr_temp,DIR_Volts,REV_Volts)
            AEU = [0] * 448   # reinicio
            pow_panel = [0]*8   # reinicio
            n_pows = [[0 for i in range(7)] for n in  range(14)]      #reinicio
            count_xml = 0
            Amperes =  [0.0] * 448
            Alarms  = [0.0] * 448
            SSPA_temp  = [0.0] * 448
            Contr_temp  = [0.0] * 448
            SSPA_Volts = [0.0] * 448 #almacena el voltaje de SSPA
            DIR_Volts = [0.0] * 448 #almacena el voltaje directo
            REV_Volts = [0.0] * 448 #almacena el voltaje reverso
            #print("xml day", xml_list[i])


        os.remove(bz2path + xml_list[i])        #elimina el xml una vez leído


    if tot_xml >0 and count_xml > 0:
        pow_panel = [float(x/count_xml) for x in pow_panel] #si no completa los 30 minutos
        AEU[:] = [float(x/count_xml) for x in AEU]
        ##n_pows = [float(x/count_xml) for x in n_pows] # proemdio de n tx
        n_pows = [[float(x/count_xml) for x in n] for n in n_pows]
        #update_data(AEU, date_,time_, pow_panel, n_pows)
        update_data(AEU, date_toWrite,time_toWrite, pow_panel, _n_pows, Amperes
                                        ,SSPA_Volts,Alarms,SSPA_temp,Contr_temp,DIR_Volts,REV_Volts)
        AEU = [0] * 448   # reinicio
        Amperes =  [0.0] * 448
        Amperes =  [0.0] * 448
        SSPA_Volts = [0.0] * 448
        Alarms  = [0.0] * 448
        SSPA_temp  = [0.0] * 448
        Contr_temp  = [0.0] * 448
        DIR_Volts = [0.0] * 448 #almacena el voltaje directo
        REV_Volts = [0.0] * 448 #almacena el voltaje reverso
        #print("incomplete", xml_list[i])
        count_xml = 0

def dayReport():
    pass

def showLastDateFiles():
    pass

def main():

    if read_xmls:
        #print("Date: ",year, doyear)
        if online == 0:  #ie offline
            startdate_ = datetime.datetime.strptime(startdate,"%Y/%m/%d").date()
            enddate_ = datetime.datetime.strptime(enddate,"%Y/%m/%d").date()
            print("Offline from: ", startdate_, "to: ",enddate_)
            try:
                delta_ = enddate_ - startdate_
                print("delta", delta_.days)
            except:
                print("Error in date range")

            date_list = [startdate_ + datetime.timedelta(days=x) for x in range(delta_.days + 1)]
            #print(date_list)
            for date_ in date_list:
                doy_ = date_.strftime('%j')
                try:
                    #print("trying ", doy_)
                    find_new_bz2(int(date_.year), int(doy_))

                except:
                    print("Searching valid files...")

                read_xml()
                #print("Date:", year_, doy_)
            print("---------------------------------------------------------------")
            print("%.2f hours read, " % (tot_xml/60),"and %.2f useful hours " % ((tot_xml - n_empty_files)/60))

        else:
            find_new_bz2(year, doyear)
            read_xml()
            check_aeu_status()


    if plot_pow:
        print("Plot amisr logs")
        plot_radar()

    #check_aeu_status()#habilitado en pruebas

if __name__ == '__main__':

    main()
