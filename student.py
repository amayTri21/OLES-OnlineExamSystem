import base64
import io
import sys
import mysql.connector
from mysql.connector import Error
from PIL import Image
#from PIL.ImageQt import ImageQt
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
import socket,cv2, pickle,struct
import numpy as np
#import face_recognition
import time
from gaze_tracking import GazeTracking
import keyboard
import random
from fpdf import FPDF
#import matplotlib.pyplot as plt

connection = mysql.connector.connect(host='localhost', database='OnlineExamSystem', user='root', password='', port='3306')
cursor = connection.cursor(buffered=True)
#motion detection
frameCount = 0
fgbg = cv2.createBackgroundSubtractorMOG2(300, 400, True)
#gaze tracking
gaze = GazeTracking()
examQuesTablename = ()
checkedans = {'0':None}

class Login(QDialog):
    def __init__(self,master):
        self.master = master
        super(Login,self).__init__()
        loadUi("login.ui",self)
        self.setWindowTitle("OLES - Online Exam System")
        self.signframe.setVisible(False)
        self.rollno_3.setVisible(False)
        self.loginbtn.clicked.connect(self.loginFunction)
        self.blur()
        self.accountbtn.clicked.connect(self.createAccount)
        self.accountbtn_2.clicked.connect(self.loginAccount)
        self.photobtn.clicked.connect(self.getfile)
        self.signbtn.clicked.connect(self.signUp)

        reg_ex = QRegExp("[0-9]+.?[0-9]{,2}")
        input_validator = QRegExpValidator(reg_ex, self.rollno)
        self.rollno.setValidator(input_validator)      

    def loginFunction(self):
        self.rollNo = self.rollno.text()
        password = self.password.text()
        type = self.typeCombo.currentText();      

        sql = "select * from user where rollno = %s and password = %s and type = %s"
        values = (self.rollNo,password,type)
        cursor.execute(sql,values)
        result = cursor.fetchall()
        if result:            
            for x in result:
                mainwindow = Application(self.rollNo)
                widgets.addWidget(mainwindow)
                widgets.setCurrentIndex(widgets.currentIndex()+1)
        else:
            print("Login failed")

    def createAccount(self):
        self.loginframe.setVisible(False)
        self.signframe.setVisible(True)

    def loginAccount(self):
        self.signframe.setVisible(False)
        self.loginframe.setVisible(True)
        
    def blur(self):	
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(30) 
        self.blurlbl.setGraphicsEffect(self.blur_effect)

    def getfile(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file','c:\\',"Image files (*.jpg *.png)",options=QFileDialog.DontUseNativeDialog)
        self.photolbl.setPixmap(QPixmap(fname))
        self.rollno_3.setText(fname)

    def connectDB(self):
        try:
            connection = mysql.connector.connect(host='sql12.freesqldatabase.com',database='sql12394903',user='sql12394903',password='WNRjtUUQWr',port='3306')
            mySql_Create_Table_Query = """SELECT * FROM user"""
            cursor = connection.cursor()
            cursor.execute(mySql_Create_Table_Query)
            result = cursor.fetchall()
            for x in result:
                print(x)

        except mysql.connector.Error as error:
            print("Failed to create table in MySQL: {}".format(error))

        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("MySQL connection is closed")

    def signUp(self):
        name = self.name.text()
        rollno = self.rollno_2.text()
        email = self.email.text()
        password = self.password_2.text()
        confirmPass = self.password_3.text()
        type = self.typeCombo_2.currentText()

        with open (self.rollno_3.text(),"rb") as File:
            BinaryData = File.read()

        sql = "insert into user (rollno,name,email,type,password,photo) values (%s,%s,%s,%s,%s,%s)"
        value = (rollno,name,email,type,password,BinaryData)

        if (rollno.isdigit() == False):
            m = QMessageBox.about(self, "warning", "Please Enter a Roll Number in Digits")

        elif (len(rollno) < 7):
            m = QMessageBox.about(self, "warning", "Please Enter a Roll Number of Length 7 Digits")

        elif (len(password)<8):
            m = QMessageBox.about(self, "warning", "Please Enter a Strong Password")

        elif (confirmPass != password):
            m = QMessageBox.about(self, "warning", "Please Enter Correct Password")

        elif (name == '' or email == '' or password == '' or rollno == '' or self.rollno_3.text() == ''):
            m = QMessageBox.about(self, "warning", "Please fill all the data")

        else:
            cursor.execute(sql,value)
            connection.commit()
            m = QMessageBox.about(self, "SUCCESS!", "ACCOUNT CREATED!")


class Application(QMainWindow,Login):
    def __init__(self,rollNo):
        super(Application,self).__init__(rollNo)
        loadUi("application.ui",self)
        self.setWindowTitle("OLES - Online Exam System")
        self.blur()
        self.userrollno.setText(rollNo)
        self.setUserInfo()
        self.resultsframe.setVisible(False)
        self.teacherdashboardframe.setVisible(False)
        self.createframe.setVisible(False)
        self.adduserframe.setVisible(False)
        self.settingsframe.setVisible(False)
        self.feedbackframe.setVisible(False)
        self.adduserbtn.setVisible(False)
        self.createexambtn.setVisible(False)
        self.dashboardbtn.clicked.connect(self.showDashboard)
        self.resultsbtn.clicked.connect(self.showResults)
        self.settingsbtn.clicked.connect(self.showSettings)
        self.createexambtn.clicked.connect(self.showCreate)
        self.adduserbtn.clicked.connect(self.showAddUser)
        self.feedbackbtn.clicked.connect(self.showFeedback)  
        self.startexambtn.clicked.connect(self.startExam)  
        self.createnewexambtn.clicked.connect(self.createNewExam)   
        self.refreshbtn.clicked.connect(self.setCreatedExams) 
        self.addquesframe.setVisible(False)
        self.addquesbtn.clicked.connect(self.showAddQuesPanel)
        self.printresultbtn.clicked.connect(self.printResult)

    def blur(self):	
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(30) 
        self.blurlbl.setGraphicsEffect(self.blur_effect)

    def setUserInfo(self):
        sql = "select * from user where rollno = %s"
        values = (self.userrollno.text(),)
        cursor.execute(sql,values)
        myresult = cursor.fetchone()
        StoreFilepath = "img/image.jpg"
        with open(StoreFilepath, "wb") as file:
            file.write(myresult[6])
            file.close()
        self.userphoto.setPixmap(QPixmap("img/image.jpg"))
        self.username.setText(myresult[2])
        self.usertype.setText(myresult[4])

    def setBtnBG(self,QLabel,QPushButton,Image):
        QLabel.setStyleSheet("background:#691A7F; border-radius:10px")
        QPushButton.setStyleSheet("color:white; text-align:left; padding-left:20px;")
        QPushButton.setIcon(Image)

    def showDashboard(self):
        self.dashboardframe.setVisible(True)
        self.resultsframe.setVisible(False)
        self.feedbackframe.setVisible(False)
        self.createframe.setVisible(False)
        self.adduserframe.setVisible(False)
        self.settingsframe.setVisible(False)
        self.currentExamsData()
        self.setBtnBG(self.dashboardbtnlbl,self.dashboardbtn,QtGui.QIcon('img/dashboard-white.png'))

    def showResults(self):
        self.dashboardframe.setVisible(False)
        self.resultsframe.setVisible(True)
        self.createframe.setVisible(False)
        self.adduserframe.setVisible(False)
        self.settingsframe.setVisible(False)
        self.feedbackframe.setVisible(False)
        self.showResultsTable()
        

    def showFeedback(self):
        self.dashboardframe.setVisible(False)
        self.resultsframe.setVisible(False)
        self.createframe.setVisible(False)
        self.adduserframe.setVisible(False)
        self.settingsframe.setVisible(False)
        self.feedbackframe.setVisible(True)

    def showSettings(self):
        self.dashboardframe.setVisible(False)
        self.resultsframe.setVisible(False)
        self.createframe.setVisible(False)
        self.adduserframe.setVisible(False)
        self.settingsframe.setVisible(True)
        self.feedbackframe.setVisible(False)

    def showCreate(self):
        self.dashboardframe.setVisible(False)
        self.resultsframe.setVisible(False)
        self.createframe.setVisible(True)
        self.adduserframe.setVisible(False)
        self.settingsframe.setVisible(False)
        self.feedbackframe.setVisible(False)
        self.setCreatedExams()

    def showAddUser(self):
        self.dashboardframe.setVisible(False)
        self.resultsframe.setVisible(False)
        self.createframe.setVisible(False)
        self.adduserframe.setVisible(True)
        self.settingsframe.setVisible(False)
        self.feedbackframe.setVisible(False)

    def currentExamsData(self):
        cursor.execute("SELECT srno,name,DATE_FORMAT(date,\"%d-%m-%Y\")AS Date,starttime,endtime,type,dept,totalmarks FROM exams where date >= current_date and date < current_date + interval 1 day")
        result = cursor.fetchall()
        self.currentexams.setRowCount(0)
        for row_number, row_data in enumerate(result):
            self.currentexams.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.currentexams.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        self.currentexams.setSelectionBehavior(QTableView.SelectRows)


        cursor.execute("SELECT srno,name,DATE_FORMAT(date,\"%d-%m-%Y\")AS Date,starttime,endtime,type,dept,totalmarks FROM exams where date > current_date")
        result = cursor.fetchall()
        self.upcomingexams.setRowCount(0)
        for row_number, row_data in enumerate(result):
            self.upcomingexams.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.upcomingexams.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        self.upcomingexams.setSelectionBehavior(QTableView.SelectRows)


    def startExam(self):
        global examQuesTablename
        rows = sorted(set(index.row() for index in self.currentexams.selectedIndexes()))
        for row in rows:
            examQuesTablename = (self.currentexams.model().data(self.currentexams.model().index(row, 0)),self.currentexams.model().data(self.currentexams.model().index(row, 1)),self.currentexams.model().data(self.currentexams.model().index(row, 5)),self.currentexams.model().data(self.currentexams.model().index(row, 6)),self.currentexams.model().data(self.currentexams.model().index(row, 2)),self.currentexams.model().data(self.currentexams.model().index(row, 3)),self.currentexams.model().data(self.currentexams.model().index(row, 4))) 
        print("examQuesTablename -",examQuesTablename)

        self.rollNo = self.userrollno.text()
        examwindow = Exam(self.rollNo)            
        widgets.addWidget(examwindow)
        widgets.setCurrentIndex(widgets.currentIndex()+1)
        widgets.showFullScreen()        

    def getExamQuesTablename(self):
        global examQuesTablename 
        return examQuesTablename 

    def createNewExam(self):
        examname = self.nameofexamlbl.text()
        examtype = self.examtypelbl.text()
        totalmarks = self.totalmarkslbl.text()
        examdate = self.dateEdit.date().toString(Qt.ISODate)
        starttime = self.timeEdit.time().toString(Qt.ISODate)
        endtime = self.timeEdit_2.time().toString(Qt.ISODate)
        department = self.deptlbl.text()

        print("date- ",examdate)
        print("starttime- ",starttime)
        print("endtime- ",endtime)

        sql = "insert into exams(name,date,starttime,endtime,type,totalmarks,dept) values(%s,%s,%s,%s,%s,%s,%s)"
        values =(examname,examdate,starttime,endtime,examtype,totalmarks,department)
        cursor.execute(sql,values)

        sql1 = "select srno from exams where name = %s and date = %s and starttime = %s and endtime = %s and type = %s and totalmarks = %s and dept = %s"
        values1 =(examname,examdate,starttime,endtime,examtype,totalmarks,department)
        cursor.execute(sql1,values1)
        myresult = cursor.fetchone()

        examQuesTablename = str(myresult[0])+examname+examtype+department;
        sql2 = "CREATE TABLE {} ( `quesNo` VARCHAR(20) NOT NULL ,`shuffledNo` VARCHAR(20) NULL , `question` LONGBLOB NOT NULL , `type` VARCHAR(255) NOT NULL , `option1` VARCHAR(255) NULL , `option2` VARCHAR(255) NULL , `option3` VARCHAR(255) NULL , `option4` VARCHAR(255) NULL , `option5` VARCHAR(255) NULL ,`marks` VARCHAR(20) NOT NULL , `correctAns` VARCHAR(255) NOT NULL , PRIMARY KEY (`quesNo`))".format(examQuesTablename)
        cursor.execute(sql2)

    def setCreatedExams(self):
        cursor.execute("SELECT srno,name,DATE_FORMAT(date,\"%d-%m-%Y\")AS Date,starttime,endtime,type,dept,totalmarks FROM exams ")
        result = cursor.fetchall()
        self.createdexams.setRowCount(0)
        for row_number, row_data in enumerate(result):
            self.createdexams.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.createdexams.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        self.createdexams.setSelectionBehavior(QTableView.SelectRows);
        self.createdexams.clicked.connect(self.selectCreatedExam)

    def selectCreatedExam(self):
        rows = sorted(set(index.row() for index in self.createdexams.selectedIndexes()))
        for row in rows:
            self.examidlbl.setText(self.createdexams.model().data(self.createdexams.model().index(row, 0)))
            self.examnamelbl.setText(self.createdexams.model().data(self.createdexams.model().index(row, 1)))
            self.examtypelbl_2.setText(self.createdexams.model().data(self.createdexams.model().index(row, 5)))
            self.deptlbl_2.setText(self.createdexams.model().data(self.createdexams.model().index(row, 6)))

    def showAddQuesPanel(self):
        self.createframe_2.setVisible(False)
        self.createframe_3.setVisible(False)
        self.addquesframe.setVisible(True)
        self.quesphotobtn.clicked.connect(self.getquesphoto)
        self.addansbtn.clicked.connect(self.addAnstoCreatedExam)
        self.quesphotoaddresslbl.setVisible(False)
        self.quesconfirmbtn.clicked.connect(self.addQuestoCreatedExam)
        self.addquesexitbtn.clicked.connect(self.exitAddQuesPanel)

    def getquesphoto(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file','c:\\',"Image files (*.jpg *.png)",options=QFileDialog.DontUseNativeDialog)
        self.quesphotolbl.setPixmap(QPixmap(fname))
        self.quesphotoaddresslbl.setText(fname)

    def addAnstoCreatedExam(self):
        lineedit = QLineEdit()
        lineedit.setFixedHeight(50)
        lineedit.setFixedWidth(780)
        lineedit.setFont(QFont('', 14))
        lineedit.setStyleSheet("background: rgba(255,255,255,0.6); border:none; border-radius:5px;")
        lineedit.setPlaceholderText("      Type your answer")
        self.verticalLayoutAns.addWidget(lineedit) 

    def addQuestoCreatedExam(self):
        examQuesTablename = self.examidlbl.text()+self.examnamelbl.text()+self.examtypelbl_2.text()+self.deptlbl_2.text()
        quesno = self.quesnolbl.text()
        with open (self.quesphotoaddresslbl.text(),"rb") as File:
            BinaryData = File.read()
        questype = self.questypebox.currentText()
        marks = self.quesmarkslbl.text()
        correctans = self.correctanslbl.text()
        widgets = (self.verticalLayoutAns.itemAt(i).widget() for i in range(self.verticalLayoutAns.count())) 
        answers = ()
        for widget in widgets:
            if isinstance(widget, QLineEdit):
                answers = answers + (widget.text(),)
        print("Answers - ",answers)
        if(len(answers)<5):
            for i in range(len(answers),5):
                answers = answers + ("",)
        print("Answers - ",answers)
        sql = "insert into {}(quesNo,question,type,option1,option2,option3,option4,option5,marks,correctAns) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(examQuesTablename.lower())
        print(sql)
        value = (quesno,BinaryData,questype,answers[0],answers[1],answers[2],answers[3],answers[4],marks,correctans)        
        cursor.execute(sql,value)
        connection.commit()
        quesno = str(int(quesno)+1)
        self.quesnolbl.setText(quesno)
        self.quesphotolbl.setPixmap(QPixmap())
        self.quesmarkslbl.setText("")
        self.correctanslbl.setText("")
        for i in reversed(range(self.verticalLayoutAns.count())): 
            self.verticalLayoutAns.removeWidget(self.verticalLayoutAns.itemAt(i).widget())

    def exitAddQuesPanel(self):
        self.createframe_2.setVisible(True)
        self.createframe_3.setVisible(True)
        self.addquesframe.setVisible(False)
        self.examtypelbl.setText("")
        self.deptlbl.setText("")
        self.nameofexamlbl.setText("")
        self.totalmarkslbl.setText("")

    def showResultsTable(self):
        cursor.execute("SELECT srno,name,type,dept FROM exams")
        result = cursor.fetchall()
        self.resultexams.setRowCount(0)
        for row_number, row_data in enumerate(result):
            sql = "SELECT * FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'onlineexamsystem' AND TABLE_NAME = '{}' AND COLUMN_NAME = '{}'".format(str(result[row_number][0])+str(result[row_number][1]).lower()+str(result[row_number][2]).lower()+str(result[row_number][3]).lower(), "marked"+self.userrollno.text())
            cursor.execute(sql)
            existexam = cursor.fetchall()
            if existexam:
                sql1 ="SELECT srno,name,DATE_FORMAT(date,\"%d-%m-%Y\")AS Date,starttime,endtime,type,dept,totalmarks FROM exams where srno = {}".format(str(result[row_number][0]))
                cursor.execute(sql1)
                examdata = cursor.fetchall()
                for row_number, row_data in enumerate(examdata):
                    self.resultexams.insertRow(row_number)
                    for column_number, data in enumerate(row_data):
                        self.resultexams.setItem(row_number, column_number, QTableWidgetItem(str(data)))
            connection.commit()
        self.resultexams.setSelectionBehavior(QTableView.SelectRows)

    def printResult(self):      
        rows = sorted(set(index.row() for index in self.resultexams.selectedIndexes()))
        examid = ""
        examname = ""
        examtype = ""
        department = ""
        for row in rows:
            examid = self.resultexams.model().data(self.resultexams.model().index(row, 0))
            examname = self.resultexams.model().data(self.resultexams.model().index(row, 1))
            examtype = self.resultexams.model().data(self.resultexams.model().index(row, 5))
            department = self.resultexams.model().data(self.resultexams.model().index(row, 6))
        sql = "SELECT * FROM {}".format(examid+examname+examtype+department)
        print("examtable -",examid+examname+examtype+department)
        cursor.execute(sql)
        quesans = cursor.fetchall()

        pdf = FPDF()
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font("Arial", size = 12)
        # Effective page width, or just epw
        epw = pdf.w - 2*pdf.l_margin
        pdf.set_font("Arial",'B',16.0) 
        pdf.cell(epw, 0.0, 'Result', align='L')
        pdf.set_font("Arial", size = 10) 
        pdf.ln(3.0)
        pdf.cell(100, 10, 'Name - '+'Shivam Deotarse'+'   Roll No - '+'5019114', align='L')
        pdf.ln(7.0)
        pdf.cell(100, 10, 'Exam ID - '+'19'+'    Exam Name - '+'AT'+'    Exam Type - '+'IA2'+'   Department - '+'IT', align='L')
        pdf.image('img\logo-oles-filled.png', x = 175, y = 7, w = 20, h = 20)
        pdf.ln(5.0)

        th = pdf.font_size
        # Line break equivalent to 4 lines
        pdf.ln(4*th)
        
        pdf.set_font('Times','B',14.0) 
        pdf.cell(epw, 0.0, 'Attempted Responses', align='C')
        pdf.set_font('Times','',10.0) 
        pdf.ln(10)

        pdf.set_font('Times','B',10.0)
        pdf.cell(epw/26, 2*th, 'No', border=1, align='C')
        pdf.cell(epw/1.5, 2*th, 'Question', border=1, align='C')
        pdf.cell(epw/16, 2*th, 'Type', border=1, align='C')    
        pdf.cell(epw/8, 2*th, 'Correct Ans', border=1, align='C')
        pdf.cell(epw/8, 2*th, 'Response', border=1, align='C')
        pdf.ln(2*th)

        pdf.set_font('Times','',10.0)
        
        # Here we add more padding by passing 2*th as height
        for row,row_data in enumerate(quesans):
            # Enter data in colums
            pdf.cell(epw/26, 7*th, str(quesans[row][0]), border=1)  
            sql = "select question from {} where quesno = {}".format(examid+examname+examtype+department, str(quesans[row][0]))
            cursor.execute(sql)
            myresult = cursor.fetchone()[0]
            StoreFilepath = "img/question{}.png".format(str(quesans[row][0]))
            with open(StoreFilepath, "wb") as file:
                file.write(myresult)
                file.close() 
            pdf.cell(epw/1.5, 7*th, '', border=1)     
            pdf.image('img\question'+str(row+1)+'.png', x = 19, y = 33+(row+1)*25, w = 125, h = 20)        
            pdf.cell(epw/16, 7*th, str(quesans[row][3]), border=1)    
            pdf.cell(epw/8, 7*th, str(quesans[row][4]), border=1)
            pdf.cell(epw/8, 7*th, str(quesans[row][5]), border=1)
            pdf.ln(7*th)
        
        pdf.ln(20)        
        pdf.set_font('Times','B',14.0) 
        pdf.cell(epw, 0.0, 'Analysis', align='C')
        pdf.set_font('Times','',10.0) 
        pdf.ln(10)

        
        # fig = plt.figure()
        # ax = fig.add_axes([0,0,1,1])
        # langs = ['Correct Answers', 'Wrong Answers', 'Unattempted Answers']
        # students = [23,17,35]
        # ax.bar(langs,students)
        # plt.savefig("img/analysis1.png")

        # pdf.image('img\analysis1.png', x = 19, y = 300, w = 125, h = 125)
        pdf.output("result.pdf")
        

class Exam(QMainWindow,Login):
    def __init__(self,rollNo):
        super(Exam,self).__init__(rollNo)
        loadUi("exam.ui",self)
        self.setWindowTitle("OLES - Online Exam System")
        self.blur()
        self.userrollno_2.setText(rollNo)
        self.setUserInfo()        
        self.exampanel.setVisible(False)
        self.finalstartexambtn.clicked.connect(self.startExam)
        self.submitexambtn.clicked.connect(self.submitExam)
        #blocks all keys of keyboard
        for i in range(150):
            keyboard.block_key(i)
        a = Application(rollNo)
        examQuesTablename = a.getExamQuesTablename()
        self.examidlbl.setText(examQuesTablename[0])
        self.examnamelbl.setText(examQuesTablename[1])
        self.examtypelbl.setText(examQuesTablename[2])
        self.examdeptlbl.setText(examQuesTablename[3])
        self.examdatelbl.setText(examQuesTablename[4])
        self.examtimelbl.setText(examQuesTablename[5]+"-"+examQuesTablename[6])
        self.shuffleQues(examQuesTablename[0]+examQuesTablename[1]+examQuesTablename[2]+examQuesTablename[3])
        self.setQuesNo(examQuesTablename[0]+examQuesTablename[1]+examQuesTablename[2]+examQuesTablename[3])

    def blur(self):	
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(40) 
        self.blurlbl.setGraphicsEffect(self.blur_effect)

    def setUserInfo(self):
        sql = "select * from user where rollno = %s"
        values = (self.userrollno_2.text(),)
        cursor.execute(sql,values)
        myresult = cursor.fetchone()
        StoreFilepath = "img/image.jpg"
        with open(StoreFilepath, "wb") as file:
            file.write(myresult[6])
            file.close()
        self.userphoto_2.setPixmap(QPixmap("img/image.jpg"))
        self.username_2.setText(myresult[2])
        self.usertype_2.setText(myresult[4])

    def setQuesNo(self,examtable):
        sql = "select shuffledNo from {}".format(examtable)
        cursor.execute(sql)
        result = cursor.fetchall()
        quesno = ()
        for x in result:
            quesno = quesno + (x[0],)
        print("questions-",quesno)

        positions = [(i,j) for i in range(len(quesno)) for j in range(0,4)]
        for position, ques in zip(positions, quesno):
            #print("position=`{}`, ques=`{}`".format(position, quesno.index(ques)))
            button = QPushButton("{}".format(quesno.index(ques)+1),self)
            button.setFixedHeight(70)
            button.setFixedWidth(70)
            button.setFont(QFont('', 20))
            button.setStyleSheet("background: rgba(255,255,255,0.75); border:none; border-radius:5px;")
            button.clicked.connect(lambda ch, ques=ques: self.getQues(ques,examtable,quesno))
            self.gridLayout.addWidget(button, *position) 
            checkedans[ques] = []   
        print("Checked Ans -",checkedans)            

    def setAns(self,fetchedans,type,checkedans,ques,quesno):
        a = list(fetchedans)
        random.shuffle(a)
        answers = tuple(a)        
        
        if type == "mcq":
            for ans in answers:
                if ans is not None:
                    label = QRadioButton(ans)
                    label.setFixedWidth(1280)
                    label.setFont(QFont('',14))
                    label.setStyleSheet("background: rgba(255,255,255,0.6);border-radius:5px; padding:10px 10px")
                    if len(checkedans[str(quesno)]):
                        if ans == checkedans[str(quesno)][0]:
                            label.setChecked(True)
                    self.verticalLayout.addWidget(label)
        elif type == "multi":
            for ans in answers:
                if ans is not None:
                    label = QCheckBox(ans)
                    label.setFixedWidth(1280)
                    label.setFont(QFont('',14))
                    label.setStyleSheet("background: rgba(255,255,255,0.6);border-radius:5px; padding:10px 10px")
                    if len(checkedans[str(quesno)]):
                        for check in checkedans[str(quesno)]:
                            if ans == check:
                                label.setChecked(True)
                    self.verticalLayout.addWidget(label)
        elif type == "logical":
            for ans in answers:
                if ans is not None:
                    label = QRadioButton(ans)
                    label.setFixedWidth(1280)
                    label.setFont(QFont('',14))
                    label.setStyleSheet("background: rgba(255,255,255,0.6);border-radius:5px; padding:10px 10px")
                    if len(checkedans[str(quesno)]):
                        if ans == checkedans[str(quesno)][0]:
                            label.setChecked(True)
                    self.verticalLayout.addWidget(label)
        elif type == "numerical":            
            label = QTextEdit("Type your integer answer -")
            label.setFixedWidth(1280)
            label.setFont(QFont('',14))
            label.setStyleSheet("background: rgba(255,255,255,0.6);border-radius:5px; padding:10px 10px")
            if len(checkedans[str(quesno)]):
                label.setText(checkedans[str(quesno)][0])
            self.verticalLayout.addWidget(label)

    def startExam(self):
        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start() 

        self.exampanel.setVisible(True)
        self.informationframe.setVisible(False) 

    def shuffleQues(self,examtable):
        cursor.execute("select quesNo from {}".format(examtable))
        result = cursor.fetchall()
        ques = ()
        for x in result:
            ques = ques + (x[0],)
        l = list(ques)
        random.shuffle(l)
        quesnos = tuple(l)
        print("shuffledQues -",quesnos)
        for i in range(1,len(quesnos)+1):
            sql = "update {} set shuffledNo = %s where quesNo = %s".format(examtable)
            value = (quesnos[i-1],i)
            print("values -",value)
            cursor.execute(sql,value)
            connection.commit() 

    def getQues(self,ques,examtable,quesno):
        answidgets = (self.verticalLayout.itemAt(i).widget() for i in range(self.verticalLayout.count()))         
        for widget in answidgets:
            if isinstance(widget, QRadioButton):
                if widget.isChecked():
                    checkedans[self.quesnolbl.text()] = [widget.text()]
                    print("Ans updated -",checkedans)
            if isinstance(widget, QCheckBox):
                if widget.isChecked():
                    checkedans[self.quesnolbl.text()].append(widget.text())
                    print("Ans updated -",checkedans)
            if isinstance(widget, QTextEdit):
                if widget.text() is not None:
                    checkedans[self.quesnolbl.text()] = [widget.text()]
                    print("Ans updated -",checkedans)
        for i in reversed(range(self.verticalLayout.count())): 
            self.verticalLayout.removeWidget(self.verticalLayout.itemAt(i).widget())
            print("removed widget")
        print("quesno -",ques)       
        sql = "select * from {} where quesNo = %s".format(examtable)
        value = (ques,)
        cursor.execute(sql,value)         
        result = cursor.fetchall()
        StoreFilepath = "img/question.jpg"
        with open(StoreFilepath, "wb") as file:
            file.write(result[0][2])
            file.close()
        self.quesdisplay.setPixmap(QPixmap("img/question.jpg"))
        self.quesnolbl.setText(str(quesno.index(ques)+1))
        #print("result -",result)
        
        self.setAns((result[0][4],result[0][5],result[0][6],result[0][7],result[0][8]),result[0][3],checkedans,ques,quesno.index(ques)+1)   
        connection.commit()     

    def closeEvent(self):
        self.thread.stop()
        #event.accept()   

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""       

        #face tracking
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml') 
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:     
            self.warningdisplaylbl.setText('Your face not found')
            self.majorwarninglbl.setText(str(int(self.majorwarninglbl.text())-1))
        for (x, y, w, h) in faces:
            cv2.rectangle(cv_img, (x, y), (x + w, y + h), (255, 0, 0), 2)  

        # motiondetection
        global frameCount
        frameCount += 1
        # Resize the frame
        resizedFrame = cv2.resize(cv_img, (0, 0), fx=2, fy=2)
        cv_img = cv2.resize(cv_img, (0, 0), fx=1.3, fy=1.3)
        # Get the foreground mask
        fgmask = fgbg.apply(resizedFrame)

        # Count all the non zero pixels within the mask
        count = np.count_nonzero(fgmask)
        print('Frame: %d, Pixel Count: %d' % (frameCount, count))

        # Determine how many pixels do you want to detect to be considered "movement"
        #if (frameCount > 1 and cou`nt > 5000):
        if (frameCount > 1 and count > 5000):
                self.warningdisplaylbl.setText('Do not move')
                self.minorwarninglbl.setText(str(int(self.minorwarninglbl.text())-1))

        # We send this frame to GazeTracking to analyze it
        gaze.refresh(cv_img)
        cv_img = gaze.annotated_frame()

        if gaze.is_blinking():
            self.warningdisplaylbl.setText('Blinking')
        elif gaze.is_right():
            self.warningdisplaylbl.setText('Looking Right')
            self.minorwarninglbl.setText(str(int(self.minorwarninglbl.text())-1))
        elif gaze.is_left():
            self.warningdisplaylbl.setText('Looking Left')
            self.minorwarninglbl.setText(str(int(self.minorwarninglbl.text())-1))
        elif gaze.is_center():
            self.warningdisplaylbl.setText('Looking Center')

        # left_pupil = gaze.pupil_left_coords()
        # right_pupil = gaze.pupil_right_coords()           

        qt_img = self.convert_cv_qt(cv_img)
        self.webcam.setPixmap(qt_img)

        if(int(self.majorwarninglbl.text())<0 or int(self.minorwarninglbl.text())<0 ):
            self.submitExam()

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(400, 250, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def submitExam(self):
        sql = "ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} VARCHAR(255) NOT NULL".format(examQuesTablename[0]+examQuesTablename[1]+examQuesTablename[2]+examQuesTablename[3], "marked"+self.userrollno_2.text())
        cursor.execute(sql)
        for i in range(1,len(checkedans)):
            sql1 = "update {} set {} = %s where shuffledNo = %s".format(examQuesTablename[0]+examQuesTablename[1]+examQuesTablename[2]+examQuesTablename[3], "marked"+self.userrollno_2.text())
            value1 = ""
            for value in checkedans[str(i)]:
                value1 += value + "#"
            cursor.execute(sql1,(value1,i))
        connection.commit()
        widgets.setCurrentIndex(widgets.currentIndex()-1)
        widgets.showNormal()
        self.thread.stop() 
        for i in range(150):
            keyboard.unblock_key(i)   
    

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        # create socket
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        host_ip = '192.168.56.1' # paste your server ip address here
        port = 9999
        client_socket.connect((host_ip,port)) # a tuple
        # capture from web cam
        cap = cv2.VideoCapture(0)
        
        # Socket Accept            
        while self._run_flag:                              
            ret, cv_img = cap.read()
            a = pickle.dumps(cv_img)
            message = struct.pack("Q",len(a))+a
            self.sleep(1)
            client_socket.sendall(message)
            # cv2.imshow('TRANSMITTING VIDEO',cv_img)
            # key = cv2.waitKey(1) & 0xFF
            # if key ==ord('q'):
            #     client_socket.close()
            if ret:
                self.change_pixmap_signal.emit(cv_img)
        # shut down capture system
        cap.release()
        

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

app = QApplication(sys.argv)
loginwindow = Login('dummy')
#applicationwindow = Application('dummy')
widgets = QtWidgets.QStackedWidget()
widgets.addWidget(loginwindow)
widgets.setMinimumWidth(1200)
widgets.setMinimumHeight(800)
widgets.setWindowTitle("OLES - Online Exam System")
widgets.show()
app.exec_()
