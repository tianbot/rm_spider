import random
import re
import string
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import scrapy

from rm_spider.settings import FILES_STORE

PAGE_SIZE = 1000


def gen_request_id(length=12):
    return "req" + "".join(
        random.choices(string.ascii_lowercase + string.digits, k=length)
    )


class NjustSpider(scrapy.Spider):
    """爬取南京理工大学 2024 新长江杯 智能无人系统应用挑战赛赛事照片"""

    name = "njust"
    allowed_domains = ["pailixiang.com"]
    start_urls = ["https://www.pailixiang.com/m/album/main_ig73676720.html"]

    def parse(self, response, **kwargs):
        for album in response.css(".album_btn"):
            if href := album.css("::attr(href)").get():  # 获取 href 属性
                yield scrapy.Request(
                    urljoin(response.url, href.replace("/m", "", 1)),
                    callback=self.parse_album,
                )

    def parse_album(self, response):
        if match := re.search(r'albumId:\s*"(\d+)"', response.text):
            url = f"https://www.pailixiang.com/Portal/Services/AlbumDetail.ashx?t=2&rid={gen_request_id()}"
            data = {
                "albumId": match.group(1),
                "groupId": "",
                "len": str(PAGE_SIZE),
                "from": "",
                "accessType": "1",
                "order": "0",
                "nw": "",
            }
            yield scrapy.FormRequest(
                url,
                formdata=data,
                callback=self.parse_album_detail,
                meta={"albumId": data["albumId"]},
            )

    def parse_album_detail(self, response):
        data = response.json()
        if data.get("Message") != "查询成功！":
            self.logger.error(data["Message"])
            return

        for item in data.get("Data", []):
            user = item.get("CreateUserName")
            # 2024-07-31 15:42:03 -> YYYYMMDD_HHMMSS
            shoot_time = datetime.strptime(
                item["ShootTime"], "%Y-%m-%d %H:%M:%S"
            ).strftime("%Y%m%d_%H%M%S")
            save_dir = Path(FILES_STORE) / self.name / shoot_time.split("_")[0]
            if not save_dir.exists():
                save_dir.mkdir(parents=True)
            save_path = save_dir / f"{shoot_time}_{user}.jpg"
            if not save_path.exists():
                yield scrapy.Request(
                    item["DownloadImageUrl"],
                    callback=self.parse_image,
                    meta={"save_path": save_path.as_posix()},
                )

        if (total_count := data.get("TotalCount", 0)) and "albumId" in response.meta:
            url = f"https://www.pailixiang.com/Portal/Services/AlbumDetail.ashx?t=1&rid={gen_request_id()}"
            for page in range(1, total_count // PAGE_SIZE + 1):
                data = {
                    "albumId": response.meta["albumId"],
                    "groupId": "",
                    "len": str(PAGE_SIZE),
                    "from": "",
                    "order": "0",
                    "nw": "",
                    "start": str(page * PAGE_SIZE + 1),
                    "optTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                yield scrapy.FormRequest(
                    url, formdata=data, callback=self.parse_album_detail
                )

    @staticmethod
    def parse_image(response):
        with open(response.meta["save_path"], "wb") as fp:
            fp.write(response.body)
