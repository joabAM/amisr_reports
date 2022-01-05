#!/usr/bin/env python3
'''

@author: Oper - Joab Apaza
'''

import datetime
import time
import matplotlib.dates as mdates

import os,glob,stat
import os.path
import bz2
import xml.etree.ElementTree as ET
import csv
from pytz import timezone
import numpy as np
import paramiko

import aeustatus_sri as aeuST
import fileinput

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

dictDataType = {"power":1, "current":2, "alarms":3, "temperature":4,
                "SSPA volts":5, "volts dir":6, "volts rev":7,
                "-8 volts":8
                }

class DB_AMISR ():

    xmlPath = ""
    bz2path = ""
    DataType = None
    csvpathfile = ""
    dataBasePath = ""
    tot_xml = 0
    n_empty_files = 0
    last_day = None
    flag_read_l_date = 0
    online=False
    startdate = ""
    enddate = ""
    hostname = ""
    username = ""
    password = ""
    curr_day = None
    show_all_panel = []  #número panel
    aeu_plot_list = [] #lista de AEUs se almacenan en formato 1 a 448
    panel_plot_list = []    #lista de paneles se almacenan en formato 1 a 14
    aeus_plot_range = []

    def __init__(self,xmlPath,bz2Path,dataBasePath,hostname, username,
                password, online=False):

        self.xmlPath = xmlPath
        self.bz2path = bz2Path
        self.online = online
        self.hostname = hostname
        self.username = username
        self.password = password
        self.dataBasePath = dataBasePath


    def getPanelList(self):

        return self.show_all_panel, self.aeus_plot_range

    def definePath(self,dataType):

        if dataType>7 and dataType <1:
            print("Invalid data type to write...")
            return 0

        self.DataType = dataType
        if self.DataType == 1:       #potencias
            self.csvpathfile = self.dataBasePath +'dataPower.csv'
        elif self.DataType == 2:     #Corrientes
            self.csvpathfile =  self.dataBasePath +'dataCurrent.csv'
        elif self.DataType == 3:     # Alarmas
            self.csvpathfile = self.dataBasePath +'dataAlarm.csv'
        elif self.DataType == 4:     #Temperaturas
            if temperatureType == 1:
                self.csvpathfile = self.dataBasePath +'dataTemperatureSSPA.csv'
            if temperatureType == 2:
                self.csvpathfile = self.dataBasePath +'dataTemperatureCRTL.csv'
        elif self.DataType == 5:     # voltaje SSPA
            self.csvpathfile = self.dataBasePath +'dataSSPAvolts.csv'
        elif self.DataType == 6:     # voltajes Dir
            self.csvpathfile = self.dataBasePath +'dataFWDvolts.csv'
        elif self.DataType == 7:     # voltajes Rev
            self.csvpathfile = self.dataBasePath +'dataREVvolts.csv'
        else:     # voltajes Rev
            self.csvpathfile = self.dataBasePath +'dataM8Vvolts.csv'

    def find_new_bz2(self,s_year, s_doy):
        ''' Agregar en el futuro paramiko para traer los archivos
         desde el servidor y dejar en la carpeta bz2dir'''
        source = self.xmlPath+str(s_year)+'/'+str(s_doy).zfill(3)+'/'
        #print("buscando: ...", source)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.hostname, port=22, username=self.username, password=self.password)
        sftp_client = client.open_sftp()

        if len(os.listdir(self.bz2path)) != 0:
            #print("Cleanning b2z dir...")
            files = glob.glob(self.bz2path+"*")
            #print(files)
            for f in files:
                try:
                    os.remove(f)
                except:
                    continue

        for sftp_file in sftp_client.listdir(source):
            sftp_client.get(source+sftp_file,  self.bz2path+sftp_file)
        sftp_client.close()

        listbz2 =  os.listdir(self.bz2path)      #read all files
        listbz2.sort()
        print("decompressing... year: {} doy: {}".format(s_year,s_doy))
        for filebz2 in listbz2:
            if filebz2.endswith(".bz2"):
                self.decompress(self.bz2path + filebz2)
                os.remove(self.bz2path + filebz2)


    def decompress(self, path):
        try:
            with bz2.BZ2File(path) as zipfile:
                data = zipfile.read() # get the decompressed data
                newfilepath = path[:-4] # assuming the filepath ends with .bz2
                xml = open(newfilepath, 'wb')
                xml.write(data)  # write a uncompressed file
                xml.close() #close the file
        except:
            print ("\nError on reading compressed file")
            pass


    def update_data(self,data_to_write,_date,_time ):
        '''
            Escribe en el csv solo si no existe el día, caso contrario lo omite
            data: 'date' 'time' 'good', 'numtx', 'bad', 'ugly', 'rf', 'peak', 'total', 'numrx',AEU[1], AEU[2]..
            ... AEU[448], npow[],amp[1:448], volts[1:448], alarms[1:448], temSS[1:448], tempCT[1:448]
            visto como 1 hasta 14 el número de paneles, la columna 2 completan del 8 al 14
        '''

        last_row = []
        #old_csv_d  ata = []

        if os.path.isfile(self.csvpathfile):
            modecsv = 'a'
            #print("l_date",self.flag_read_l_date)
            if self.flag_read_l_date == 0:
                print("reading last date...")
                with open(self.csvpathfile, 'r') as file_reader:
                    f_reader = csv.reader(file_reader)
                    for row in f_reader:
                        last_row = row
                    self.last_day = datetime.datetime.strptime(last_row[0]+" "+last_row[1],"%Y-%m-%d %H:%M:%S")
                self.flag_read_l_date = 1
        else:
            modecsv = 'w'


        with open(self.csvpathfile,modecsv) as csvfile:
            file = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
            #if self.online:
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

            act_day = datetime.datetime.strptime(_date +" "+ _time,"%Y-%m-%d %H:%M:%S")

            if self.online == 0 and modecsv=='a' and self.flag_read_l_date == 1:
                if act_day > self.last_day :
                    if act_day != self.curr_day:
                        print("writing csv... Date: ", act_day)
                        self.curr_day = act_day
                    #print(data_to_write)
                    file.writerow(data_to_write)
                    return True
                else:
                    return False
                    print("The data in these files has already been processed.")
            else:
                file.writerow(data_to_write)


    def read_xml(self):
        '''Lee los xmls, filtra los archivos con datos validos, ademas de poder sacar un
            promedio mínimo de 1 minutos. Añade el conteo de intervalos de potencia
            100 a 200, 200 a 300, etc
        '''
        readStatus = aeuST.AEUStatus()
        xml_list = os.listdir(self.bz2path)
        filepath = xml_list

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
        m8volts = [0.0] * 448 #almacena el voltaje de -7.5
        DIR_Volts = [0.0] * 448 #almacena el voltaje directo
        REV_Volts = [0.0] * 448 #almacena el voltaje reverso
        Alarms  = [0] * 448  # almacena las alarmas en formato decimal
        SSPA_temp  = [0.0] * 448
        Contr_temp  = [0.0] * 448
        n_pows = [[0 for i in range(7)] for n in  range(14)]
        date_toWrite = None
        time_toWrite = None
        #print("lista", xml_list)
        pow_var=['good', 'numtx', 'bad', 'ugly', 'rf', 'peak', 'total', 'numrx']



        for i in range(len(xml_list)):
            filepath =  self.bz2path + xml_list[i]
            tree=ET.parse(filepath)
            root=tree.getroot()
            date_time = root.get('timestamp')
            date_ = date_time[:10]
            time_=date_time[11:19]  #"2014-09-02 00:06:00.011163+00:00"
            #print("Date time",date_time)
            panel = root.find('panel')
            power = root.find('power').attrib
            self.tot_xml = self.tot_xml + 1
            data = None
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
                        try:
                            m8volts[pos_aeu]    = round(readStatus.m8v_voltage_monitor)
                        except:
                            m8volts[pos_aeu]    = 0
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

                s_pow=[]
                for n in n_pows:
                    for x in n:
                        s_pow.append(x)

                if self.DataType == 1:
                    data = [date_toWrite, time_toWrite] + pow_panel + AEU + s_pow
                elif self.DataType == 2:
                    data = [date_toWrite, time_toWrite] +  Amperes
                elif self.DataType == 3:
                    data = [date_toWrite, time_toWrite] +  Alarms
                elif self.DataType == 4:
                    if temperatureType == 1:
                        data = [date_toWrite, time_toWrite] + SSPA_temp
                    elif temperatureType == 2:
                        data = [date_toWrite, time_toWrite] + Contr_temp
                    else:
                        print("ERROR invalid temperatureType")
                        return
                elif self.DataType == 5:
                    data = [date_toWrite, time_toWrite] + SSPA_Volts
                elif self.DataType == 6:
                    data = [date_toWrite, time_toWrite] + DIR_Volts
                elif self.DataType == 7:
                    data = [date_toWrite, time_toWrite] + REV_Volts
                elif self.DataType == 8:
                    data = [date_toWrite, time_toWrite] + m8volts

                self.curr_day = datetime.datetime.strptime(date_toWrite +" "+ time_toWrite,"%Y-%m-%d %H:%M:%S")
                self.update_data(data, date_toWrite, time_toWrite)

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
                m8volts = [0.0] * 448
                #print("xml day", xml_list[i])


            else:
                #print("No data in xml file...")
                self.n_empty_files = self.n_empty_files + 1


            os.remove(filepath)        #elimina el xml una vez leído


    def writeDB(self, startdate, enddate, dataType):

        dataType = dictDataType[dataType]
        self.definePath(dataType)
        self.startdate = startdate
        self.enddate = enddate

        if self.online == 0:  #ie offline
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
                    self.find_new_bz2(int(date_.year), int(doy_))

                except:
                    print("Searching valid files... year: {} doy: {}".format(int(date_.year),int(doy_)))

                self.read_xml()
                #print("Date:", year_, doy_)
            print("---------------------------------------------------------------")
            print("%.2f hours read, " % (self.tot_xml/60),"and %.2f useful hours " % ((self.tot_xml - self.n_empty_files)/60))

        else:
            self.find_new_bz2(year, doyear)
            self.read_xml()
            self.check_aeu_status()
        return



    def readDB(self,dataType, start_plot_date,end_plot_date,rtl2PD=False, show_plot=False, aeuStatus = False, plot_interval=1,
                panels_plot_list=None, aeus_plot_list=None, aeus_plot_range = None, plot_interval_panel_list=None):

        return_lines_to_PD = rtl2PD
        dataType = dictDataType[dataType]
        self.definePath(dataType)
        self.show_all_panel = []  #número panel
        self.aeu_plot_list = [] #lista de AEUs se almacenan en formato 1 a 448
        self.panel_plot_list = []    #lista de paneles se almacenan en formato 1 a 14
        self.aeus_plot_range = aeus_plot_range

        start_plot_date = start_plot_date.replace('/','-')
        end_plot_date = end_plot_date.replace('/','-')

        real_start_date = None
        real_end_date = None

        valid_interval = [0, 0.1, 0.5, 1, 2, 6, 12, 24] #el doble de lo ingresado
        interval = float(plot_interval)  #
        if not(interval in valid_interval):
            print("Invalid time interval for plot, use 0, '0.1', '0.5', '1', '2', '6', '12' or '24' hours")
            return
        interval *=60 # ahora interval en minutos interval = 2*15*plot_interval
        if interval == 0:
            interval = 1
        print("data Prom: {:2d} min".format(int(interval)))

        if self.DataType == 1: #solo para potencia
            startIndex = 10
        else:
            startIndex = 2

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
        if not return_lines_to_PD :
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
                        self.aeu_plot_list.append(rc_to_aeu(r,c,(i+1)))
                    self.show_all_panel.append([r,c])
                    self.aeus_plot_range = [1,32]
                elif n == -1:      ###plot block panel
                    for i in range(self.aeus_plot_range[0],self.aeus_plot_range[1]+1):
                        self.aeu_plot_list.append(rc_to_aeu(r,c,i))
                    self.show_all_panel.append([r,c])
                else:
                    self.aeu_plot_list.append(rc_to_aeu(r,c,n))
            #print(self.aeu_plot_list)
            #cambiar y verificar la lista de entrada para
            #graficar paneles
            for r,c in panels_plot_list:
                if r > 7 or r < 1:
                    print("Invalid value to row number /panel_list")
                    return
                if c > 2 or c < 1:
                    print("Invalid value to colum number /panel_list")
                    return
                self.panel_plot_list.append(rc_to_aeu(r,c,32)/32)


            for r,c in plot_interval_panel_list:
                if r > 7 or r < 1:
                    print("Invalid value to row number /interval_panel_list")
                    return
                if c > 2 or c < 1:
                    print("Invalid value to colum number /interval_panel_list")
                    return
                plot_pow_list.append(int(rc_to_aeu(r,c,32)/32))

        y_panel = [[] for i in range(len(self.panel_plot_list))]
        y_aeu = [[] for i in range(len(self.aeu_plot_list))]
        y_nInt = [[] for i in range(9)] # 9 = intervals(7)+ good + bad
        y_nInt_panel = [[[] for i in range(7)] for k in range(14)]
        aeu_alarms = [[] for i in range(448)]
        alarm_date = []
        if os.path.isfile(self.csvpathfile):

            with fileinput.input([self.csvpathfile]) as csvFile:

                s_date = start_plot_date
                e_date = end_plot_date

                print(s_date, e_date)
                s_date = datetime.datetime.strptime(s_date,"%Y-%m-%d").date()
                e_date = datetime.datetime.strptime(e_date,"%Y-%m-%d").date() + datetime.timedelta(days=1)
                day_date = s_date
                flag_remnantData = False

                index_line = 1   #  Nro de linea
                valid_lines = 0
                M = 0
                #print("tot lines",len(lines))
                for line in csvFile:          #cada línea de la lista son muestras cada 1 min
                    line = line.rstrip("\n")
                    line = line.split(",")
                    date = datetime.datetime.strptime(line[0]+line[1],"%Y-%m-%d%H:%M:%S")

                    if fileinput.isstdin() and len(day_lines)>1 :
                        flag_remnantData = True
                    if (date.date() >= s_date and date.date() <= e_date) or flag_remnantData:       #Rango de fechas validos
                        #print(index_line)
                        #-----------------------------------------------------------------------------------------
                        if return_lines_to_PD:              #índice de línea
                            day_lines.append(line)
                            continue

                        new_date = date.date()
                        if new_date > day_date or fileinput.isstdin(): #hasta aquí se tiene una lista de todo 1 día

                            #print(new_date)
                            k = 0
                            S_acum_1 = 0  #suma de AEUs
                            S_acum_2 = 0  #potencia pico xml
                            S_p_acum = [0]*len(self.panel_plot_list)
                            S_aeu_acum = [0]*len(self.aeu_plot_list)
                            S_n_acum = [0]*9
                            S_n_acum_panel = [[0 for x in range(7)] for n in range(14)]
                            #print("daylines", len(day_lines))

                            for _l in day_lines:    #todas las lineas del día
                                k += 1
                                if not aeuStatus:
                                    #*********************************************************************************
                                    if show_plot[0] == 1: # potencia total
                                        S = sum(float(j) for j in _l[startIndex:(startIndex+448)])#Suma todas las AEUs
                                        S_acum_1 += S
                                        S_acum_2 += float(_l[7])
                                    #*********************************************************************************
                                    if show_plot[1] == 1: # potencia panel
                                        #N_panel  del 1 al 14
                                        m = 0
                                        for pl in self.panel_plot_list:
                                            init_panel = startIndex + (int(pl)-1)*32
                                            end_panel =  startIndex + int(pl)*32
                                            S = sum(float(j) for j in _l[init_panel:end_panel]) #suma de panel
                                            #S = sum(float(j) for j in _l[init_panel:end_panel])/32 #promedio de panel
                                            S_p_acum[m] += S
                                            m += 1
                                    #*********************************************************************************
                                    if show_plot[2] == 1: # potencia aeu
                                        m = 0
                                        #print(self.aeu_plot_list)
                                        for nAeu in self.aeu_plot_list:
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
                                ###if aeuStatus and (new_date == plot_status_day) : #para 1 solo día #ALARMA
                                else:
                                    i = 0
                                    for v in _l[startIndex:(startIndex+448)+1]:  #.split(","):
                                        #print(aeu_alarms)
                                        aeu_alarms[i].append(v)
                                        i += 1
                                    alarm_date.append(datetime.datetime.strptime(_l[0]+'_'+_l[1][:5],"%Y-%m-%d_%H:%M"))
                                    continue
                                #*********************************************************************************
                                #*********************************************************************************
                                #*********************************************************************************
                                #******************************* WRITE AND RESET**********************************
                                if k == interval and (not aeuStatus):
                                    #********act Pot total
                                    q =datetime.datetime.strptime(_l[0]+'_'+_l[1][:5],"%Y-%m-%d_%H:%M")
                                    x.append(q)
                                    #print(k, q)
                                    y_p_total.append(S_acum_1/interval)
                                    y_p_total_xml.append(S_acum_2/interval)

                                    for n in range(len(self.panel_plot_list)):
                                        y_panel[n].append(S_p_acum[n]/interval)


                                    for n in range(len(self.aeu_plot_list)):
                                        y_aeu[n].append(S_aeu_acum[n]/interval)

                                    for n in range(9):
                                        y_nInt[n].append(S_n_acum[n]/interval)

                                    for p in range(14):#para cada panel
                                        for n in range(7):
                                            y_nInt_panel[p][n].append(S_n_acum_panel[p][n]/interval)
                                    k = 0
                                    S_acum_1 = 0
                                    S_acum_2 = 0
                                    S_p_acum = [0]*len(self.panel_plot_list)
                                    S_aeu_acum = [0]*len(self.aeu_plot_list)
                                    S_n_acum = [0]*9
                                    S_n_acum_panel = [[0 for x in range(7)] for n in range(14)]

                            if (k != 0) and (not aeuStatus): #en caso se termine los datos sin completar el nro requerido para promediar
                                x.append(datetime.datetime.strptime(_l[0]+'_'+_l[1][:5],"%Y-%m-%d_%H:%M"))

                                y_p_total.append(S_acum_1/k)
                                y_p_total_xml.append(S_acum_2/k)

                                for n in range(len(self.panel_plot_list)):
                                    y_panel[n].append(S_p_acum[n]/k)

                                for n in range(len(self.aeu_plot_list)):
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


            x = [n.replace(tzinfo=timezone('UTC')) - datetime.timedelta(hours=5) for n in x]   #to localTime

            if return_lines_to_PD :
                return day_lines

            if aeuStatus:
                return aeu_alarms,alarm_date

            return y_p_total, y_p_total_xml,y_panel,y_aeu, y_nInt,y_nInt_panel, x



        else:
            print("There is no data")
