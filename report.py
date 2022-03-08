from fpdf import FPDF,HTMLMixin
from PIL import Image
import numpy as np
import os
import datetime
from utils import *

class PDF(FPDF, HTMLMixin):
    def footer(self):
        # Position cursor at 1.0 cm from bottom:
        self.set_y(-10)
        # Setting font: helvetica italic 8
        self.set_font("helvetica", "I", 8)
        # Printing page number:
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")


fig_type={
"interval":0, "correlation":1, "pie": 2, "alarm":3,"general":4
}
table_type={
"aeu_list":0,"aeu_reps":1
}
text_stats ="""<font size="12"><p>The following graph shows the variation in the amount
of AEU transmitting in a power interval, which goes from the value shown in the title
to the previous lower value, except for level 0 and greater than 500 watts; these amounts and
variations are presented with the panels involved. The graphs on the right show the
total amount of AEU in said interval with its evolution over time (hours)</p>"""

text_correlation = """<font size="12"><p>The correlation graph between the power
intervals shows the AEU exchange between different power levels, that is, it is
possible to know which power levels are more likely to increase others. For the
particular interest of AMISR-14, it is observed that the faulty AEUs (= 0 watts)
come from the power ranges with the lowest correlation, that is, those closest
to -1.  </p>"""

text_pie="""<font size="12"><p>Since the AMISR power loss was noticed, repairs were
started following the manufacturer's guidelines, part of these and the main reason
for the power loss is the failure of the Q3 driver (BL6G10-45), which is very sensitive
to the negative voltages on its gate ( < -0.5v). Along with the repairs to these drivers,
improvements were made to the amplification board as protection measures to avoid further
losses. Despite this, and the reduction of the input power level in the AEUs, losses of
the Q3 drivers have still been observed in the radar AEUs.\n
The number of failures in these drivers increased sharply during an isolated event in
November 2020, while testing of the repairs was being conducted. It was noted that it
was something that affected the entire radar, but only a few AEUs were damaged.</p>"""

