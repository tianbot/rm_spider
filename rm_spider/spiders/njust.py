import random
import re
import string
from urllib.parse import urljoin

import scrapy

from rm_spider.items import RmSpiderItem


def gen_request_id(length=12):
    return "req" + "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


class NjustSpider(scrapy.Spider):
    """爬取南京理工大学 2024 新长江杯 智能无人系统应用挑战赛赛事照片"""
    name = "njust"
    allowed_domains = ["www.pailixiang.com"]
    start_urls = ["https://www.pailixiang.com/m/album/main_ig73676720.html"]

    def parse(self, response, **kwargs):

        for album in response.css('.album_btn'):
            if href := album.css('::attr(href)').get():  # 获取 href 属性
                yield scrapy.Request(urljoin(response.url, href.replace("/m", "", 1)), callback=self.parse_album)

    def parse_album(self, response):

        if match := re.search(r'albumId:\s*"(\d+)"', response.text):
            url = f"https://www.pailixiang.com/Portal/Services/AlbumDetail.ashx?t=2&rid={gen_request_id()}"
            data = {
                "albumId": match.group(1),
                "groupId": "",
                "len": "1000",  # 一天不太可能有 1000 张照片，免得处理分页
                "from": "",
                "accessType": "1",
                "order": "0",
                "nw": "",
            }
            yield scrapy.FormRequest(url, formdata=data, callback=self.parse_album_detail)

    def parse_album_detail(self, response):

        data = response.json()
        if data.get("Message") != "查询成功！":
            self.logger.error(data["Message"])
            return

        if items := data.get("Data", []):
            yield RmSpiderItem(file_urls=[item["DownloadImageUrl"] for item in items])
