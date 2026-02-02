#coding=utf-8
#!/usr/bin/python
import sys
sys.path.append('..')
from base.spider import Spider
import base64
import json
import copy
import asyncio

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

	def categoryContent(self,tid,pg,filter,extend):
		asyncio.run(self._task_main())
		#self.base_url = self.ext.get('base')
		self.log(tid)
		self.log(filter)
		self.log(extend)
		self.raw_json = self.base_url + "hjbox_media.json"
		if self.media_json_data is None:
			data= self._get_media_data(self.raw_json)
			#self.log(data)
			self.media_json_data = data
			videos = self.media_json_data['list']
			self.id_map = {item["vod_id"]: item for item in videos}
		videos = self.media_json_data['list']
		result = {
			"page": pg,
			"pagecount": 1,
			"limit": len(videos),
			"total": len(videos),
			"list": videos
		}
		return result

	def _get_media_data(self,url):
		self.log(url)
		data = self.fetch(url)
		self.log(data)
		data = data.text
		data = base64.b64decode(data)
		data = data.decode('utf-8')
		data = json.loads(data)
		return data

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
				self.log(self.media_dict)
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
	def searchContent(self,key,quick):
		pass
	def destroy(self):
		pass
	def localProxy(self, param):
		pass