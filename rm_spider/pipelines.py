# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from urllib.parse import urlparse

# useful for handling different item types with a single interface
from scrapy.pipelines.files import FilesPipeline


class RmSpiderPipeline(FilesPipeline):

    def file_path(self, request, response=None, info=None, *, item=None):
        if self.spiderinfo.spider.name == "njust":
            return urlparse(request.url).path.split("/", 2)[-1]
        return '_'.join(request.url.rsplit('/', 3)[-3:])
