 def async_get_category_media_data(self, tid):
        asyncio.run(self._category_request_task_main(tid))

    def categoryContent(self, tid, pg, filter, extend):
        self.log(tid)
        self.log(extend)
        self.async_get_category_media_data(tid)
        videos = []
        if self.media_json_data:
            videos = self.media_json_data['list']

        if extend and len(videos):
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



    def _get_media_data(self, url):
        self.log(url)
        data = self.fetch(url)
        if data.status != 200:
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

    def detailContent(self, array):
        id = array[0]
        media_vod = self.id_map.get(id)
        file_class = media_vod.get('file_class')
        self.log(file_class)
        if len(file_class) == 0:
            return {"list": None}

        if file_class not in self.media_dict:
            self._file_class_media_request(file_class)
            self.log(self.media_dict)
        cur_class_media = self.media_dict.get(file_class)
        cur_id_map = cur_class_media.get('id_map')
        item = cur_id_map.get(id)

        # self.log(item)
        new_media = copy.deepcopy(media_vod)
        new_media["vod_play_from"] = item["vod_play_from"]
        new_media["vod_play_url"] = item["vod_play_url"]
        new_media["vod_content"] = item["vod_content"]
        fans = new_media.get('fans')
        hot_mark = ""
        if fans is not None:
            if fans >= 10000:
                hot_mark = "    热度: " + str(round(fans / 1000, 1)) + "K"
            elif fans >= 1:
                hot_mark = "    热度: " + str(fans)
            new_media["vod_remarks"] += hot_mark
        vod = []
        vod.append(new_media)
        result = {"list": vod}
        return result


    def searchContent(self, key, quick):
        videos = []
        if self.media_json_data:
            videos = self.media_json_data['list']

        search_list = []
        for item in videos:
            if key in item['vod_name']:
                search_list.append(item)

        result = {
            "list": search_list,
            "page": "1"
        }
        return result

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
        self.log("媒体请求开始", file_class)
        self._file_class_media_request(file_class)
        self.log("媒体请求开始", file_class)
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



  
