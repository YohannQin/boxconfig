import sys
import requests
import re
from urllib.parse import urljoin
sys.path.append('..')
from base.spider import Spider
from pyquery import PyQuery as pq


class Spider(Spider):
    def init(self, extend=""):
        self.host = 'https://xchina001.site'
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }
        print(f"使用站点: {self.host}")

    def getName(self):
        return "小黄书"

    def isVideoFormat(self, url):
        return any(ext in (url or '') for ext in ['.m3u8', '.mp4', '.ts'])

    def manualVideoCheck(self):
        return False
    
    def _extractVideoItems(self, html_content):
        vods = []
        video_items = re.findall(r'<div[^>]*class="item video[^>]*>(.*?)</div>', html_content, re.S)
        for item in video_items:
            link_match = re.search(r'<a[^>]*href="(.*?)"[^>]*title="(.*?)"[^>]*>', item)
            self.log("aa\n")
            self.log(item)
            if link_match:
                href = link_match.group(1)
                title = link_match.group(2)
                img = ''
                img_match = re.search(r'background-image:url\((.*?)\)', item)
                if img_match:
                    img = img_match.group(1).strip('"\'')
                    if not img.startswith(('http://', 'https://')):
                        img = urljoin(self.host, img)
                
                vods.append({
                    'vod_id': href,
                    'vod_name': title.strip(),
                    'vod_pic': img,
                    'vod_remarks': ''
                })
        
        if not vods:
            general_items = re.findall(r'<a[^>]*href="(/videos/.*?)"[^>]*title="(.*?)"[^>]*>', html_content, re.S)
            for href, title in general_items:
                full_href = urljoin(self.host, href)
                vods.append({
                    'vod_id': full_href,
                    'vod_name': title.strip(),
                    'vod_pic': '',
                    'vod_remarks': ''
                })
        
        return vods
        
    def parseVideoItems(self, doc):
        # 查找所有视频项
        video_items = doc('.item.video')
        videos_data = []

        for item in video_items.items():
            # 1. 提取 href
            # 从第一个a标签获取href
            href = item.find('a').eq(0).attr('href')
            self.log(href)
    
            # 2. 提取 title
            # 从第一个a标签的title属性获取
            title = item.find('a').eq(0).attr('title')
            # 或者从.title类元素获取
            title_text = item.find('.title a').text()
            self.log(title_text)
    
            # 3. 提取 model-item (模特名称)
            model_item = item.find('.model-item').text()
            self.log(model_item)
    
            # 4. 提取 tags
            # 获取所有tag div，排除空的和包含图标的
            tags_elements = item.find('.tags > div')
            items = list(tags_elements.items())
            self.log(len(items))
            #self.log(items)
            vendor = items[0].text().strip()
            comment =items[1].text().strip()
            seria_num = items[2].text().strip()
            times = items[3].text().strip()
            #magnet = items[4].text().strip()
            
            # 提取封面图片URL
            # 从style属性中提取背景图片URL
            style_attr = item.find('.img').attr('style')
            cover_url = None
            if style_attr and 'background-image:url' in style_attr:
                import re
                match = re.search(r"url\('([^']+)'\)", style_attr)
                if match:
                    cover_url = match.group(1)
            
            name = title.strip()
            if seria_num:
                name = seria_num + ' ' + name
            videos_data.append({
                    'vod_id': href,
                    'vod_name': name,
                    'vod_pic': cover_url,
                    'vod_remarks': model_item
                })
        return videos_data

    def parseModelItems(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        # 查找所有作者
        model_items = soup('.item.model')
        videos_data = []

        for item in model_items:
            # 1. 提取 href
            href = item.find('a').get('href')
            # self.log(href)

            # 2. 提取 作者名
            title = item.find('a').get('title')
            # self.log(title)

            # 3. 提取 tags， 获取所有tags的所有直接子div
            tags_elements = item.select(".tags > div")
            image_count = tags_elements[0].get_text().strip()
            video_count = tags_elements[1].get_text().strip()

            # 4 获取简介
            brief_div = item.find('.brief')
            if brief_div:
                brief_text = brief_div.get_text().strip()

            # 5 获取图片
            style_attr = item.find('.img').get('style')
            cover_url = None
            if style_attr and 'background-image:url' in style_attr:
                match = re.search(r"url\('([^']+)'\)", style_attr)
                if match:
                    cover_url = match.group(1)

            remarks = '视频:' + video_count
            videos_data.append({
                'vod_id': href,
                'vod_name': title,
                'vod_pic': cover_url,
                'vod_remarks': remarks,
                'vod_tag': 'folder'
            })
        return videos_data

    def homeContent(self, filter):
        result = {}
        classes = []
        video_cate = [
            {'type_name': '华人演员', 'type_id': '/models/type-7.html'},
            {'type_name': '日本演员', 'type_id': '/models/type-10.html'},
            #{'type_name': '麻豆传媒', 'type_id': '/videos/series-5f904550b8fcc.html'},
            #{'type_name': '独立创作者', 'type_id': '/videos/series-61bf6e439fed6.html'},
        ]
         
        url = urljoin(self.host, 'categories.html')
        response = requests.get(url, headers=self.header)
        #self.log(response.content)
        response.encoding = 'utf-8'
        doc = pq(response.content)
        #video_cate = []
        self.log("11111\n")
        for a in doc('a').items():
            # 提取href中的ID
            href = a.attr('href')
            if href and 'videos/series-' in href:
                self.log(href)
                series_id = href.split('series-')[1].split('.html')[0]

                # 提取class="title"的文本内容
                title = a.find('.title').text()
                if not title:
                    continue

                video_cate.append({
                    'type_name': title,
                    'type_id': href,
                })

        #classes.extend(video_classes)
        result['class'] = video_cate
        result['filters'] = {}
        return result

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        if tid.startswith('http'):
            url = tid
        else:
            url = urljoin(self.host, tid)
        pg = int(pg) if pg else 1
        if pg > 1:
            if '?' in url:
                url += f"&page={pg}"
            else:
                url += f"?page={pg}"
        
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            html_content = res.text
            # 使用辅助方法提取视频项
            #vods = self._extractVideoItems(html_content)
            if "models" in tid:
                vods = self.parseModelItems(html_content)
            else:
                vods = self.parseVideoItems(pq(res.content))
            result['list'] = vods
            current_page_items = len(vods)
            has_next_page = '下一页' in html_content or 'next' in html_content.lower() or f'page={pg+1}' in html_content
            if has_next_page:
                pagecount = pg + 1
                total = pagecount * current_page_items
            else:
                pagecount = pg
                total = current_page_items
            
            result['page'] = pg
            result['pagecount'] = pagecount
            result['limit'] = current_page_items
            result['total'] = total
        except Exception as e:
            print(f"categoryContent error: {e}")
            result['list'] = []
            result['page'] = pg
            result['pagecount'] = 1
            result['limit'] = 30
            result['total'] = 0
        return result

    def detailContent(self, ids):
        vid = ids[0]
        url = vid if 'http' in vid else urljoin(self.host, vid)
        vod = {
            'vod_id': vid,
            'vod_name': '小黄书视频',
            'vod_pic': '',
            'type_name': '',
            'vod_year': '',
            'vod_area': '',
            'vod_remarks': '',
            'vod_actor': '',
            'vod_director': '',
            'vod_content': ''
        }
        
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            html_content = res.text
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.S)
            if title_match:
                vod['vod_name'] = title_match.group(1).strip()
            else:
                title_match_alt = re.search(r'<title>(.*?)</title>', html_content, re.S)
                if title_match_alt:
                    full_title = title_match_alt.group(1).strip()
                    vod['vod_name'] = full_title.split(" - ")[0] if " - " in full_title else full_title
            cover_match = re.search(r'<meta property="og:image" content="(.*?)"', html_content, re.S)
            if cover_match:
                cover_img = cover_match.group(1).strip()
                if not cover_img.startswith(('http://', 'https://')):
                    cover_img = urljoin(self.host, cover_img)
                vod['vod_pic'] = cover_img
            desc_match = re.search(r'<meta name="description" content="(.*?)">', html_content, re.S)
            if desc_match:
                vod['vod_content'] = desc_match.group(1).strip()
            else:
                jsonld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html_content, re.S)
                if jsonld_match:
                    try:
                        import json
                        jsonld_data = json.loads(jsonld_match.group(1))
                        if isinstance(jsonld_data, list):
                            for item in jsonld_data:
                                if isinstance(item, dict) and 'description' in item:
                                    vod['vod_content'] = item['description']
                                    break
                    except:
                        pass

            # 解析视频连接
            video_url = None
            videoplayer_pattern = re.compile(r'const player = new VideoPlayer\(.*?src:\s*["\']([^"\']+?)["\']', re.S)
            videoplayer_match = videoplayer_pattern.search(html_content)
            if videoplayer_match:
                video_url = videoplayer_match.group(1)
                
            vod['vod_play_from'] = '瑟佬在线'
            vod['vod_play_url'] = video_url
        except Exception as e:
            print(f"detailContent error: {e}")
        return {'list': [vod]}

    def playerContent(self, flag, id, vipFlags):
        url = id
        try:
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            html = res.text
            videoplayer_pattern = re.compile(r'const player = new VideoPlayer\(.*?src:\s*["\']([^"\']+?)["\']', re.S)
            videoplayer_match = videoplayer_pattern.search(html)
            if videoplayer_match:
                video_url = videoplayer_match.group(1)
                if re.search(r'\.(m3u8|mp4|ts)', video_url):
                    return {
                        'jx': 0,
                        'parse': 0,
                        'url': video_url,
                        'header': {
                            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
                            'Referer': url
                        }
                    }
            
        except Exception as e:
            print(f"playerContent解析错误: {e}")
        return {'parse': 1, 'url': url, 'header': self.header}

    def searchContent(self, key, quick):
        result = {'list': []}
        try:
            search_url = f'{self.host}/search?q={key}'
            res = requests.get(search_url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            html_content = res.text
            vods = self._extractVideoItems(html_content)
            result['list'] = vods
        except Exception as e:
            print(f"searchContent error: {e}")
        return result
    
    def homeVideoContent(self):
        try:
            url = self.host
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            html_content = res.text
            vods = self._extractVideoItems(html_content)
            return {'list': vods}
        except Exception as e:
            print(f"homeVideoContent error: {e}")
            return {'list': []}
    
    def localProxy(self, params):
        return None
