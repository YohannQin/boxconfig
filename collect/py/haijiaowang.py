# coding: utf-8
import sys
import requests
import re
import json
from urllib.parse import urljoin
sys.path.append('..')
from base.spider import Spider
from pyquery import PyQuery as pq
from datetime import datetime
from bs4 import BeautifulSoup

class Spider(Spider):
    def init(self, extend=""):
        self.host = 'https://admit.danbhfn.xyz/'
        #self.host = 'https://hjwang4.com/'
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }
        
        print(f"使用站点: {self.host}")

    def getName(self):
        return "海角网"

    def isVideoFormat(self, url):
        return any(ext in (url or '') for ext in ['.m3u8', '.mp4', '.ts'])

    def manualVideoCheck(self):
        return False
    
    def parseVideoItems(self, doc):
        # 查找所有视频项
        video_items = doc('.xqbj-list-rows')
        videos_data = []

        for item in video_items.items():
            if not item.find('.xqbj-list-rows-image'):
                continue
            # 1. 提取 href
            # 从第一个a标签获取href
            href = item.find('a').eq(0).attr('href')
            #self.log(href)
    
            # 2. 提取 title
            # 从第一个a标签的title属性获取
            title = item.find('a').eq(0).attr('title')
            # 或者从.title类元素获取
            #title = item.find('h3').text()
            #self.log(title)
    
            # 3. 提取 model-item (模特名称)
    
            # 4. 提取 tags
            # 获取所有tag div，排除空的和包含图标的
            tags_elements = item.find('.xqbj-list-rows-bottom-tags-text')
            items = list(tags_elements.items())
            #self.log(len(items))
            #self.log(items)
            author = items[0].text().strip()
            watch =items[1].text().strip()
            comment = items[2].text().strip()
            desk_time = items[3].text().strip()
            mobile_time = items[4].text().strip()
            
            video_str = ""
            if not item.find('.is-video'):
                video_str = "  (无视频)"
            
            remarks = desk_time + '    ' + author + video_str
            
            # 提取封面图片URL
            # 从style属性中提取背景图片URL
            #cover_url = item.find('img').eq(0).attr('z-image-loader-url)
            
            videos_data.append({
                    'vod_id': href,
                    'vod_name': title,
                    'vod_pic': "",
                    'vod_remarks': remarks
                })
        return videos_data

    def homeContent(self, filter):
        result = {}
        classes = [
            {'type_name': '海角首页', 'type_id': '/page/'},
            {'type_name': '海角热门', 'type_id': '/order/hot/page/'},
            {'type_name': '今日更新', 'type_id': '/order/today/page/'},
            {'type_name': '海角社区', 'type_id': '/communitys/video/'},
            {'type_name': '海角乱伦', 'type_id': '/category/hjll/'},
            {'type_name': '海角原创', 'type_id': '/category/hjyc/'},
            {'type_name': '海角吃瓜', 'type_id': '/category/hjcg/'},
            {'type_name': '海角看片', 'type_id': '/category/hjkp/'},
            {'type_name': '海角网黄', 'type_id': '/category/hjwh/'},
            {'type_name': '海角探花', 'type_id': '/category/hjth/'},
            {'type_name': '海角动漫', 'type_id': '/category/hjdm/'},
            {'type_name': '海角搬运', 'type_id': '/category/hjby/'},
        ]
        
        result['class'] = classes
        result['filters'] = {}
        return result

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        if tid.startswith('http'):
            url = tid
        else:
            url = urljoin(self.host, tid)
        pg = int(pg) if pg else 1
        url = urljoin(url, str(pg))
        
        try:
            self.header['Referer'] = url
            res = requests.get(url, headers=self.header, timeout=20)
            self.log(res.apparent_encoding)
            res.encoding = 'utf-8'
            html_content = res.text
            vods = self.parseVideoItems(pq(res.text))
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

    def _get_text_link(self, href, name):
        return f'[a=cr:{{"id":"{href}","name":"{name}"}}/]{name}[/a]'
    
    def _get_actor_text_link(self, actor):
        if not actor.get('identifier'):
            return actor["name"]
        href = f'/videos/model-{actor["identifier"]}.html'
        name = actor["name"]
        return self._get_text_link(href, name)
        
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
            self.header['Referer'] = url
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            self.log(res.encoding)
            soup = BeautifulSoup(res.text, 'html.parser')
            # 获取详细内容
            content = soup.select('.text-content')[0]
            ptags = content.find_all('p')
            #self.log(len(ptags))
            text_list = [p.get_text() for p in ptags if p.get_text().strip()]
            texts = '\n\n'.join(text_list)
            self.log(texts)
            novel = soup.select('.novel-info')[0]
            author_url = novel.find('a').get('href')
            self.log(author_url)
            
            vod['vod_play_from'] = '海角网'
            vod['vod_play_url'] = f'开撸${url}'
            div = soup.find('div', attrs={'data-config': True})
            if div:
                config_str = div['data-config']
                config = json.loads(config_str)
                if config.get('video'):
                    video_url = config['video'].get('url')
                    vod['vod_play_url'] = video_url
                    self.log(video_url)
                else:
                    self.log("无视频信息")
                    vod['vod_play_url'] = None
            
            html_content = res.text
            
            json_parse = False
            if False: #desc_match:
                vod['vod_content'] = desc_match.group(1).strip()
            else:
                jsonld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html_content, re.S)
                if jsonld_match:
                    try:
                        jsonld_data = json.loads(jsonld_match.group(1))
                        #self.log(len(jsonld_data))
                        #self.log(jsonld_data)
                        if isinstance(jsonld_data, list):
                            #self.log(len(jsonld_data))
                            for item in jsonld_data:
                                #self.log(item)
                                if isinstance(item, dict) and item.get("@type") == "VideoObject":
                                    vod['vod_name'] = item.get('name')
                                    vod['vod_content'] = item.get('name')
                                    vod['vod_content'] = item.get('name') + '\n\n' + texts
                                    author = item.get('author')
                                    if author:
                                        #vod['vod_director]  = '/'.join([self._get_actor_text_link(term) for term in item['actor']])
                                        vod['vod_director'] = self._get_text_link(author_url, author.get('name'))
                                    dt = datetime.strptime(item.get('uploadDate'), "%Y-%m-%dT%H:%M:%S%z")
                                    vod['vod_remarks'] = dt.strftime("%Y-%m-%d %H:%M:%S")
                                    json_parse = True
                                    break
                    except Exception as e:
                        self.log("json解析失败")
                        self.log(e)
                        pass
                if not json_parse:
                    vod['vod_name'] = soup.title.text
                    vod['vod_content'] = vod['vod_name'] + '\n\n' + texts
                    author_name = soup.select('.screenName')[0].get_text()
                    vod['vod_director'] = self._get_text_link(author_url, author_name)
                    
            
        except Exception as e:
            self.log(f"detailContent error: {e}")
        return {'list': [vod]}

    def playerContent(self, flag, id, vipFlags):
        url = id
        if not url:
            return
        """
        try:
            self.header['Referer'] = url
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
        """
        return {'parse': 0, 'url': url, 'header': self.header}

    def searchContent(self, key, quick):
        result = {'list': []}
        try:
            search_url = f'{self.host}/search?q={key}'
            res = requests.get(search_url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            html_content = res.text
            res.encoding = 'utf-8'
            doc = pq(res.content)
            vods = self.parseVideoItems(doc)
            result['list'] = vods
        except Exception as e:
            print(f"searchContent error: {e}")
        return result
    
    def homeVideoContent(self):
        return
        try:
            url = self.host
            res = requests.get(url, headers=self.header, timeout=10)
            res.encoding = 'utf-8'
            html_content = res.text
            vods = None
            return {'list': vods}
        except Exception as e:
            print(f"homeVideoContent error: {e}")
            return {'list': []}
    
    def localProxy(self, params):
        return None
