
from plots_amisrDB import *
import amisrDB
from amisrStats import *
from report import Report

import os


online = 0 # True or False 1 o 0
startdate = '2021/12/01'  #formato yyyy/mm/dd para offline
enddate = '2021/12/15'   #para offline
hostname = '127.0.0.1 '
username = 'soporte'
password = 'soporte'
xml_path = '/media/soporte/DATA/dataAMISR/xmls/'



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


def main():

    ################################ESCRIBIR BASES DE DATOS en CSV
    ###objeto base de datos
    dbObj = amisrDB.DB_AMISR(xml_path,bz2path,dataBasePath, hostname, username,
                           password, online=False)

    ###dbObj.writeDB(startdate, enddate, dataType) #escribir base de datos

    DataDB = dbObj.readDB("power",startdate,enddate) #objeto con información en Pandas DataFrame
    # """Objeto para lectura de datos de gráficos antiguos"""
    #

    #lectura de ALARMA, solo vswr, retorna data y date

    DataAlarm = dbObj.readDB("alarm",startdate,enddate,read_interval="6" ,alarmType="vswr")

    stats = STATS_AMISR(type="power", data=DataDB )
    #stats = STATS_AMISR()#contructor vacio, prueba de alarmas

    #
    # #plotObj2 = Plot_amisrDB("alarm") #antig{uo ploteo}
    #
    # """show_plot = [1, 0, 0, 0] primero solo potencia general"""




    report = Report(stats.startdate,stats.enddate)   #clase pdf report


    stats.updateNPows() # para getStatsTx y correlation
    stats.updateStatusTable()#necesario para los valores del pie, y las tablas

    fig_alarm = stats.getPlotsAlarms(DataAlarm)
    power_figure = stats.getPlotTotal("power",interval=60)
    #
    
    fig_intervals = stats.getTxIntervals()
    fig_xcorr = stats.getCrossCorrelation()
    figs_pie, values_pie = stats.getPieRep()
    fig_rate, rates = stats.getRateFig("cero", general=True)
    table_rate, rates = stats.getTableRates()

    table_over, total_pow = stats.getOverview() #ejecutar getRateFig() antes

    panel_rates=[]
    for panel in range(14):
        f, r = stats.getRateFig("cero", general=False, panel=(panel+1))
        panel_rates.append([f,r])
    
    fig_panels,labels_list = stats.getPlotPanels("power", interval=60) #una hora, y sin especificar lista para obtener todos
    

    ###stats.show()

    #
    report.print_overview(table_over, total_pow, power_figure[0])
    report.addFigure(figs_pie, "pie", values_pie)
    report.addFigure(fig_intervals, "intervals")
    report.print_rates(fig_rate, table_rate, rates)
    report.addFigure(fig_xcorr, "correlation")
    report.addFigure(fig_alarm, "alarm", None)

    for i in range(14):
        report.print_panel(fig_panels[i][0],fig_panels[i][1],panel_rates[i][0],panel_rates[i][1],labels_list[i])
    #
    # #
    report.getReport()
    #







    #ejemplo:
    '''dbObj.readDB(start_plot_date,end_plot_date,, aeuStatus = False, plot_interval=1,panel_plot_list=None,
            aeu_plot_list=None, aeus_plot_range = None, plot_interval_panel_list=None):

        retorna y_p_total, y_p_total_xml, y_panel, y_aeu, y_nInt, y_nInt_panel, x
        return aeu_alarms,alarm_date  -> aeuStatus = True
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

    main()
