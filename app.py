import RPi.GPIO as GPIO
import threading
import subprocess
import time
import datetime
from  time import localtime,strftime
import pymysql
import os
from py532lib.i2c import * #pip3 install py532lib
from flask import Flask, request, abort

from linebot import (
	LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

# Line BOT
app = Flask(__name__)
# Channel Access Token
line_bot_api = LineBotApi('7O73HJIwylbM9bQvBd4Lt1/QvKWxH3RaXFQi2GvfrSWJEP+rYbP9MeNlENq3qDACmttnsvaZVNpEkXnc1L9pRH9K+hee5UEun/ExyJBvYFnFC1gIxciS4Z+QZ42O37USyDOWbZemBkfBeKRqIU4f0wdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('eeac4a6fb266c27b3618e6ae4dccf8c1')

#GPIO 
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
SERVO_MOTOR_PIN = 17
GREEN_PIN = 27
YELLO_PIN = 22
RED_PIN = 23

#AWS RDS
RDS_IP = 'hscc.c0iclrewkkd6.us-east-1.rds.amazonaws.com'
RDS_DB_PARAMETER = {'HOST':RDS_IP, 'USER':"hscc739", 'PASS':"hscc739HSCC739", 'DBNAME':"wsn_final", 'PORT':3306}

#status
system_status = 'wait'

class DOOR():
	def __init__(self):
		GPIO.setup(SERVO_MOTOR_PIN, GPIO.OUT)
		self.PWM_FREQ = 50
		self.PWM = GPIO.PWM(SERVO_MOTOR_PIN, self.PWM_FREQ)
		self.PWM.start(0)
		dc = self.angle_to_duty_cycle(0)
		self.PWM.ChangeDutyCycle(dc)
		time.sleep(0.5)

	def lock(self):
		dc = self.angle_to_duty_cycle(0)
		self.PWM.ChangeDutyCycle(dc)
		time.sleep(0.5)

	def unlock(self):
		dc = self.angle_to_duty_cycle(90)
		self.PWM.ChangeDutyCycle(dc)
		time.sleep(0.5)

	def angle_to_duty_cycle(self, angle):
		duty_cycle = (0.05 * self.PWM_FREQ) + (0.19 * self.PWM_FREQ * angle / 180)
		return duty_cycle


class LIGHT():
	def __init__(self):
		GPIO.setup(GREEN_PIN, GPIO.OUT)
		GPIO.setup(YELLO_PIN, GPIO.OUT)
		GPIO.setup(RED_PIN, GPIO.OUT)
		GPIO.output(GREEN_PIN, GPIO.LOW)
		GPIO.output(YELLO_PIN, GPIO.LOW)
		GPIO.output(RED_PIN, GPIO.LOW)
		
	def red_on(self):
		GPIO.output(RED_PIN, GPIO.HIGH)
	def red_off(self):
		GPIO.output(RED_PIN, GPIO.LOW)
	def green_on(self):
		GPIO.output(GREEN_PIN, GPIO.HIGH)
	def green_off(self):
		GPIO.output(GREEN_PIN, GPIO.LOW)
	def yellow_on(self):
		GPIO.output(YELLO_PIN, GPIO.HIGH)
	def yellow_off(self):
		GPIO.output(YELLO_PIN, GPIO.LOW)


class DATABASE():
	def __init__(self, host, user, password, dbname):
		self.connection = None
		self.host = host
		self.user = user
		self.password = password
		self.dbname = dbname

	def connect(self):
		try:
			self.connection = pymysql.connect(self.host, self.user, self.password, self.dbname, charset='utf8')
			self.connection.ping(True)
		except Exception as e:
			print(e)

	def query(self, cmd):
		try:
			cursor = self.connection.cursor()
			cursor.execute(cmd)
		except pymysql.ProgrammingError as e:
			print(e)
			print('Skip it.')
		except pymysql.OperationalError as e:
			print(e)
			self.connect()
			self.query(cmd)
		except Exception as e:
			print(e) #test
			traceback.print_exc()

		return cursor

	def commit(self):
		try:
			self.connection.commit()
		except Exception as e:
			print(e)

	def close(self):
		self.connection.close()


class input_cli:  #always open a receive slot for gateway
	def __init__(self, users_info, RDS_db, LineMessage):
		self.users_info = users_info
		self.RDS_db = RDS_db
		self.LineMessage = LineMessage

	def run(self):
		global system_status, light
		global user_name, limitation_period

		while True:
			command = LineMessage.split() # input('>>').split()

			try:
				if command[0] == 'signup': #yello led
					system_status = 'signup'
					light.yellow_on()

					user_name = command[1]
					limitation_period = command[2]

					time.sleep(5)
					if system_status == 'signup':
						light.yellow_off()
						system_status = 'wait'


				elif command[0] == 'delete':
					self.users_info.clear()
					cmd = "delete from user_info where 1"
					cursor = self.RDS_db.query(cmd)
					self.RDS_db.commit()
				elif command[0] == 'print':
					#[TODO] publish
					for user in self.users_info:
						print(str(self.users_info[user]))
				else:
					print('No such command.')

			except Exception as e:
				print(e)
				light.yellow_off()
				light.red_off()
				light.green_off()


def getUserIDs(RDS_db):
	users_info = {}
	cursor = RDS_db.query('select nfc_id, name, signup_time, vaild_time from user_info')
	for record in cursor:
		user_info = {}
		user_info['name'] = str(record[1])
		user_info['signup_time'] = str(record[2])
		user_info['vaild_time'] = str(record[3])
		users_info[str(record[0])] = user_info

	return users_info


def isExpired(user_info):

	if user_info['vaild_time'] == 'None':
		return False

	current_time = datetime.datetime.now()
	vaild_time = datetime.datetime.strptime(user_info['vaild_time'],"%Y-%m-%d %H:%M:%S")

	if current_time > vaild_time:
		return True

	return False

def user_signup(RDS_db, user_nfc_id, user_name, limitation_period, users_info):

	if user_nfc_id in users_info:
		return None, None

	user_info = {}
	signup_time = strftime("%Y-%m-%d %H:%M:%S",localtime())
	user_info['signup_time'] = signup_time
	if limitation_period == '0':
		cmd = "INSERT INTO user_info(nfc_id, name, signup_time) VALUES (\'%s\',\'%s\',\'%s\')" %(user_nfc_id, user_name, signup_time)
		user_info['vaild_time'] = 'None'
	else:
		vaild_time = datetime.datetime.strptime(signup_time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(0,int(limitation_period))
		cmd = "INSERT INTO user_info(nfc_id, name, signup_time, vaild_time) VALUES (\'%s\',\'%s\',\'%s\',\'%s\')" %(user_nfc_id, user_name, signup_time, vaild_time)
		user_info['vaild_time'] = vaild_time.strftime("%Y-%m-%d %H:%M:%S")

	print(cmd)
	cursor = RDS_db.query(cmd)
	RDS_db.commit()

	user_info['name'] = user_name
	users_info[user_nfc_id] = user_info

	return signup_time, user_info['vaild_time']


class cmd_handler:
	def __init__(self):
		global light, system_status
		global user_name, limitation_period

		#self.nfc_reader = Pn532_i2c()
		#self.nfc_reader.SAMconfigure()
		self.door = DOOR()
		light = LIGHT()
		self.RDS_db = DATABASE(RDS_DB_PARAMETER['HOST'], RDS_DB_PARAMETER['USER'], RDS_DB_PARAMETER['PASS'], RDS_DB_PARAMETER['DBNAME'])
		self.RDS_db.connect()


		'''cmd = "INSERT INTO user_info(nfc_id, name, signup_time, vaild_time) VALUES (\'%s\',\'%s\',\'%s\',\'%s\')" %('9999','banana',strftime("%Y-%m-%d %H:%M:%S",localtime()),'2019-05-09 18:00:00')
		cursor = RDS_db.query(cmd)
		RDS_db.commit()'''

	def execute(LineMessage):
		global light, system_status
		global user_name, limitation_period

		# retrieve user_infos
		users_info = getUserIDs(self.RDS_db)
		print('User Information:')
		for user in users_info:
			print(str(users_info[user]))
		
		input_cli(users_info, self.RDS_db, LineMessage)
		'''
		try:
			print('Read nfc...')
			raw_nfc_data = self.nfc_reader.read_mifare().get_data()
			nfc_data = list((' '.join(hex(x)[2:] for x in raw_nfc_data)).split(' '))
			nfc_data.pop(8)
			nfc_data.pop(8)
			nfc_data.pop(8)
			nfc_data = ''.join(str(x) for x in nfc_data)

			print('----------------------------------')
			print('Received NFC ID: %s' %(nfc_data))
			if system_status == 'wait':
			
				if nfc_data in users_info:
					if isExpired(users_info[nfc_data]) is False:
						print('This ID is recognized. Open the door.')
						light.green_on()
						self.door.unlock()
						time.sleep(3)
						light.green_off()
						self.door.lock()
					else:
						#[TODO] publish
						print('This ID is expired.')
						light.red_on()
						users_info.pop(nfc_data)
						cmd = "delete from user_info where nfc_id = \'%s\'" %(nfc_data)
						self.RDS_db.query(cmd)
						self.RDS_db.commit()
						time.sleep(2)
						light.red_off()

				else:
					#[TODO] publish
					print('Ilegal ID!')
					light.red_on()
					time.sleep(2)
					light.red_off()

			elif system_status == 'signup':
			
				signup_time, vaild_time = user_signup(self.RDS_db, nfc_data, user_name, limitation_period, users_info)
				print('----------------------------------')
				if signup_time is None:
					#[TODO] publish
					print('This NFC ID has already existed.')
				else:
					print('Sign up a new user: ')
					print('NFC ID: %s' %(nfc_data))
					print('USER NAME: %s' %(user_name))
					print('SIGNUP TIME: %s' %(signup_time))
					print('VAILD TIME: %s' %(vaild_time))

				light.yellow_off()
				system_status = 'wait'
				#[TODO] publish message "signup ok"

		except KeyboardInterrupt:
			pass
		'''


# Listen to all Post Request from /callback
@app.route("/callback", methods=['POST'])
def callback():
	global cmd_handle
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
	global_handle.execute(body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# reply message
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = TextSendMessage(text=event.message.text)
    line_bot_api.reply_message(event.reply_token, message)


if __name__ == "__main__":
	global cmd_handle
	cmd_handle = cmd_handler()
	port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
