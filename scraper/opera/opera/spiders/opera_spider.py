from scrapy.spider import Spider
from scrapy.http import Request, FormRequest
from scrapy.selector import Selector
from scrapy.shell import inspect_response
from scrapy.utils.response import open_in_browser
from scrapy import log
from opera.items import SpectacleItem, ReprItem, SeatsItem
from opera import secrets
import urlparse
from datetime import datetime
import locale
import json
import re


def parse_spectacle_url(url):
    """Return the path part of the URL as an id, and remove fragment and query parts for the URL itself"""
    u = urlparse.urlsplit(url)
    return (u.path[1:], urlparse.urlunsplit((u.scheme, u.netloc, u.path, '', '')))


class OperaSpider(Spider):
    name = "opera"
    allowed_domains = ["operadeparis.fr"]

    start_urls = ["https://billetterie.operadeparis.fr/account"]
    disponibility_url = "https://www.operadeparis.fr/_secutix_greg_node_spectacle_dispos"
    spectacles_lists = {
        "http://www.operadeparis.fr/saison-2013-2014/opera": "opera",
        "http://www.operadeparis.fr/saison-2013-2014/ballet": "ballet",
        "http://www.operadeparis.fr/saison-2014-2015/opera": "opera",
        "http://www.operadeparis.fr/saison-2014-2015/ballet": "ballet",
    }

    def parse(self, response):
        return [FormRequest.from_response(response,
                            formdata={'login': secrets.OPERA_USER,
                                      'password': secrets.OPERA_PASSWORD,
                                     },
                            callback=self.after_login)]

    def after_login(self, response):
        locale.setlocale(locale.LC_TIME, "fr_FR.utf8")
        sel = Selector(response)
        error_msg = sel.css("#error_message_container").extract()
        if error_msg:
            self.log("Login failed : " + error_msg[0], level=log.ERROR)
            return
        return [Request(self.disponibility_url, callback=self.parse_disponibility)]

    def parse_disponibility(self, response):
        self.disponibility = json.loads(response.body_as_unicode())
        for sl, stype in self.spectacles_lists.items():
            req = Request(sl, callback=self.parse_spectacle_list)
            req.meta['stype'] = stype
            yield req

    def parse_spectacle_list(self, response):
        sel = Selector(response)
        spectacles = sel.css('#genre_liste .views-row')
        for spectacle in spectacles:
            url = spectacle.css('.views-field-title span a').xpath('@href')[0].extract()
            req = Request(url, callback=self.parse_spectacle_page)
            req.meta['stype'] = response.meta['stype']
            yield req

    def _is_disponible(self, product_id):
        if product_id == "0":
            return False
        try:
            disp_status = self.disponibility[product_id]
            return disp_status == "GOOD"
        except KeyError:
            return False

    def parse_spectacle_page(self, response):
        sel = Selector(response)
        name = sel.css('.H1.title').xpath('text()')[0].extract()
        if name.isupper():
            name = name.title()
        location = sel.css("span.lieux::text")[0].extract().strip()
        item = SpectacleItem()
        item["name"] = name
        item["name_id"], item["url"] = parse_spectacle_url(response.url)
        item["location"] = location
        item['stype'] = response.meta['stype']
        yield item

        for month in sel.css('#calendrier .mois'):
            month_year = month.css(".mois_titre::text")[0].extract().strip()
            for day in month.css(".jour.plein"):
                day_of_month = day.xpath("text()")[0].extract().strip()
                for time in day.css(".reserver"):
                    hour = time.css("::text")[0].extract().strip()
                    datestr = u"{} {} {}".format(day_of_month, month_year, hour).encode("utf-8")
                    date = datetime.strptime(datestr, "%d %B %Y %H:%M")
                    repr_item = ReprItem()
                    repr_item["date"] = date
                    repr_item["spectacle"] = item
                    time_classes = time.xpath("@class")[0].extract().split()
                    product_id = filter(lambda el: re.match(r'\d+', el), time_classes)[0]
                    if self._is_disponible(product_id):
                        res_url = "https://billetterie.operadeparis.fr/secured/selection/event/seat?perfId={}".format(product_id)
                        repr_item["url"] = res_url
                        request = Request(res_url, callback=self.parse_representation)
                        request.meta["item"] = repr_item
                        yield request
                    else:
                        repr_item["seats"] = []
                        repr_item["url"] = ""
                        yield repr_item

    def parse_representation(self, response):
        sel = Selector(response)
        item = response.meta["item"]
        item["seats"] = []
        for row in sel.css("table tr.group_start"):
            if row.css(".category_unavailable"):
                continue
            si = SeatsItem()
            si["category"] = row.css("td.category").xpath("text()[2]")[0].extract().strip()
            price_int = int(row.css("td.unit_price span.int_part::text")[0].extract())
            price_dec = int(row.css("td.unit_price span.mantissa::text")[0].extract())
            si["price"] = price_int + price_dec / 100.
            si["quantity"] = max(map(int, row.css("td.quantity option::attr(value)").extract()))
            si["zones"] = map(lambda s:s.capitalize(), row.css("td.area option[class]::text").extract())
            item["seats"].append(si)
        return item