text_overview = """<font size="12"><p>The Umet-JRO AMISR-14 radar, located at the Jicamarca
Radio Observatory is a radar composed of an array of phased antennas designed by SRI
International and used mainly for ionospheric studies.
This new radar allows us a better understanding of ionospheric phenomena, mostly
coherent dispersion, such as equatorial electrojet and Equatorial Spread F.
It started operations in August 2014 being used mainly for campaigns specific, but
since October 2015 it has been used constantly in conjunction with the JULIA operation
of the main radar of the Jicamarca Radio Observatory.
The radar operates at the frequency of 445MHz, although it can operate at frequencies from
430MHz to 450MHz, with a current peak power of {} kW and with a maximum duty cycle 10%
with a maximum transmit pulse width of 2ms. One of its characteristics main is its ability
to change the aim electronically, pulse to pulse, which allows you to gives the ability
to create high resolution time images of the phenomenon to be studied.
The antenna array has been oriented North-South to obtain a greater pointing width
in the East-West direction.\n The following graphs show the performance of the radar since
{} to {}</p>"""
text_alarm_one="""<font size=12></p>The following graph shows the VSWR alarms produced during
the operation of AMISR in the selected period; the VSWR alarm maight have been asociated to the failure
in the AMISR Antenna Element Units (AEU), since during the event in november 2020, the radar
showed multiple alarms simultaneously in all panels.
</p>
"""
text_fail_rate1="""<font size=12></p>The failure rate of the AMISR-14 radar throughout the hours
operated is graphed in the following figure, likewise there is a linear adjustment to the number
of failures, from that curve the rate has been calculated. The failure rate has units of AEU/h which is
a small number, so the hours/AEU has been displayed in the overview box instead.
</p>
"""
text_fail_rate2="""<font size=12></p>The following table shows the failure rate for each panel. These
numbers are higher than the general rate because the number of failures is lower if only one panel is
considered. However, if the amounts are added inversely, the same value would be obtained. than the
inverse of the general rate. The table is mainly referential, to see the behavior of each panel, a low
quantity indicates the panel has a higher failure rate.
</p>
"""
class Report():

    pdf = None
    start_date = ""
    end_date = ""
    img = None
    username = "Joab Apaza"

    def __init__(self, start, end, username=username):
        self.work_path = os.getcwd()
        self.path_amisr_img = self.work_path+"/images/AMISR_rain.png"
        self.username = username
        self.pdf    =   PDF('P', 'mm', 'A4')
        self.start_date =   start
        self.end_date   =   end
        self.datetime_start = start
        self.datetime_end = end

        self.pdf.set_font("Times", size=38)
        self.pdf.add_page()
        self.pdf.set_xy(10,50)
        self.pdf.cell(0,10,txt="AMISR OPERATION REPORT",ln=1,align='R')
        self.pdf.set_font("Times", size=20)
        a = self.datetime_start
        b = self.datetime_end
        text = ""
        if a.year == b.year:
            text = "from {} {} to {} {} of {}".format(a.strftime("%B"), a.day, b.strftime("%B"), b.day, b.year)
        else:
            text = "from {} {} of {} to {} {} of {}".format(a.strftime("%B"), a.day,a.year, b.strftime("%B"), b.day, b.year)
        self.pdf.set_font("Courier", style='I', size=18)
        self.pdf.cell(0,10,txt=text,ln=1,align='R')

        self.pdf.set_font("Times", size=20)
        self.pdf.cell(0,10,txt="Jicamarca Radio Observatory",ln=1,align='R')

        self.pdf.set_font("Times", size=10)
        aux_text    = "Elaborated by: {}".format(self.username)
        self.pdf.cell(0,5,txt=aux_text,align='R')

        self.pdf.image(self.path_amisr_img, x=20, y=80)


        pass

    def addFigure(self, figure, type, values = None, subtype=None):
        type = fig_type[type]
        if type == 0:
            self.add_intervals(figure)
            pass
        elif type == 1:
            self.add_correlation(figure)
            pass
        elif type == 2:
            self.add_pie(figure, values)
            pass
        elif type == 3:
            self.add_alarm(figure, values)
            pass
        elif type == 4:
            pass
        else:
            self.add_general(figure)
            return
        pass

    def add_intervals(self,figure):
        print("creating stats image...")
        self.pdf.add_page()
        self.pdf.set_font("Times", "B", size=18)
        text = "AMISR by power output intervals"
        self.pdf.cell(10, 10, text, ln=1, align='L')
        self.pdf.write_html(text_stats)


        data = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', figure.canvas.get_width_height(),data)

        self.pdf.image(img, x=10, y=60, h=3.4*(self.pdf.eph/4), w=3.8*(self.pdf.epw)/4)

        return

    def add_correlation(self,figure):
        self.pdf.add_page()
        self.pdf.set_font("Times", "B", size=18)
        text = "Cross correlation between power output intervals"
        self.pdf.cell(10, 10, text, ln=1, align='L')
        self.pdf.write_html(text_correlation)
        data = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', figure.canvas.get_width_height(),data)
        self.pdf.image(img, x=60, y=65, h=100, w=100)
        text="""<font size="12"><p>The previous figure is symmetrical with respect to its diagonal, based
on the repairs carried out on the radar, it has been observed that AEUs that drop to half their power, or
between 100 to 300 watts correspond in most cases to the fault of the Q1 and Q2 preamps (shown in the
following figure)</p>"""
        self.pdf.set_xy(10,170)
        self.pdf.write_html(text)
        path = self.work_path+"/images/AMISR_SSPA.jpg"
        self.pdf.image(path, x=30, y=200, h=80, w=150)

    def add_pie(self, figures, values):
        self.pdf.add_page()
        self.pdf.set_font("Times", "B", size=16)
        text = "Repairment Status AMISR-14"
        self.pdf.cell(10, 10, text, ln=1, align='L')
        #text_pie = text_pie.format()
        self.pdf.write_html(text_pie)
        ##[len(df3Tx), len(df3noTx), len(noTxnoRepEVER), len(noTxRepSOME),len(noTx_FNOV), len(noTx_noFNOV)
        data1 = np.fromstring(figures[0].canvas.tostring_rgb(), dtype=np.uint8, sep='')

        t = 100.0/(values[0]+values[1])

        self.pdf.set_font_size(size=12)
        img1 = Image.frombytes('RGB', figures[0].canvas.get_width_height(),data1)
        text1 = """<font size="12"><p>This figure shows the number of working AEU: {} ({:.1f}%) vs the non working:
{} ({:.1f}%) until {}.</p>""".format(values[0],values[0]*t,values[1],values[1]*t,self.end_date)

        #self.pdf.set_xy(40)
        self.pdf.image(img1, x=70,y=90, h=80, w=80)
        self.pdf.set_xy(10,80)
        self.pdf.write_html(text1)


        t1 = 100.0/(values[2]+values[3])# reps
        t2 = 100.0/(values[4]+values[5])# failNov
        text2 = """<font size="12"><p>This figures show in the left the number of AEU repaired at least once: {}
({:.1f}%) vs no repaired ever {} ({:.1f}%), and in the right shows those that failed {} ({:.1f}%) vs the not
failed  {} ({:.1f}%) AEU depending of the failure in November 20.</p>""".format(values[2],values[2]*t1,values[3],
                        values[3]*t1,values[4],values[4]*t2,values[5],values[5]*t2)

        data2 = np.fromstring(figures[1].canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img2 = Image.frombytes('RGB', figures[1].canvas.get_width_height(),data2)
        self.pdf.image(img2, x=30, y=190, h=80, w=160)
        self.pdf.set_xy(10,170)
        self.pdf.write_html(text2)

    def print_overview(self,table, power, power_figure):
        self.pdf.add_page()
        self.pdf.set_font("Times", "B", size=18)
        text = "Overview of AMISR-14 working status"
        self.pdf.cell(10, 10, text, ln=1, align='L')
        text = text_overview.format(power,self.start_date, self.end_date)
        self.pdf.write_html(text)

        data = np.fromstring(table.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', table.canvas.get_width_height(),data)
        self.pdf.image(img, x=60, y=105, h=60, w=90)

        data = np.fromstring(power_figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', power_figure.canvas.get_width_height(),data)
        self.pdf.image(img, x=10, y=190, h=90, w=180)

        self.pdf.set_xy(10,170)
        text = """<font size="12"><p>For power calculations, the sum of the registered power of all AEUs
is taken into account, this varies with the power that the radar observes. This can be seen in the
following graph, where the blue line is the one obtained by adding all the AEUs.</p>"""
        self.pdf.write_html(text)

    def add_alarm(self,figure, values):
        self.pdf.add_page()
        self.pdf.set_font("Times", "B", size=18)
        text = "VSWR Alarms"
        self.pdf.cell(10, 10, text, ln=1, align='L')

        self.pdf.write_html(text_alarm_one)

        data = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', figure.canvas.get_width_height(),data)
        self.pdf.image(img, x=30, y=50, h=120, w=180)

        figure2 = values
        data = np.fromstring(figure2.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', figure2.canvas.get_width_height(),data)
        self.pdf.image(img, x=50, y=180, h=80, w=120)

    def print_rates(self, fig_rate, table_rate, rates):
        self.pdf.add_page()
        self.pdf.set_font("Times", "B", size=18)
        text = "AMISR fail rates"
        self.pdf.cell(10, 10, text, ln=1, align='L')

        self.pdf.set_xy(10,20)
        self.pdf.write_html(text_fail_rate1)
        figure = fig_rate
        data = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', figure.canvas.get_width_height(),data)
        self.pdf.image(img, x=40, y=60, h=self.pdf.eph/3, w=self.pdf.epw/1.5)


        self.pdf.set_xy(10,160)
        self.pdf.write_html(text_fail_rate2)
        figure = table_rate
        data = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', figure.canvas.get_width_height(),data)
        self.pdf.image(img, x=10, y=185, h=40, w=self.pdf.epw/1.1)

    def print_panel(self, fig_total, fig_aeu, fig_rate, rate, label ):

        self.pdf.add_page()
        self.pdf.set_font("Times", "B", size=18)
        text = "Panel {} power transmited and rate".format(label)
        self.pdf.cell(10, 10, text, ln=1, align='L')

        self.pdf.set_xy(10,20)
        if rate == 0:
            new_rate=0
        else:
            new_rate = 1/rate
        text="""<font size="12"><p>The following figures shows the transmitting average power of
panel {} and its fail rate with equal to {:.5f} AEU/hour.</p>""".format(label,new_rate)
        self.pdf.write_html(text)
        figure = fig_total
        data = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', figure.canvas.get_width_height(),data)
        self.pdf.image(img, x=20, y=60, h=80, w=80)

        figure = fig_rate
        data = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', figure.canvas.get_width_height(),data)
        self.pdf.image(img, x=110, y=60, h=72, w=80)

        self.pdf.set_xy(10,160)
        text="""<font size="12"><p>A general view of the power of the panel {} for each AEU is
shown in the graph bellow:</p>""".format(label)
        self.pdf.write_html(text)
        figure = fig_aeu
        data = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
        img = Image.frombytes('RGB', figure.canvas.get_width_height(),data)
        self.pdf.image(img, x=20, y=180, h=100, w=150)

    def print_panel_detail(self, panel_text):
        self.pdf.add_page(orientation='L')
        self.pdf.set_font("Times", "B", size=18)
        text = "Panel repairments and status list"
        self.pdf.cell(10, 10, text, ln=1, align='L')


        self.pdf.set_xy(10,15)
        text = panel_text
        text= text.replace("<th ","<th width=20 ")
        #print(text)
        self.pdf.set_font("Times", size=10)
        self.pdf.write_html(text)


    def getReport(self):
        self.pdf.output("pdf-amisr-report.pdf")
        return
