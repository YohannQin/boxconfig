#coding=utf-8
#!/usr/bin/python
import sys
sys.path.append('..')
from base.spider import Spider
import base64
import json
import copy
import asyncio
import datetime
import concurrent.futures

class Spider(Spider):
	def init(self,extend=""):
		self.base_url = ""
		self.raw_json = "https://ghfast.top/https://raw.githubusercontent.com/YohannQin/my_test/refs/heads/main/hj_media_en.json"
		#self.raw_json = "https://raw.githubusercontent.com/YohannQin/database/refs/heads/main/hj/user/hjbox_media.json"
		self.media_json_data = None
		self.id_map = None
		self.media_dict = dict()
		self.ext = json.loads(extend)
		self.filters = self.ext.get('filters')
		self.base_url = self.ext.get('base')
		
	def homeContent(self,filter):
		classes = [{"type_name": "博主","type_id":"author"}]
		result = {"class": classes, "filters": self.filters}
		return result
	
	def async_get_category_media_data(self, tid):
		asyncio.run(self._category_request_task_main(tid))

	def categoryContent(self,tid,pg,filter,extend):
		self.log(tid)
		self.log(extend)
		self.raw_json = self.base_url + "hjbox_media.json"
		#self.async_get_category_media_data(tid)
		
		if self.media_json_data is None:
			self._category_request_main(tid)
		
		curr_data = []
		videos = self.media_json_data['list']
		if extend and len(videos):
			self.log(extend)
			curr_data = videos
			if 'sort' in extend and extend['sort'] == "最热":
				curr_data = sorted(videos, key=lambda x: x['fans'], reverse=True)  # True=从晚到早

			filter_data_list = []
			for item in curr_data:
				if 'year' in extend and extend['year'] != item['vod_year']:
					continue
				if 'class' in extend and extend['class'] not in item['type_name']:
					continue
				filter_data_list.append(item)
			if len(filter_data_list):
				curr_data = filter_data_list
			videos = curr_data
		
		result = {
			"page": pg,
			"pagecount": 1,
			"limit": len(videos),
			"total": len(videos),
			"list": videos
		}
		return result
	"""
	def _get_media_data(self,url):
		self.log(url)
		data = self.fetch(url)
		self.log(data)
		data = data.text
		data = base64.b64decode(data)
		data = data.decode('utf-8')
		data = json.loads(data)
		return data
	"""
	def detailContent(self,array):
		id = array[0]
		media_vod = self.id_map.get(id)
		file_class = media_vod.get('file_class')
		self.log(file_class)
		if file_class:
			if file_class in self.media_dict:
				cur_class_media = self.media_dict.get(file_class)
			else:
				url = self.base_url + file_class + '.json'
				data = self._get_media_data(url)
				data = data.get('list')
				id_map = {item["vod_id"]: item for item in data}
				cur_class_media = {
					"media_data": data,
					"id_map": id_map
				}
				self.media_dict[file_class] = cur_class_media
				#self.log(self.media_dict)
			cur_id_map = cur_class_media.get('id_map')
			item = cur_id_map.get(id)

		#self.log(item)
		new_media = copy.deepcopy(media_vod)
		new_media["vod_play_from"] = item["vod_play_from"]
		new_media["vod_play_url"] = item["vod_play_url"]
		new_media["vod_content"] = item["vod_content"]
		fans = new_media.get('fans')
		hot_mark = ""
		if fans is not None:
			if fans >= 10000:
				hot_mark = "    热度: " + str(round(fans/1000, 1)) + "K"
			elif fans >= 1:
				hot_mark = "    热度: " + str(fans)
			new_media["vod_remarks"] += hot_mark
		vod = []
		vod.append(new_media)
		result = {"list": vod}
		return result

	def playerContent(self,flag,id,vipFlags):
		result = {
			'parse': 0,
			'url': id
		}
		return result

	def getName(self):
		return '色播聚合'
		
	async def _media_task(self):
		self.log("开始")
		await asyncio.sleep(5)
		self.log("结束")
		return True
	
	async def _task_main(self):
		self.log("开始执行")
		task1 = asyncio.create_task(self._media_task())
		await asyncio.gather(task1)
		self.log("结束执行")

	def homeVideoContent(self):
		pass
	def isVideoFormat(self,url):
		pass
	def manualVideoCheck(self):
		pass
		
	def searchContentPage(self, key, quick, page):
		result = {}
		videos = []
		if not page:
			page = '1'
		if self.media_json_data:
			videos = self.media_json_data['list']

		search_list = []
		for item in videos:
			if key in item['vod_name']:
				search_list.append(item)

		result['list'] = search_list
		result['page'] = page
		result['pagecount'] = 1
		result['limit'] = len(search_list)
		result['total'] = len(search_list)
		return result

	def searchContent(self, key, quick, pg="1"):
		return self.searchContentPage(key, quick, pg)

	def destroy(self):
		pass
	def localProxy(self, param):
		pass
		
	def _get_media_data(self, url):
		self.log(url)
		data = self.fetch(url)
		if data.status_code != 200:
			self.log("url请求失败")
			self.log(data.text)
			return None
		data = data.text
		data = base64.b64decode(data)
		data = data.decode('utf-8')
		data = json.loads(data)
		return data

	def _category_media_request(self, category):
		url = self.base_url + 'hjbox_media.json'
		data = self._get_media_data(url)
		if data is None:
			return False
		videos = data['list']
		self.id_map = {item["vod_id"]: item for item in videos}
		self.media_json_data = data
		return True

	def _file_class_media_request(self, file_class):
		url = self.base_url + file_class + '.json'
		data = self._get_media_data(url)
		if data is None:
			return False
		data = data.get('list')
		id_map = {item["vod_id"]: item for item in data}
		cur_class_media = {
			"media_data": data,
			"id_map": id_map
		}
		self.media_dict[file_class] = cur_class_media
		return True

	def _category_media_parse(self, category, data):
		self.log("\n首页处理\n")
		if data is None:
			return False
		data = data.text
		data = base64.b64decode(data)
		data = data.decode('utf-8')
		data = json.loads(data)
		videos = data['list']
		self.id_map = {item["vod_id"]: item for item in videos}
		self.media_json_data = data
		self.log(category)
		self.log("\n首页处理结束\n")
		return True

	def _file_class_media_parse(self, file_class, data):
		self.log("\n分类文件处理\n")
		if data is None:
			return False
		data = data.text
		data = base64.b64decode(data)
		data = data.decode('utf-8')
		data = json.loads(data)
		data = data.get('list')
		id_map = {item["vod_id"]: item for item in data}
		cur_class_media = {
			"media_data": data,
			"id_map": id_map
		}
		self.media_dict[file_class] = cur_class_media
		#self.log(data)
		self.log(file_class)
		self.log("\n分类文件处理结束\n")
		return True
				
	def _generate_latest_file_class_list(self):
		now = datetime.datetime.now()
		year = now.year
		quarter = (now.month - 1) // 3 + 1

		# 生成最近几个季度
		recent_quarters = []
		for i in range(2):
			recent_quarters.append(f"{year}h{quarter}")
			# 计算上一个季度
			if quarter == 1:  # 如果是第一季度，上一个季度是去年的第四季度
				year -= 1
				quarter = 4
			else:
				quarter -= 1
		return recent_quarters

	async def _media_category_request_task(self, category):
		self.log("分类请求开始")
		self._category_media_request(category)
		self.log("分类请求结束")
		return True

	async def _media_request_task(self, file_class):
		self.log("媒体请求开始")
		self._file_class_media_request(file_class)
		self.log("媒体请求开始")
		return True

	async def _category_request_task_main(self, category):
		self.log("开始执行")
		tasks = []
		task = asyncio.create_task(self._media_category_request_task(category))
		tasks.append(task)

		class_list = self._generate_latest_file_class_list()
		for file_class in class_list:
			task = asyncio.create_task(self._media_request_task(file_class))
			tasks.append(task)

		await asyncio.gather(*tasks)
		self.log("结束执行")
	
	def send_request_with_callback(self, url, callback, class_str):
		"""发送请求并使用指定的回调函数处理响应"""
		try:
			self.log(url)
			response = self.fetch(url)
			response.raise_for_status()  # 检查HTTP错误
			return callback(class_str, response)
		except  Exception as e:
			self.log(e)
			return {
				'status': 'error',
				'url': url,
				'error': str(e),
				'callback': callback.__name__
			}
			
	def run_concurrent_requests(self, urls):
		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		# 创建任务映射
			future_to_url = {
				executor.submit(self.send_request_with_callback, item['url'], item['callback'], item['class']): item['url']
				for item in urls
			}
		
			# 处理完成的任务
			for future in concurrent.futures.as_completed(future_to_url):
				url = future_to_url[future]
				try:
					result = future.result()
					self.log(f"✓ {url}: {result}")
				except Exception as e:
					self.log(f"✗ {url}: {e}")

	def _category_request_main(self, tid):
		tasks = []
		
		url = {
			"url": self.base_url + "hjbox_media.json",
			"class": tid,
			"callback": self._category_media_parse
		}
		tasks.append(url)
		
		class_list = self._generate_latest_file_class_list()
		#class_list = ["2022h3"]
		for class_str in class_list:
			url = {
				"url": self.base_url + class_str + ".json",
				"class": class_str,
				"callback": self._file_class_media_parse
			}
			tasks.append(url)
			
		self.run_concurrent_requests(tasks)
   

