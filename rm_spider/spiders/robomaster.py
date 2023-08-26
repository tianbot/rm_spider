import re

import scrapy

from rm_spider.items import RmSpiderItem

P_TIME = re.compile(r'&?time=\d+')


class PicSpider(scrapy.Spider):
    name = 'pic'
    allowed_domains = ['m.inmuu.com']
    start_urls = [
        'https://m.inmuu.com/v1/srv/activityPhoto/getNewPhotoList/1838361?num=100&timeOrder=0',  # 2022
        'https://m.inmuu.com/v1/srv/activityPhoto/getNewPhotoList/3027711?num=100&timeOrder=0',  # 2023
    ]

    def parse(self, response, **kwargs):
        if response.status != 200:
            self.logger.error(f"status code: {response.status}")
            return
        data = response.json()
        if data['code'] != 0:
            self.logger.error(f"code: {data['msg']}")
            return
        items = data['data']['data']
        if not items:
            self.logger.info(f"no more items")
            return
        rm_item = RmSpiderItem()
        rm_item['file_urls'] = [item['originUrl'] for item in items]
        yield rm_item
        sshort = int(items[-1]['sshort'])
        if P_TIME.search(response.url):
            url = P_TIME.sub(f'&time={sshort}', response.url)
        else:
            url = f'{response.url}&time={sshort}'
        yield scrapy.Request(url=url, callback=self.parse)
