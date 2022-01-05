
import datetime
import time
import os,glob,stat
import os.path

import math


import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as plticker
from matplotlib.ticker import FuncFormatter


dictDataType = {"power":1, "current":2, "alarms":3, "temperature":4,
                "SSPA volts":5, "volts dir":6, "volts rev":7,
                "-8 volts":8
                }

class Plot_amisrDB():

    DataType = 0
    plot_format = 0
    status_range = [1,448] # ragno de aeu a visualizar 1 a 448
    show_plot = [0, 0, 0, 0] # grafico total, de panel, de aeu, n_pows, intervalos de potencia
    aeus_plot_list = []
    aeus_plot_range =[] #rango de aeus, solo para funciona con -1
    panels_plot_list = []
    panel_average = False    #muestra una gŕafica adicional con la potencia promedio de los paneles
    show_plot_bar = False   #muestra barra de Gráficos en el último grafico
    plot_interval_panel_list = [] # al estar vacio se omiten los gráficos
    show_all_panel = []  #número panel
    aeus_plot_range = []

    def __init__(self,DataType,panel_average=False,aeus_plot_list=None, show_plot_bar = False):
        dataType = dictDataType[DataType]
        self.DataType = dataType
        self.show_plot_bar = show_plot_bar
        self.panel_average = panel_average
        self.aeus_plot_list = aeus_plot_list

        if dataType == 1:
            self.TitleLabel = "Power"
            self.unitLabel = "kW"
            self.YmaxT = 235.2
            self.YmaxP = 16.8
            self.YmaxAEU = 750
        elif dataType == 2:
            self.TitleLabel = "Current"
            self.unitLabel = "A"
            self.YmaxT = 1500
            self.YmaxP = 150
            self.YmaxAEU = 5
        elif dataType == 3:
            TitleLabel = "Alarms"
        elif dataType == 4:
            if temperatureType == 1:#temp SSPAs
                TitleLabel = "Temperature SSPA"
            elif temperatureType == 2:      #temp CTRL
                TitleLabel = "Temperature CTRL"
            self.unitLabel = "°C"
            self.YmaxT = 65
            self.YmaxP = 65
            self.YmaxAEU = 65
        elif dataType == 5:
            self.TitleLabel = "Volts SSPA"
            self.unitLabel = "V"
            self.YmaxT = 40
            self.YmaxP = 40
            self.YmaxAEU = 40

        elif dataType == 6:       #
            self.TitleLabel = "Volts FWD"
            self.YmaxT = 3
            self.YmaxP = 3
            self.YmaxAEU = 3
            self.unitLabel = "V"

        elif dataType == 7:
            self.TitleLabel = "Volts REV"
            self.YmaxT = 3
            self.YmaxP = 3
            self.YmaxAEU = 3
            self.unitLabel = "V"
        elif dataType == 8:
            self.TitleLabel = "-8 Volts"
            self.YmaxT = -15
            self.YmaxP = -15
            self.YmaxAEU = -15
            self.unitLabel = "V"
        else :
            print("ERROR, no Power or Current plot select")
            return
        self.titles = ["AMISR Total "+self.TitleLabel, "Panel "+self.TitleLabel, "AEU "+self.TitleLabel, "AEUs / Power Intervals", "Panel Average "+self.TitleLabel]

    def setRadarList(self,List):
        self.show_all_panel = List[0]  #número panel
        self.aeus_plot_range = List[1]

    def getPlot(self,plot_format, show_plot, y_p_total, y_p_total_xml,y_panel,y_aeu, y_nInt,y_nInt_panel, x, panels_plot_list ):


        figureList = []
        x_dates = x
        x_label = [n.strftime("%Y/%m/%d, %H:%M:%S") for n in x]

        x = mdates.date2num(x)

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
        fig1 = None

        #********************************* TOTAL ******************************************
        if show_plot[0] == 1:
            factor = 1
            fig1, ax = plt.subplots(constrained_layout=True)
            ax_2 = ax.twinx()

            if self.DataType == 1:
                y_t = [x/1000 for x in y_p_total]
                y_t_xml = [x/1000 for x in y_p_total_xml]# kilo Watts
            elif self.DataType == 2:
                y_t =  y_p_total
            if self.DataType == 4 or self.DataType == 5 or self.DataType == 6:
                y_t = [x/448 for x in y_p_total] #valores promedio(estimado)

            #print(y_t)
            if plot_format == '1':
                line, = ax.plot_date(x, y_t, fmt = '', drawstyle='default', linestyle='-'
                                                ,label = 'Radar '+self.TitleLabel+' (AEUs)')
                #ax.callbacks.connect('xlim_changed', on_xlims_change(ax,line))
                if self.DataType == 1: #solo potencia
                    ax.plot_date(x,y_t_xml,fmt = '', linestyle='-',label = 'peak '
                                                                +self.TitleLabel+' (xml)')


            elif plot_format == '2':

                ax.plot(y_t,label = 'Radar '+self.TitleLabel+' (AEUs)')

                if self.DataType == 1: #solo potencia
                    ax.plot(y_t_xml,label = 'peak '+self.TitleLabel+' (xml)')

            else:
                print("Error, plot_format invalid value...")


            plt.gca().format_coord = fmt
            #print(x,y_t)
            ax.set_xlabel('dates')
            ax.set_ylabel(self.TitleLabel+' ('+self.unitLabel+')')
            if self.DataType == 1:
                ax_2.set_ylabel('percent (%)')
                ax.axhline(y=224, color='r', linestyle='--',label = 'ideal')
            minY = min(y_t_xml)-5
            ax.set_ylim(minY, self.YmaxT) #igual a 105%
            minPerC = (minY/self.YmaxT)*105
            ax_2.set_ylim(minPerC, 105)

            ax.legend(bbox_to_anchor=(-0.02,0.2), loc="upper right", fontsize = "x-small", title = "legend")
            ax.minorticks_on()
            ax.grid()
            ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black')
            plt.title(self.titles[0], fontsize=16)
            #print(labels)
            plt.setp(ax.get_xticklabels(), rotation=40, ha='right')
            fig1.canvas.draw()
            figureList.append(fig1)

        #**************************************PANEL*************************************
        if show_plot[1] == 1 :
            panel_label_list = ["R0"+str(k[0])+"-C"+str(k[1])  for k in panels_plot_list]
            if  self.DataType==1 or self.DataType==2: #Solo en potencia y corriente interesa el total
                fig2, ax = plt.subplots(constrained_layout=True)
                ax2 = ax.twinx()
                #fig2 =  plt.figure(nf)
                l = 0
                for y in y_panel:
                    if  self.DataType==1 :
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
                if  self.DataType==1 :
                    ax2.set_ylabel('percent (%)')
                    ax2.set_ylim(0,105)
                    ax.axhline(y=16, color='r', linestyle='--',label = 'ideal')
                plt.gca().format_coord = fmt
                ax.set_xlabel('dates')
                ax.set_ylabel(self.TitleLabel+'('+self.unitLabel+')')
                minY = min(min(y_panel))/1000 - 1
                ax.set_ylim(minY, self.YmaxP)# 16.8 = 105%
                #print(minY, self.YmaxP)
                ax.legend(bbox_to_anchor=(-0.06,1), loc="upper right", fontsize = "x-small", title = "legend")
                ax.grid()
                ax.grid(which='minor', linestyle=':', linewidth='0.5', color='black')
                plt.title(self.titles[1], fontsize=16)
                plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
                fig2.canvas.draw()
                figureList.append(fig2)

            if self.panel_average: # grafica para la potencia promedio, amperaje, y solo Temperatura
                fig2_a, ax_a = plt.subplots(constrained_layout=True)
                ax2_a = ax_a.twinx()
                if self.DataType ==1:
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

                if self.DataType == 1:
                    ax_a.axhline(y=500, color='r', linestyle='--',label = 'ideal')
                ax_a.set_xlabel('dates')
                ax_a.set_ylabel(self.TitleLabel+'('+self.unitLabel+')')
                plt.gca().format_coord = fmt

                #minY = min(min(y_panel))/32000 - 1
                ax_a.set_ylim(200, 550) #igual a 105%

                ax_a.legend(bbox_to_anchor=(-0.06,1), loc="upper right", fontsize = "x-small", title = "legend")
                ax_a.grid()
                ax_a.grid(which='minor', linestyle=':', linewidth='0.5', color='black')
                plt.title(self.titles[4], fontsize=16)
                plt.setp(ax_a.get_xticklabels(), rotation=30, ha='right')
                fig2_a.canvas.draw()
                figureList.append(fig2_a)

        #**************************************AEU*************************************
        if show_plot[2] == 1:
            aeu_label_list = []
            for k in self.aeus_plot_list:
                r = k[0]
                c = k[1]
                n = k[2]

                if len(self.show_all_panel) > 0:

                    for R,C in self.show_all_panel:
                        if r == R and c == C:
                            for i in range(self.aeus_plot_range[0], self.aeus_plot_range[1]+1):
                                aeu_label_list.append("R0"+str(r)+"-C"+str(c)+" #"+str(i))
                        else:
                            aeu_label_list.append("R0"+str(r)+"-C"+str(c)+" #"+str(n))
                else:
                    aeu_label_list.append("R0"+str(r)+"-C"+str(c)+" #"+str(n))
            #print(aeu_label_list)
            fig3 =  plt.figure(constrained_layout=True)
            l = 0
            arrayToPd = []
            for y in y_aeu:

                plt.plot_date(x,y,fmt = ' ',linestyle='-',label = aeu_label_list[l])
                l += 1

            if self.DataType == 1:
                plt.axhline(y=500, color='r', linestyle='--',label = 'ideal')
            plt.xlabel('dates')
            plt.xticks(rotation=30)
            plt.minorticks_on()
            plt.grid(which='minor', color='#444444', linestyle='-', alpha=0.2)
            plt.title(self.titles[2], fontsize=16)
            plt.ylim(0, self.YmaxAEU)
            plt.ylabel(self.TitleLabel+ '('+self.unitLabel+')')
            plt.legend(bbox_to_anchor=(-0.06,1), loc="upper right", fontsize = "x-small", title = "legend")
            fig3.canvas.draw()
            figureList.append(fig3)

        #**************************************INTERVAL POWER*************************************
        if show_plot[3] == 1:
            label_list = ["0", "0 to 100", "100 to 200", " 200 to 300", "300 to 400", "400 to 500", ">500"]
            fig4, ax1 = plt.subplots(2,1,constrained_layout=True)
            ax2 = ax1[0].twinx()
            #print(y_nInt[0])
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
            plt.title(self.titles[3], fontsize=16)
            plt.setp(ax1[0].get_xticklabels(), rotation=30, ha='right')

            n_plots_i = len(plot_pow_list)

            i_j = 0
            l_colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
            figureList.append(fig4)
            for panel in plot_pow_list:
                y_u = y_nInt_panel[panel-1]
                #print("Power 0: ",panel, y_u[0])
                l = 0
                rf, cf = plot_interval_panel_list[i_j]
                # # s = sum( n[0] for n in y_u)
                # # print("suma:", s)     #acumulado de 32 por panel
                # print(s,t)
                fig = plt.figure()
                for y in y_u: #cada nivel de potencia
                    line, = plt.plot_date(x,y,fmt = '',color=l_colors[l],linestyle='-',label = label_list[l])
                    l += 1
                plt.legend(bbox_to_anchor=(-0.05,1), loc="upper right", fontsize = "x-small", title = "legend")
                plt.grid()
                plt.ylabel('# AEUs')
                plt.title('AEUs per power Interval Panel R'+ str(rf)+"-C"+str(cf))
                plt.xticks(rotation=60)
                i_j += 1
                fig.canvas.draw()
                figureList.append(fig)

        return figureList
        #**************************************STATUS DAYs (ALARMAS)*************************************
        ## para cada valor de alarma se asigna un colorbar
        ## 0= OK, 1 = TEMP, 2= VSWR, 3 = SUMMARY ()


    def getPlotsAlarms(self,aeu_alarms,alarm_date,maxAEU,minAEU):

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

        fig_s.canvas.draw()
        return fig_s



    def show(self):
        plt.show()

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
