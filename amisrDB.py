#!/usr/bin/env python3
'''

@author: Oper - Joab Apaza
'''

import datetime
import time
import matplotlib.dates as mdates
import sys
import os,glob,stat
import os.path
import bz2
import xml.etree.ElementTree as ET
import csv
from pytz import timezone
import numpy as np
import paramiko
import pandas as pd
import smtplib
import aeustatus_sri as aeuST
import fileinput

from utils import *


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
                password,online=False, key_file=None, period=900, email_1=None,
                email_2=None,email_3=None,email_sender=None,email_pass=None,limit_alert=150):

        self.xmlPath = xmlPath
        self.bz2path = bz2Path
        self.online = online
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key      = key_file
        self.dataBasePath = dataBasePath
        self.period_online = period
        self.email_recipients =  [email_1]
        if email_2 != None:
            self.email_recipients.append(email_2)
        if email_3 != None:
            self.email_recipients.append(email_3)
        self.email_sender = email_sender
        self.email_password = email_pass
        self.power_limit_alert = limit_alert
        self.curret_amisr_status = [0]*8

        ##***********************************************************************
        self.labels_status_gnral = ['good', 'numtx', 'bad', 'ugly', 'rf', 'peak', 'total', 'numrx']
        self.nAeusTx = (448/2 +1) #mas de la mitad transmitiendo para considerarlo útil
        if self.online:
            self.nAeusTx = 0
        self.check_last_date = False


    def getPanelList(self):

        return self.show_all_panel, self.aeus_plot_range

    def definePath(self,dataType):
        #usa números yase ha usado decodeDataType()
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
        elif self.DataType == 41:     #Temperaturas
            self.csvpathfile = self.dataBasePath +'dataTemperatureSSPA.csv'
        elif self.DataType == 42:
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

        #client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(self.hostname, port=22, username=self.username, password=self.password, key_filename=self.key)

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
        remote_files_list=[]
        for sftp_file in sftp_client.listdir(source):
            remote_files_list.append(sftp_file)
        remote_files_list.sort(key=lambda date: datetime.datetime.strptime(date, "%Y%m%d-%H%M%S-umet.xml.bz2"))

        if self.online:
            if len(remote_files_list) > self.period_online:
                remote_files_list = [remote_files_list[-2]] #trabaja con el penultimo archivo
                print("online mode, reading file ",remote_files_list)
            else:
                return
        for remote_file in remote_files_list:
            #print("getting ",(source+remote_file) )
            sftp_client.get(source+remote_file,  self.bz2path+remote_file)
        sftp_client.close()

        listbz2 =  os.listdir(self.bz2path)      #read all files
        listbz2.sort()
        print("decompressing... year: {} doy: {}".format(s_year,s_doy))
        for filebz2 in listbz2:
            if filebz2.endswith(".bz2"):
                self.decompress(self.bz2path + filebz2)
                os.remove(self.bz2path + filebz2)
        #client.close()

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
        if not self.online:
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
        pow_var=self.labels_status_gnral

        op_ = False

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

    	    #hay casos que se transmite con medio arreglo o solo 1 panel, eso para pruebas
            if panel != None and int(power.get('numtx')) > self.nAeusTx : # and power.get('rf')==1:
                #print(date_time, power)
                count_xml = count_xml + 1
                time_toWrite = time_
                date_toWrite = date_
                #print("count", count_xml)

                j = 0
                for var in pow_var:
                    pow_panel[j]+=int(power.get(var)) #Acumula datos de Potencia "good,numtx,bad,ugly,rf,peak,total,numrx"
                    self.curret_amisr_status[j] = int(power.get(var))
                    j = j + 1
                self.curr_day = datetime.datetime.strptime(date_toWrite +" "+ time_toWrite,"%Y-%m-%d %H:%M:%S")

                if  self.online:
                    os.remove(filepath)
                    return

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
                elif self.DataType == 41:
                    data = [date_toWrite, time_toWrite] + SSPA_temp
                elif self.DataType == 42:
                    data = [date_toWrite, time_toWrite] + Contr_temp
                elif self.DataType == 5:
                    data = [date_toWrite, time_toWrite] + SSPA_Volts
                elif self.DataType == 6:
                    data = [date_toWrite, time_toWrite] + DIR_Volts
                elif self.DataType == 7:
                    data = [date_toWrite, time_toWrite] + REV_Volts
                elif self.DataType == 8:
                    data = [date_toWrite, time_toWrite] + m8volts




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
                op_ = True

            else:
                if self.online:
                    print("no data for date: ",datetime.datetime.strptime(date_ +" "+ time_,"%Y-%m-%d %H:%M:%S"))
                #print("No data in xml file...")
                self.n_empty_files = self.n_empty_files + 1
                op_ = False

            os.remove(filepath)        #elimina el xml una vez leído
        return op_

    def writeDB(self, startdate, enddate, dataType):

        str_type = dataType

        if self.online == False:  #ie offline
            dataType =  decodeDataType(dataType)
            self.definePath(dataType)
            self.startdate = startdate
            self.enddate = enddate
            print("Writting {}...".format(str_type))
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

                except Exception as e:
                    print("Error {} year: {} doy: {}".format(e, int(date_.year),int(doy_)))
                    print("Searching valid files... ")

                self.read_xml()
                #print("Date:", year_, doy_)
            print("---------------------------------------------------------------")
            print("%.2f hours read, " % (self.tot_xml/60),"and %.2f useful hours " % ((self.tot_xml - self.n_empty_files)/60))

        else:
            today   = datetime.date.today()
            year    = today.year
            doyear  = str(today.timetuple()[7])

            self.find_new_bz2(year, doyear)
            self.read_xml()
            #self.check_aeu_status()
        return


    def getDayPower(self,outPath, powerDay_date=None ):
        
        if powerDay_date==None:
            print("You must specify --startDate=nnnnn !")
            return
        ##reading current ##########################################################################
        self.definePath(2)
        day_lines = []
        work_path = os.getcwd()
        s_date = datetime.datetime.strptime(powerDay_date,"%Y/%m/%d").date()
        labels = pd.read_csv(work_path+"/labels-default.csv")

        if os.path.isfile(self.csvpathfile):
            with fileinput.input([self.csvpathfile]) as csvFile:
                index_line = 1   #  Nro de linea
                valid_lines = 0
                M = 0
                #print("tot lines",len(lines))
                date = None
                for line in csvFile:          #cada línea de la lista son muestras cada 1 min
                    line = line.rstrip("\n")
                    line = line.split(",")
                    date = datetime.datetime.strptime(line[0]+line[1],"%Y-%m-%d%H:%M:%S")

                    if (date.date() == s_date ):       #datos para todo un día
                        day_lines.append(line)

        dataCurrent = pd.DataFrame(day_lines, dtype='int32')
        dataCurrent.columns = labels.columns
        dataCurrentF = fix_dataframe_date(dataCurrent)
        dataCurrentF = dataCurrentF.drop(columns=['time'])
        dataCurrentF.set_index("date", inplace=True)
        dataCurrentF = dataCurrentF  - 0.15 #regular consumption AEU 
        dataCurrentF[dataCurrentF<0] = 0


        day_lines = []
        ##reading sspa voltage############################################################################
        self.definePath(5)
        if os.path.isfile(self.csvpathfile):
            with fileinput.input([self.csvpathfile]) as csvFile:
                index_line = 1   #  Nro de linea
                valid_lines = 0
                M = 0
                #print("tot lines",len(lines))
                date = None
                for line in csvFile:          #cada línea de la lista son muestras cada 1 min
                    line = line.rstrip("\n")
                    line = line.split(",")
                    date = datetime.datetime.strptime(line[0]+line[1],"%Y-%m-%d%H:%M:%S")
                    if (date.date() == s_date ):       #datos para todo un día
                        day_lines.append(line)

        dataSSPAVolts = pd.DataFrame(day_lines, dtype='int32')
        dataSSPAVolts.columns = labels.columns
        dataSSPAVoltsF = fix_dataframe_date(dataSSPAVolts)
        dataSSPAVoltsF = dataSSPAVoltsF.drop(columns=['time'])
        dataSSPAVoltsF.set_index("date", inplace=True)

        if (len(dataSSPAVoltsF)!= len(dataCurrentF)):
            print("Error data lenght  current and voltage")
            print(len(dataCurrentF), len(dataSSPAVoltsF))
            return False
        avgPower = pd.DataFrame(dataCurrentF.values*dataSSPAVoltsF.values, index=dataCurrentF.index)
        f = avgPower.sum(axis=1)
        name = "power_"+powerDay_date.replace("/","")+'.csv'
        filename = os.path.join(outPath, name)
        f.to_csv(filename)
        print("Created fle: {}".format(filename))
        return True

    def readDB(self,dataType, start_plot_date,end_plot_date, aeuStatus = False,read_interval="0.1", alarmType="none"):
        strdata = dataType
        dataType =  decodeDataType(dataType)
        self.definePath(dataType)

        start_plot_date = start_plot_date.replace('/','-')
        end_plot_date = end_plot_date.replace('/','-')

        real_start_date = None
        real_end_date = None

        valid_interval = [0, 0.1, 0.5, 1, 2, 6, 12, 24] #el doble de lo ingresado
        interval = float(read_interval)  #
        if not(interval in valid_interval):
            print("Invalid time interval for plot, use 0, '0.1', '0.5', '1', '2', '6', '12' or '24' hours")
            return
        interval *=60 # ahora interval en minutos interval = 2*15*plot_interval
        if interval == 0:
            interval = 1

        if not self.check_last_date:
            print("Data {} ".format(strdata))


        startIndex = 2 # primeros 2 son hora


        day_lines = []

        s_date = ''
        e_date = ''
        #Cambiar los datos de las AEUS a una solo lista
        #verificar el rango

        #Alarmas vacio para las 448 y el total de promedio
        dataAlarms = pd.Series(0, index=range(448))
        aeu_alarms = pd.DataFrame(columns=range(449))
        k = 0
        i_df = 0
        if os.path.isfile(self.csvpathfile):

            with fileinput.input([self.csvpathfile]) as csvFile:

                s_date = start_plot_date
                e_date = end_plot_date

                if not self.check_last_date:
                    print(s_date, e_date)
                s_date = datetime.datetime.strptime(s_date,"%Y-%m-%d").date()
                e_date = datetime.datetime.strptime(e_date,"%Y-%m-%d").date()

                if s_date > e_date:
                    print("Final date must be higher thar initial date!!!...")
                    os._exit(os.EX_IOERR)

                if s_date == e_date:
                    e_date += datetime.timedelta(days=1)
                day_date = s_date


                index_line = 1   #  Nro de linea
                valid_lines = 0
                M = 0
                #print("tot lines",len(lines))
                date = None
                for line in csvFile:          #cada línea de la lista son muestras cada 1 min
                    line = line.rstrip("\n")
                    line = line.split(",")
                    date = datetime.datetime.strptime(line[0]+line[1],"%Y-%m-%d%H:%M:%S")
                    if self.check_last_date:
                        continue
                    if (date.date() >= s_date and date.date() <= e_date):       #Rango de fechas validos
                        #print(index_line)
                        #-----------------------------------------------------------------------------------------
                        if aeuStatus : #                                solo  #ALARMA

                            listA = [int(float(n)) for n in line[startIndex:(startIndex+448)+1]]
                            df = pd.Series(listA)

                            df = df.where(df == decodeAlarm(alarmType))
                            df.fillna(value=0, inplace=True)
                            df = df.astype('int64')

                            dataAlarms = dataAlarms | df
                            k += 1
                            if k == interval:
                                date= line[0]+' '+line[1][:5]
                                k = 0
                                aux = [date]+dataAlarms.tolist()
                                aeu_alarms.loc[i_df] = aux
                                dataAlarms = pd.Series(0, index=range(448)) #reinicio
                                i_df += 1

                        else:
                            day_lines.append(line)

                        #*********************************************************************************

                        valid_lines += 1

                    index_line += 1

            if self.check_last_date:
                return date             #retorna la ultima fecha



            if aeuStatus:
                aeu_alarms.set_index(0, inplace=True)
                #print(aeu_alarms)
                return aeu_alarms

            else:
                if len(day_lines) < 1:
                    print("Error, there is no data for those dates... Data type: ",strdata)
                    sys.exit()

                return day_lines


        else:
            print("There is no data")


    def run_online(self):
        '''

        good    numtx   bad     ugly    rf      peak    total   numrx
        0       1       2       3       4       5       6       7
        '''
        msg_sended = 0
        time.sleep(120)
        limit_timer = self.period_online
        flag_bellow_power = False
        flag_radar_on = False
        flag_rf_on = False
        while True:

            self.writeDB(None, None, None)

            if (self.curret_amisr_status[1] > 200):
                flag_radar_on = True
            else:
                flag_radar_on = False

            if (self.curret_amisr_status[4] > 0): #toma 0 o 1
                flag_rf_on = True
            else:
                flag_rf_on = False


            if flag_bellow_power and (self.curret_amisr_status[5] > self.power_limit_alert):
                msg_sended = 0
                limit_timer = self.period_online
                flag_bellow_power = False

            if self.curret_amisr_status[5] < self.power_limit_alert:
                flag_bellow_power = True
                print("Power bellow limit...")
                msg_sended +=1
                if limit_timer == 300:
                    limit_timer = 120   #se espera 2 min
                else:
                    limit_timer = 300    #se cambia a esperar solo 5 min para la proxima revision

            print("\n",self.labels_status_gnral)
            print(self.curret_amisr_status)

            time.sleep(limit_timer)


            if msg_sended > 5:
                print("Online monitoring finished...")
                break

            if flag_radar_on and (msg_sended > 3) and  flag_rf_on: #baja potencia, con AEU en tx/rx
                print("Sending alert!!!... status:{} under limit:{}".format(self.curret_amisr_status[5],self.power_limit_alert))
                self.send_alert(self.curret_amisr_status,self.curr_day, "power")

            if flag_radar_on and (msg_sended > 3) and not flag_rf_on: # sin rf, con AEU en tx/rx
                print("Sending alert!!!... status rf:{} , no RF signal".format(flag_rf_on))
                self.send_alert(self.curret_amisr_status,self.curr_day, "rf")


    def send_alert(self,power_status, datetime, type):

        dest_mail = self.email_recipients
        message = ""
        if type=="power":
            message = 'Drop in AMISR Power, transmiting with '+ str(power_status[5]/1000)+ ' KWatts\n'
        elif type =="rf":
            message = 'No RF signal input!!! '

        subject = 'AMISR-14 POWER ALERT'
        str1 = ' \t'.join(self.labels_status_gnral )
        #str2 = ' \t'.join(power_status)
        message += str1+'\n'
        #message += str2
        message = 'Subject: {}\n\n{}'.format(subject, message)
        server = smtplib.SMTP('smtp.gmail.com',587)
        server.starttls()
        print("Sending alert to ", dest_mail)
        server.login(self.email_sender,self.email_password)
        server.sendmail(self.email_sender, dest_mail, message)
        server.quit()

    def last_database_dates(self):
        self.check_last_date = True
        data_types=[1,2,3,41,42,5,6,7,8]
        for dataTypeInt in data_types:
            self.definePath(dataTypeInt)
            try:
                last_date = self.readDB(encodeDataType(dataTypeInt), '2014/01/01', '2030/01/01')
                print("Last date for \t{:<25} \tis \t{}".format(os.path.split(self.csvpathfile)[1],last_date))
            except:
                print("There is no {} database file...".format(os.path.split(self.csvpathfile)[1]))
        return
