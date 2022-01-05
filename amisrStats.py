import pandas as pd
import numpy as np
import datetime
import time
import os,glob,stat
import os.path

from pandas.plotting import table
import math
import matplotlib
import matplotlib.pyplot as plt
from scipy import signal

dictDataType = {"power":1, "current":2, "alarms":3, "temperature":4,
                "SSPA volts":5, "volts dir":6, "volts rev":7,
                "-8 volts":8
                }

SMALL_SIZE = 16
MEDIUM_SIZE = 18
BIGGER_SIZE = 20

class STATS_AMISR():

    labels = None
    data = None
    nAvg = 1
    rMant = None
    rate = 0
    df_tx_npows = [] #lista de dataFrames, para 0tx, 100, 200, etc para los 14 paneles pot tiempo
    data_npow = pd.DataFrame() #acumulado total para 0tx, 100, 200, etc por tiempo
    table_status_list = None
    startdate = None
    enddate = None
    
    def __init__(self,type, data, navg=1):
        self.data = pd.DataFrame(data, dtype='int32')

        dataType = dictDataType[type]
        self.work_path = os.getcwd()
        if dataType == 1:
            self.labels = pd.read_csv(self.work_path+"/labels-power.csv")
        elif dataType ==2:
            print("tipo 2")
        else:
            print("ninguno")

        self.data.columns = self.labels.columns #etiquetas para cada columna
        aux = self.data.iloc[:,0:2].astype(str) #date and time
        self.data = self.data.apply(pd.to_numeric, errors='coerce')
        self.data.iloc[:,0:2] = aux #regresa hora y fecha
        self.nAvg = navg
        self.rMant = pd.read_csv(self.work_path+"/Registro_matenimiento.csv")
        self.startdate = self.data.iloc[0,0]
        self.enddate = self.data.iloc[-1,0]



    def setCustomStylePlot(self):

        plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
        plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
        plt.rc('axes', labelsize=SMALL_SIZE)    # fontsize of the x and y labels
        plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
        plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
        plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
        plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

    def getData(self, data, index):
        return data.iloc[:,index]


    def updateStatusTable(self):
        self.hours = len(self.data)/60 #los datos están en minutos

        start_Tx = self.data.iloc[:1440,10:458] #primer dia de funcionamiento
        start_Tx = start_Tx.reset_index(drop=True)
        start_Tx = start_Tx.fillna(0)
        start_power = pd.DataFrame(start_Tx.mean(),columns=["start Watts"])
        start_power.index = self.rMant.index
        start_Tx = start_Tx.mean().astype(bool) #funcionamiento True/False
        start_Tx.name = "start Tx"
        start_Tx.index = self.rMant.index


        noTx = self.data.iloc[-1440:,10:458] #ultimo dia de funcionamiento
        #noTx.drop('index',inplace=True)
        noTx = noTx.reset_index(drop=True)
        noTx = noTx.fillna(0)
        end_power = pd.DataFrame(noTx.mean(),columns=["end Watts"])
        end_power.index = self.rMant.index
        noTx2=noTx.mean().astype(bool)
        noTx2.name = "Tx"
        noTx2.index = self.rMant.index #self.rMant

        df3 = pd.concat([self.rMant,noTx2,start_Tx,start_power,end_power],axis=1,ignore_index=False)
        df3 = df3.fillna(value=0, axis=1)

        df3.iloc[:,3:6] = df3.iloc[:,3:6].replace(to_replace=1.0, value=True)
        df3.iloc[:,3:6] = df3.iloc[:,3:6].replace(to_replace=0.0, value=False)
        self.table_status_list = df3


        self.Tx     =   df3[df3.Tx== True]
        self.noTx   =   df3[df3.Tx== False]
        self.noTxnoRep  =   self.noTx[(self.noTx.fail_Nov == 0 )  & (self.noTx.rep_bef_nov == 0 ) & (self.noTx.rep_aft_nov == 0 ) ]
        self.noTxRep    =   self.noTx[(self.noTx.fail_Nov == 1 ) | (self.noTx.rep_bef_nov == 1 ) | (self.noTx.rep_aft_nov == 1 )  ]
        self.noTxFnov   =   self.noTx[ self.noTx.fail_Nov == 1 ]
        self.noTxnoFnov =   self.noTx[self.noTx.fail_Nov == 0 ]

        self.total_power_start  =   self.table_status_list["start Watts"].sum()/1000
        self.total_power_end    =   self.table_status_list["end Watts"].sum()/1000
        #print(self.table_status_list)


    def getStatusTable(self):

        plt.close("all")
        fig_tb,ax_tb = plt.subplots(constrained_layout=True)

        plt.axis('off')
        #fig_tb.set_size_inches(5, 20)
        colors = ["#FFC0CB","#FFC0CB","#FFC0CB","#FFC0CB","#FFC0CB","#FFC0CB","#FFC0CB","#FFC0CB"]
        rcolors = ["#9ACD32" for i in range(len(df3)) ]
        df = self.table_status_list
        tbl = table(ax_tb, df, loc='center',figure =fig_tb,  colColours=colors, rowColours=rcolors)
        tbl.auto_set_font_size(True)
        #tbl.set_fontsize(10)
        fig_tb.canvas.draw()
        return fig_tb


    def getPieRep(self,show=False):
        plt.close("all")
        plt.rcdefaults() #restore default configuration

        fig1, ax1 = plt.subplots(constrained_layout=True)

        df_pie_total = pd.DataFrame({'AEU status': [len(self.Tx), len(self.noTx)]},index=['Tx', 'no Tx'])
        plot = df_pie_total.plot.pie(y='AEU status',ax=ax1, figsize=(5, 5), autopct='%.1f%%',fontsize=SMALL_SIZE)
        #print("number of AEU in TX : {} and no TX:{}  TOTAL NO TX = {}".format(len(df3Tx), len(df3noTx),len(df3Tx)+len(df3noTx)))
        plot.set_ylabel("AEU STATUS", fontdict={'fontsize':MEDIUM_SIZE})
        ax1.get_legend().remove()
        #plt.tight_layout()
        fig1.canvas.draw()

        fig2, ax2 = plt.subplots(1,2)

        df_pie = pd.DataFrame({'non working AEU': [len(self.noTxnoRep), len(self.noTxRep)]},index=['no rep ever', 'rep'])
        plot2 = df_pie.plot.pie(y='non working AEU',ax=ax2[0], figsize=(10, 5), autopct='%.1f%%',fontsize=SMALL_SIZE)
        #print("noRep EVER: {} and RepSOME:{}  TOTAL NO TX = {}".format(len(noTxnoRepEVER), len(noTxRepSOME),len(noTxnoRepEVER)+len(noTxRepSOME)))
        plot2.set_ylabel("AEU no TX", fontdict={'fontsize':MEDIUM_SIZE})


        df_pie3 = pd.DataFrame({'non working AEU': [len(self.noTxFnov ), len(self.noTxnoFnov)]},index=['failed in Nov', 'not failed in nov'])
        plot3 = df_pie3.plot.pie(y='non working AEU',ax = ax2[1], autopct='%.1f%%',fontsize=SMALL_SIZE)
        #print("non failed: {} and failed:{} in November 2020  TOTAL NO TX = {}".format(len(self.noTxFnov ), len(self.noTxnoFnov),len(self.noTxFnov)+len(self.noTxnoFnov)))
        plot3.set_ylabel("AEU no TX", fontdict={'fontsize':MEDIUM_SIZE})


        ax2[0].get_legend().remove()
        ax2[1].get_legend().remove()
        plt.tight_layout()
        fig2.canvas.draw()



        if show :
            plt.show()
        #print(self.data_npow.head())
        return [fig1,fig2], [len(self.Tx), len(self.noTx), len(self.noTxnoFnov), len(self.noTxRep),len(self.noTxFnov), len(self.noTxnoFnov)]


    def updateNPows(self):
        """
        Necesario llamarse esta función antes de getStatsTx(), getCrossCorrelation()

        """
        pd.options.mode.chained_assignment = None  # default='warn'
        data = self.data.iloc[:,458:]
        j = np.zeros(14)
        for t in range(7): #rango de etiquetas para cada panel
            off = t
            for i in range(len(j)):
                j[i] = i*7+off

            aux = self.getData(data,j)
            self.df_tx_npows.append(aux)
        df_filt = pd.DataFrame()

        for r in range(7): #por cada Label ie 0tx, 100, 200, etc
            df = self.df_tx_npows[r]
            for col in self.df_tx_npows[r]:
                try:                               #conversion a números
                    df.loc[:,col] = pd.to_numeric(df.loc[:,col], downcast='float')
                except:
                    pass
            df.fillna(0)
            self.df_tx_npows[r] = df

            m = (len(df) +1)- 60 # ventana del filtro, elegido para promediar y tener horas al final

            if m%2 == 0:
                m += 1
            df_filt = signal.medfilt(df.sum(axis=1).to_numpy(),59 ) #datos filtrados ahora en horas
            df_filt = pd.DataFrame(df_filt)
            df_filt.columns=['data_filt']
            x_hours = np.linspace(0,(len(df_filt)/60),len(df_filt))
            df_filt['hours']    =   x_hours
            col = df.columns[0][6:]
            self.data_npow[col] = df_filt['data_filt']


    def getStatsTx(self, show = False):
        plt.close("all")
        self.setCustomStylePlot()

        fig, axes = plt.subplots(7,2)
        fig.set_dpi(200)
        fig.set_size_inches(20, 25)
        fig.tight_layout(h_pad=4, w_pad=1)

        prom_days = 60*24*2  #minutos en 2 días

        for r in range(7): #por cada Label ie 0tx, 100, 200, etc
            df = self.df_tx_npows[r]

            df_s    = df[:prom_days].sum()/prom_days
            df_e    = df[-prom_days:].sum()/prom_days
            df_plt  = pd.concat([df_s,df_e-df_s],axis=1)
            df_plt.columns = ['start','inc']
            title="Power Tx {} watts".format(df_plt.index[0][6:])
            a = np.linspace(1,14,num=14)
            xlabel =[str(int(i)) for i in a]

            label_watts = df_plt.index
            df_filt = self.data_npow[label_watts[0][6:]]

            df_plt.index = xlabel
            df_plt = df_plt.apply(np.ceil)
            df_plt.plot.bar(ax=axes[r,0], grid=True,stacked=True,title=title)

            title="{} watts over hours".format(label_watts[0][6:])
            df_filt.plot(x='hours', y=label_watts[0][6:],ax=axes[r,1],grid=True,title=title)
            fig.canvas.draw()
        if show :
            plt.show()

        return fig

    def getCrossCorrelation(self, show=False):      #depende de getStatsTx()
        plt.close("all")
        plt.rcdefaults() #restore default configuration
        fig, ax = plt.subplots(constrained_layout=True)
        #fig.set_dpi(100)
        fig.set_size_inches(5, 5)
        caxes=ax.matshow(self.data_npow.corr(min_periods=100,method='kendall'),vmin=-1, vmax=1,cmap='RdBu')
        names = []
        for n in self.data_npow.columns:
            a = str(n)
            if a != '>500':
                a = a[1:]

            names.append(a)
        labels = ['']+[i for i in names]+['']
        ax.set_xticks(ax.get_xticks().tolist())
        ax.set_xticklabels(labels)
        ax.set_yticks(ax.get_yticks().tolist())
        ax.set_yticklabels(labels)

        fig.colorbar(caxes)
        if show :
            plt.show()
        fig.canvas.draw()
        return fig

    def getRate(self,dataframe):
        data = dataframe#.sum(axis=1) #suma de noTx en paneles
        n = len(data)
        h = n//60
        count=0
        acum = 0
        dataHours = pd.Series(np.zeros(h))
        data.reset_index(inplace=True, drop=True) #empieza el indice desde cero
        for index, value in data.items():
            acum += value
            if index%60==0 and index!=0:
                dataHours[count] = acum/60
                acum = 0
                count +=1

        from sklearn import linear_model
        regr = linear_model.LinearRegression()
        x = np.arange(len(dataHours)).reshape(-1, 1)
        y = dataHours.values.reshape(-1, 1)
        regr.fit(x, y)
        Y_pred = regr.predict(x)
        rate = 1/regr.coef_

        return dataHours, Y_pred, rate[0][0]

    def getRateFig(self, which):
        data, pred, rate = None, None, None
        if which=="cero":
            data, pred, rate = self.getRate(self.data_npow.iloc[:,0])
        else:
            pass
        fig, ax = plt.subplots(constrained_layout=True)
        data.plot(ax=ax)
        ax.set_xlabel("horas operadas",fontsize=18)
        ax.set_ylabel("AEU averiadas",fontsize=18)
        ax.plot(pred, color='red')
        fig.canvas.draw()

        self.rate = rate
        #print("Rate: ", rate)
        return fig, rate

    def getOverview(self):
        start = 'Start ({})'.format(self.startdate)
        end = 'End ({})'.format(self.enddate)
        columns=[start, end]
        index=pd.Index(['Power (Kw)', 'Tx','no Tx','hours','no Tx and Rep','no Tx no Rep','new damaged','rate (hours/AEU)'])

        tb_over = pd.DataFrame(columns=columns, index=index)
        tb_over.loc['Power (Kw)',start]    =   int(self.total_power_start)
        tb_over.loc['Power (Kw)',end]    =   int(self.total_power_end)
        tb_over.loc['Tx',start]    =   len(self.table_status_list[self.table_status_list["start Tx"]== True])
        tb_over.loc['Tx',end]   =     len(self.Tx)
        tb_over.loc['no Tx',start]  =   len(self.table_status_list[self.table_status_list["start Tx"]== False])
        tb_over.loc['no Tx',end]    =   len(self.noTx)
        tb_over.loc['hours',end]    =   int(self.hours)
        tb_over.loc['no Tx and Rep',end]    =   len(self.noTxRep)
        tb_over.loc['no Tx no Rep',end]    =   len(self.noTxnoRep)
        tb_over.loc['new damaged',end]    =   tb_over.loc['no Tx',end]  - tb_over.loc['no Tx',start]
        tb_over.loc['rate (hours/AEU)',end]    =   int(self.rate)

        fig, ax = plt.subplots(constrained_layout=True)
        fig.set_size_inches(5, 2)
        tb_over = tb_over.fillna(0)
        tb_over.style
        #tb_over = tb_over.reset_index()
        colors = ["#FFC0CB","#FFC0CB","#FFC0CB"]
        rcolors = ["#9ACD32" for i in range(len(tb_over)) ]

        tbl = table(ax, tb_over, loc='center',figure =fig,  colColours=colors, rowColours=rcolors,
                    fontsize=16,cellLoc='center')

        ax.axis("off")
        ax.set_title('Table 1. Overview AMISR-14',y=-0.15,fontsize=10)
        fig.canvas.draw()

        return fig, int(self.total_power_end)

    def getPanelDistribution(self):
        pass


    def print():
        pass
