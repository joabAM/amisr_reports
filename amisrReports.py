
from plots_amisrDB import *
import amisrDB
from amisrStats import *
from report import Report
import argparse
import os


online = 0 # True or False 1 o 0
# startdate = '2021/08/15'  #formato yyyy/mm/dd para offline
# enddate = '2022/03/01'   #para offline
# hostname = '127.0.0.1'
# username = 'soporte'
# password = 'soporte'
# xml_path = '/media/soporte/DATA/dataAMISR/xmls/'



pkey = 'pathkey' #añadir la llave al conectar al servidor, agregar esto en el código

# 1 = Potencia, 2 = Corriente
# 3 = alarmas, 4 = temperaturas
# 5 = SSPA volt,  6 = Voltajes dir,
# 7 = volt rev,    8 = -8 volt

dataType = "power"

# 1 = mostrat, 0 = ocultar
show_plot = [1, 0, 0, 0] # grafico total, de panel, de aeu, n_pows, intervalos de potencia
plot_format = '1'
#cada panel en la lista [row, col]
#[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[7,1]
#[1,2],[2,2],[3,2],[4,2],[5,2],[6,2],[7,2]
panels_plot_list = [[1,1],[2,1],[3,1],[4,1],[5,1],[6,1],[7,1]]
panel_average = True    #muestra una gŕafica adicional con la potencia promedio de los paneles
show_plot_bar = False   #muestra barra de Gráficos en el último grafico

#cada AEU en la lista [row, col, n#]
#row: 1 a 7, col: 1 a 2, n: 1 a 32 -> cuando n=-1 se activa el rango, si es 0 muestra todas las AEU del panel
aeus_plot_list = [[3, 1, 0]]#,[4, 1, 17]]#,[3, 1, 15],[3, 1, 16],[3, 1, 20],[3, 1, 21],[3, 1, 27]]
aeus_plot_range =[1, 10] #rango de aeus, solo para funciona con -1

plot_interval_panel_list = [[1, 2], [2, 2], [7,2], [7,1]] # al estar vacio se omiten los gráficos
plot_interval = 0.5


curr_path = os.getcwd()
dataBasePath = curr_path+"/dataBase/"
bz2path = curr_path+"/bz2dir/"


