# -*- coding: UTF-8 -*-
import time
import json
import requests
import threading

class DrivingSpider:

	def __init__(self):
		self.session = requests.Session()
		self.session.headers.update({
			"Accept":"application/json, text/javascript, */*; q=0.01",
			"Accept-Encoding": "gzip, deflate",
			"Accept-Language": "en-GB,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,en-US;q=0.6",
			"Host": "hnay.aaej.cn",
			"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"
			})
		username = 18623748160
		pwd = "Ch123457"
		self.login_page_url = "http://hnay.aaej.cn/gzpt/portal/login/loginPage?backUrl=/gzpt/portal/index41050000"
		self.login_url = "http://hnay.aaej.cn/gzpt/portal/login/login?status=1&account=%d&pwd=%s&_=0.9485058519818086&username=%d&password=Ch123457&isAutoLogin=no&backUrl=/gzpt/portal/index41050000" %(username, pwd, username)
		self.booking_list_url = "http://hnay.aaej.cn/gzpt/portal/stuCenter/getPlanList?token=000&_=0.7182232083437187"
		self.order_url="http://hnay.aaej.cn/gzpt/portal/orderplan/verify/orderPlan"

	def login(self):
		self.session.get(self.login_page_url)
		self.session.headers.update({
			"Referer":"http://hnay.aaej.cn/gzpt/portal/login/loginPage?backUrl=/gzpt/portal/index41050000",
			"X-Requested-With": "XMLHttpRequest"
			})
		self.session.get(self.login_url)

	def get_planning_list(self, 
						  schoolName='安阳蓝盾驾校',
						  coachName='',
						  date='2019-07-23',
						  subject='km2',
						  pageIndex='0',
						  pageSize='10'):
		# schoolName: string
		# coachName: string
		# date: string, format "YYYY-MM-DD"
		# subject: string, "km2" or "km3"
		# pageIndex: string
		# pageSize: string, number of time slots to show (锦泰驾校120)

		self.session.headers.update({
			"Connection": "keep-alive",
			"Referer": "http://hnay.aaej.cn/gzpt/portal/stuCenter/teachingPlanList?_=0.6775536621149114",
			"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
			"Accept": "application/json",	
			"X-Requested-With": "XMLHttpRequest"
			})


		data={
		'schoolName':schoolName,
		'coachName':coachName,
		'currentDate':date,
		'shcoolId':'',
		'areaCode':'',
		'carType':'C1',
		'subject':subject,
		'pageIndex':pageIndex,
		'pageSize':pageSize
		}

		r = self.session.post(self.booking_list_url, data=data)
		# print(r.status_code)
		# print(self.session.cookies)
		return r.text

	def reserve(self, releaseId):
		# releaseId: int
		self.session.headers.update({
			"Connection": "close",
			"Referer":"http://hnay.aaej.cn/gzpt/portal/orderplan/verify/orderConfirmInit?releaseId=%d&preUrl=/gzpt/portal/stuCenter/teachingPlanList?_=0.6775536621149114"%releaseId,
			"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
			"X-Requested-With": "XMLHttpRequest",
			"Accept": "application/json, text/javascript, */*; q=0.01"
			})
		
		data={
		'releaseId':releaseId
		}
		
		resp = self.session.post(self.order_url, data=data)

		# print(resp.text)

		if resp.status_code != 200:
			print("Wrong status: %"%resp.status_code)

		
		if "success" in resp.text:
			 print("ID: %d 预约成功!"%releaseId)
		else:
			 print("ID: %d 预约失败，已被预约或有未评价的预约记录!"%releaseId)


def parse_json(json_planning_list, start_time_list):
	# This method parses json obtained from get_planning_list()
	# json_planning_list: json planning list
	# start_time_list: a list of desired strat training time
	# return: None if none of slot is available
	# 		  ids list of releaseId,  which is a unique id for each time slot
	all_plan = json.loads(json_planning_list)

	if all_plan['count'] == 0:
		return None
	else:
		available_plan = [plan for plan in all_plan['list'] if plan['readyreservationcount'] == '0']
		if available_plan == []:
			return None
		else:
			desired_plan = [plan for plan in available_plan if plan['starttime'] in start_time_list]
			if desired_plan == []:
				return None
			available_ids = [int(plan['id']) for plan in available_plan]
			return available_ids


if __name__ == '__main__':
	print("登陆安阳驾培网......")
	ds = DrivingSpider()
	ds.login()

	schoolName = str(input("请输入驾校名称："))
	date = str(input("请输入预约日期(yy-mm-dd)："))

	# start_time_list = ['08:00', '09:00']
	start_time_list = ['07:00', '17:00', '18:00', '08:00', '09:00', '16:00']
	backup_time_list = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00']
	
	# parse json
	print("获取预约计划中......")
	while True:
		json_planning_list = ds.get_planning_list(schoolName=schoolName, date=date)
		available_ids = parse_json(json_planning_list, start_time_list + backup_time_list)

		if available_ids is None:
			time.sleep(5)
			print("unavailable yet...")
		else:
			break
	print("已获取可预约计划")


	print("预约学时中......")
	# reserve the ids in parallel
	threads = [threading.Thread(target=ds.reserve, args=(releaseId, )) for releaseId in available_ids]

	for t in threads:
		t.start()
		t.join()