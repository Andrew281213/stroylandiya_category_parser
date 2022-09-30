import asyncio
import os.path

import openpyxl

from utils.async_parser import Parser, ht
from utils.utils import PROXY_URLS


class Stroylandiya(Parser):
	def get_max_url(self, **kwargs):
		pass
	
	async def _get_start_urls(self):
		url = "https://stroylandiya.ru/catalog/"
		txt = await self.get_while_request(url)
		doc = ht.document_fromstring(txt)
		items = self.get_elements_by_xpath(doc, "//div[@class='fb-category-group-link__content']/a")
		for item in items:
			url = self.get_href(item)
			title = self.get_stripped_text(item.xpath(".//h2")[0])
			img = self.get_src(item.xpath("./../..//img")[0])
			self.data.append({
				"url": url,
				"title": title,
				"img": img
			})
	
	async def _get_additional_data(self, doc, parent):
		items = self.get_elements_by_xpath(doc, "//a[@class='fb-category-image-link']")
		for item in items:
			url = self.get_href(item)
			title = self.get_stripped_text(item.xpath("./div[@class='fb-category-image-link__name']")[0])
			img = self.get_src(item.xpath(".//img")[0])
			self.data.append({
				"url": url,
				"title": title,
				"img": img,
				"parent": parent
			})
	
	async def _get_additional_urls(self, item):
		async with self._semaphore:
			txt = await self.get_while_request(item["url"])
			doc = ht.document_fromstring(txt)
			parent = item["title"]
			await self._get_additional_data(doc, parent)
			self._progress_bar.update()
	
	async def get_products_data(self):
		if not os.path.isfile("data.json"):
			await self._get_start_urls()
			exist = []
			while True:
				tasks = []
				for item in self.data:
					if item["url"] not in exist:
						exist.append(item["url"])
						tasks.append(self._get_additional_urls(item))
				if len(tasks) == 0:
					break
				await self.start_tasks(tasks)
			self.to_json(self.data)
		else:
			self.data = self.from_json()


def save():
	data = Parser.from_json()
	wb = openpyxl.Workbook()
	sheet = wb.active
	sheet.append(["Название", "Изображение", "Родительская категория"])
	for item in data:
		sheet.append([item["title"], item["img"], item.get("parent")])
	wb.save("data.xlsx")


async def start():
	parser: Stroylandiya = await Stroylandiya.async_init(Stroylandiya)
	parser.base_url = "https://stroylandiya.ru"
	# parser.use_proxy_file = True
	# parser.load_proxy("../../proxies.txt")
	# await parser.load_proxy_from_urls(PROXY_URLS)
	# await parser.get_products_data()
	save()
	

if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	loop.run_until_complete(start())