def main(kwargs):
    keys = vars(kwargs)
    online = keys.get("online")
    flag_R_W = keys.get("read_write")
    startdate = keys.get("startDate")
    enddate = keys.get("endDate")
    hostname = keys.get("host")
    username = keys.get("user")
    password = keys.get("password")
    xml_path = keys.get("xml_path")
    pkey = keys.get("key_path")
    period = keys.get("period_online")
    e_sender = keys.get("email_sender")
    e_pass = keys.get("email_password")
    email2 = keys.get("email_cc1")
    email3 = keys.get("email_cc2")
    email1 = keys.get("email_dest")
    min_power = keys.get("power_alert")



    dataType = keys.get("dataType")
    interval = keys.get("interval")
    interval_a = keys.get("interval_alarm")

    flag_add_tables = keys.get("add_tables")
    flag_add_pie = keys.get("add_pie")
    flag_add_panels = keys.get("add_panels")





    ################################ESCRIBIR BASES DE DATOS en CSV
    ###objeto base de datos
    dbObj = amisrDB.DB_AMISR(xml_path,bz2path,dataBasePath, hostname, username,
                           password, online=online,key_file=pkey, period=period,
                           email_1=e_sender,email_2=email2,email_3=email3,
                           email_sender=e_sender,email_pass=e_pass,limit_alert=min_power)
    if online==True:
        dbObj.run_online()

    else:
        if flag_R_W=="write":
            dbObj.writeDB(startdate, enddate, dataType) #escribir base de datos

        else: #then is "read"

            DataDB = dbObj.readDB(dataType,startdate,enddate) #objeto con información en Pandas DataFrame
            # """Objeto para lectura de datos de gráficos antiguos"""
            #

            #lectura de ALARMA, solo vswr, retorna data y date

            DataAlarm = dbObj.readDB("alarm",startdate,enddate,aeuStatus = True,read_interval=interval_a ,alarmType="vswr")

            stats = STATS_AMISR(type=dataType, data=DataDB )
            #stats = STATS_AMISR()#contructor vacio, prueba de alarmas

            #
            # #plotObj2 = Plot_amisrDB("alarm") #antig{uo ploteo}
            #
            # """show_plot = [1, 0, 0, 0] primero solo potencia general"""




            report = Report(stats.startdate,stats.enddate)   #clase pdf report


            stats.updateNPows() # para getStatsTx y correlation
            stats.updateStatusTable()#necesario para los valores del pie, y las tablas

            fig_alarm = stats.getPlotsAlarms(DataAlarm)
            power_figure = stats.getPlotTotal(dataType,interval=60)
            #

            fig_intervals = stats.getTxIntervals()
            fig_xcorr = stats.getCrossCorrelation()
            figs_pie, values_pie = stats.getPieRep()
            fig_rate, rates = stats.getRateFig("cero", general=True)
            table_rate, rates = stats.getTableRates()

            table_over, total_pow = stats.getOverview() #ejecutar getRateFig() antes
            fig_alarm2 = stats.getPlotsAlarmRate(DataAlarm)

            panel_rates=[]
            for panel in range(14):
                f, r = stats.getRateFig("cero", general=False, panel=(panel+1))
                panel_rates.append([f,r])

            fig_panels,labels_list = stats.getPlotPanels(dataType, interval=60) #una hora, y sin especificar lista para obtener todos

            panel_details=[]
            for panel in range(14):
                panel_details.append(stats.getPanelDetail(n_panel=(panel+1)))

            ###stats.show()

            #
            report.print_overview(table_over, total_pow, power_figure)
            if flag_add_pie:
                report.addFigure(figs_pie, "pie", values_pie)
            report.addFigure(fig_intervals, "interval")
            report.print_rates(fig_rate, table_rate, rates)
            report.addFigure(fig_xcorr, "correlation")


            report.addFigure(fig_alarm, "alarm", fig_alarm2)

            for i in range(14):
                report.print_panel(fig_panels[i][0],fig_panels[i][1],panel_rates[i][0],panel_rates[i][1],labels_list[i])
                if flag_add_tables:
                    report.print_panel_detail(panel_details[i])
            #
            # #
            report.getReport()
            #







            #ejemplo:
            '''
            #dbObj.readDB(start_plot_date,end_plot_date,, aeuStatus = False, plot_interval=1,panel_plot_list=None,
            #        aeu_plot_list=None, aeus_plot_range = None, plot_interval_panel_list=None):
            #
            #    retorna y_p_total, y_p_total_xml, y_panel, y_aeu, y_nInt, y_nInt_panel, x
            #    return aeu_alarms,alarm_date  -> aeuStatus = True
            '''

            ################################ LECTURA DE DATOS

            #datos para pandas en lista
            #
            # DataPower = dbObj.readDB("power",startdate,enddate,rtl2PD=False,show_plot=show_plot,
            #         aeuStatus=False, plot_interval=0.5, panels_plot_list =panels_plot_list,
            #         aeus_plot_list=aeus_plot_list, aeus_plot_range=aeus_plot_range,
            #         plot_interval_panel_list=plot_interval_panel_list)
            # #
            # #
            # # ##Gráficos interactivos
            # plotObj1 = Plot_amisrDB("power",panel_average=panel_average,aeus_plot_list=aeus_plot_list,
            #         show_plot_bar = False)
            # #plotObj.getPlot(plot_format, show_plot, y_p_total, y_p_total_xml,y_panel,
            # #y_aeu, y_nInt,y_nInt_panel, x):
            # plotObj1.setRadarList(dbObj.getPanelList())
            # plotObj1.getPlot(plot_format, show_plot, DataPower[0], DataPower[1], DataPower[2], DataPower[3],
            #                 DataPower[4], DataPower[5], DataPower[6], panels_plot_list)





            # aeus_plot_list2=[[3, 1, 0]]
            # DataPlot2 = dbObj.readDB(8,startdate,enddate,show_plot, False,plot_interval, panels_plot_list,
            #         aeus_plot_list2, aeus_plot_range, plot_interval_panel_list)
            #
            #
            # plotObj2 = Plot_amisrDB(8,panel_average=panel_average,aeus_plot_list=aeus_plot_list2,show_plot_bar = False)
            # #plotObj.getPlot(plot_format, show_plot, y_p_total, y_p_total_xml,y_panel,
            # #y_aeu, y_nInt,y_nInt_panel, x):
            # plotObj2.setRadarList(dbObj.getPanelList())
            # plotObj2.getPlot(plot_format, show_plot, DataPlot2[0], DataPlot2[1], DataPlot2[2], DataPlot2[3],
            #                 DataPlot2[4], DataPlot2[5], DataPlot2[6], panels_plot_list)
            #plotObj1.show()
            # plotObj2.show()

            ###############################REPORTES ESTADÍSTICOS


    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--read_write",type=str, default="read", help="read = True , write = False")
    parser.add_argument("--online",type=bool, default=False, help=" online or offline mode")
    parser.add_argument("--startDate",type=str, default=None, help="Date DD/MM/YYYY")
    parser.add_argument("--endDate",type=str, default=None, help="Date DD/MM/YYYY")
    parser.add_argument("--interval",type=int, default='60', help="plot interval")
    parser.add_argument("--interval_alarm",type=int, default='6', help="plot interval for alarm")
    parser.add_argument("--host",type=str, default='127.0.0.1', help="IP server xml")
    parser.add_argument("--user",type=str, default='soporte', help="user")
    parser.add_argument("--password",type=str, default='soporte', help="password")
    parser.add_argument("--xml_path",type=str, default='/media/soporte/DATA/dataAMISR/xmls/', help="path to data")
    parser.add_argument("--period_online",type=str, default=None, help="period to check status in seconds")
    parser.add_argument("--email_sender",type=str, default=None, help="email sender")
    parser.add_argument("--email_password",type=str, default=None, help="password sender")
    parser.add_argument("--email_cc1",type=str, default=None, help="copy msg")
    parser.add_argument("--email_cc2",type=str, default=None, help="copy msg")
    parser.add_argument("--email_dest",type=str, default=None, help="main recipient")
    parser.add_argument("--power_alert",type=int, default=150, help="minimum power to send alert")


    parser.add_argument("--add_tables",type=bool, default=True, help="tables of status per panel")
    parser.add_argument("--add_pie",type=bool, default=True, help="page of pie charts")
    parser.add_argument("--add_panels",type=bool, default=True, help="pages of panels")
    parser.add_argument("--dataType",type=str, default="power", help="data type read for processing")
    kwargs = parser.parse_args()

    main(kwargs)
