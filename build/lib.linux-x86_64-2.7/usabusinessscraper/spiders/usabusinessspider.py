# -*- coding: utf-8 -*-
import scrapy
import os, urllib
import logging
from scrapy.http import Request, FormRequest
import re, random, base64
from usabusinessscraper.items import UsabusinessscraperItem
import proxylist
# from fake_useragent import UserAgent
from captcha2upload import CaptchaUpload
import StringIO
import time

captcha_api_key = "368777fb0a6378526d68c88569d730a0"

logger = logging.getLogger('usabusiness')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('log.txt')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


class UsabusinessspiderSpider(scrapy.Spider):
    # handle_httpstatus_list = [407]
    name = "usabusinessspider"
    #allowed_domains = ["www.usbizs.com"]
    start_urls = (
        'http://www.usbizs.com/',
    )

    state_index = 0
    state_sub_url_index = {}
    city_sub_url_index = {}
    proxy_lists = proxylist.proxys
    img_url = []

    def set_proxies(self, url, callback):
        req = Request(url=url, callback=callback, dont_filter=True)
        # proxy_url = self.proxy_lists[random.randrange(0,100)]
        # req.meta.update({'proxy': "https://" + proxy_url})
        # user_pass=base64.encodestring(b'user:p19gh1a').strip().decode('utf-8')
        # req.headers['Proxy-Authorization'] = 'Basic ' + user_pass
        #
        # user_agent = self.ua.random
        # req.headers['User-Agent'] = user_agent

        # req.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        # req.headers['Accept-Encoding'] = 'gzip, deflate'
        # req.headers['Accept-Language'] = 'en-US,en;q=0.8'
        # #req.headers['Cache-Control'] = 'max-age=0'
        # #req.headers['Connection'] = 'keep-alive'
        # #req.headers['Content-Length'] = '10'
        # req.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        # #req.headers['Cookie'] = 'PHPSESSID=hpfta0h8imb3ma3obdp2vrc0d5; md5key=6f6c7f62bc57227e14c85c85d117c591; CNZZDATA5849826=cnzz_eid%3D326421496-1485428248-%26ntime%3D1485523483'
        # req.headers['Host'] = 'www.usbizs.com'
        # req.headers['Origin'] = "http://www.usbizs.com"
        # req.headers['Upgrade-Insecure-Requests'] = "1"
        # print ('&&&&&&&&&&&&&&&&&&&&&&&&&', url)
        return req

    def start_requests(self):
        # self.ua = UserAgent()
        start_url = self.start_urls[0]
        yield self.set_proxies(start_url, self.parse_item)
        #yield self.set_proxies(start_url, self.parse_detail)

    def parse(self, response):
        yield Request(response.url, self.parse_item)

    def check_captch(self, response):
        self.img_url = response.xpath('//img[contains(@src,"code.php")]/@src').extract()

        if len(self.img_url) > 0:
            req =  Request(response.urljoin(self.img_url[0]), self.solve_captcha, dont_filter=True)
            print ("CCCCCCCCCCCCCCCCCCCCCCCCCCC", response.url)
            req.meta["call_url"] = response.url
            req.meta["callback"] = response.meta["callback"]
            return req

    def solve_captcha(self, response):
        filename = "captcha.png"
        output = open(filename, "wb")
        output.write(response.body)
        output.close()
        captcha = CaptchaUpload(captcha_api_key)
        captcha_code = captcha.solve(filename)
        #captcha_code = "sdfsdsdf"
        formdata = {'code': captcha_code, 'method': 'post'}
        # print ("...............................", response.meta["callback"])
        # print ("...............................", response.meta["call_url"])
        yield FormRequest(response.meta["call_url"],formdata=formdata, callback=response.meta["callback"], dont_filter=True)

    def parse_item(self, response):
        # print ("^^^^^^^^^^^^^^^^^^^^^^^^^^^^", response.headers)
        state_div = response.xpath("//div[@class='bizrmainc']//li")
        # print ("&&&&&&&&&&&&&&&&&&&&&", state_div.extract())
        if len(state_div) == 0:
            req =  Request(response.url, self.check_captch, dont_filter=True)
            req.meta["callback"] = self.parse_item

            yield req

        else:
            for row in state_div:
                state_url = row.xpath('a/@href').extract()
                if len(state_url) > 0:
                    state = state_url[0].split("/")[0]
                    self.state_sub_url_index[state] = 1
                    url = response.urljoin(state + "/index.html")
                    # print ("++++++++++++++++++++++++++++++++++", url)
                    req = self.set_proxies(url, self.parse_city)
                    req.meta["state_code"] = state
                    req.meta["home_url"] = response.url

                    yield req

    def parse_city(self, response):
        state_code = response.meta["state_code"]
        home_url = response.meta["home_url"]

        city_div = response.xpath("//div[@class='statel']/ul/li")

        if len(city_div) == 0:
            req =  Request(response.url, self.check_captch, dont_filter=True)
            req.meta["callback"] = self.parse_city

            yield req

        else:
            for row in city_div:
                city_url = row.xpath('a/@href').extract()
                city = row.xpath('a/text()').extract()
                if len(city) > 0:
                    url = response.urljoin(city_url[0])
                    # print ("----------------------------------------", url)
                    req = self.set_proxies(url, self.parse_detail)
                    req.meta["home_url"] = home_url
                    req.meta["city"] = city[0]
                    req.meta["state"] = state_code
                    self.city_sub_url_index[city[0]] = 1

                    yield req

            self.state_sub_url_index[state_code] = self.state_sub_url_index[state_code] + 1
            call_url = home_url + state_code + "/index-" + str(self.state_sub_url_index[state_code]) +".html"
            req = self.set_proxies(call_url, self.parse_city)
            req.meta["home_url"] = home_url
            req.meta["state_code"] = state_code

            yield req

    def parse_detail(self, response):

        company_div = response.xpath("//div[@class='bizrmainc']/div//td[@class='listt']")

        if len(company_div) == 0:
            req =  Request(response.url, self.check_captch, dont_filter=True)
            req.meta["callback"] = self.parse_detail

            yield req

        else:
            for row in company_div:
                company_url = row.xpath('a/@href').extract()

                if len(company_url) > 0:
                    url = response.urljoin(company_url[0])
                    # print ("======================================", url)
                    req = self.set_proxies(url, self.parse_company)

                    yield req

            city = response.meta["city"]
            state_code = response.meta["state"]
            home_url = response.meta["home_url"]

            self.city_sub_url_index[city] = self.city_sub_url_index[city] + 1
            call_url = home_url + state_code + "/" + city +  "-" + str(self.city_sub_url_index[city]) +".html"
            req = self.set_proxies(call_url, self.parse_detail)
            req.meta["home_url"] = home_url
            req.meta["city"] = city
            req.meta["state"] = state_code

            yield req

    def parse_company(self, response):

        item = UsabusinessscraperItem()
        company_profile_div = response.xpath('//div[contains(text(),"Company Profile")]/..')
        # print ("RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR", len(company_profile_div))
        if len(company_profile_div) == 0:
            req =  Request(response.url, self.check_captch, dont_filter=True)
            req.meta["callback"] = self.parse_company

            yield req

        else:
            row = company_profile_div[0]
            company_name = row.xpath('//span[@itemprop="name"]/text()').extract()
            country = row.xpath('//span[@itemprop="addressCountry"]/text()').extract()
            city = row.xpath('//span[@itemprop="addressLocality"]/text()').extract()
            state = row.xpath('//span[@itemprop="addressRegion"]/text()').extract()
            address = row.xpath('//span[@itemprop="streetAddress"]/text()').extract()
            postal_code = row.xpath('//span[@itemprop="postalCode"]/text()').extract()

            category = row.xpath('//ul/li/strong[contains(text(),"Category")]/../text()').extract()
            description = row.xpath('//ul/li/strong[contains(text(),"Description")]/../text()').extract()
            product = row.xpath('//ul/li/strong[contains(text(),"Product")]/../text()').extract()

        company_contact_div = response.xpath('//div[contains(text(),"Contact Info")]/..')

        if len(company_contact_div) == 0:
            req =  Request(response.url, self.check_captch, dont_filter=True)
            req.meta["callback"] = self.parse_company

            yield req

        if len(company_contact_div) > 0:
            row =  company_contact_div[0]
            contact = row.xpath('//ul/li/strong[contains(text(),"Contact")]/../text()').extract()
            tel = row.xpath('//span[@itemprop="telephone"]/text()').extract()
            email = row.xpath('//span[@itemprop="email"]/text()').extract()
            fax = row.xpath('//span[@itemprop="faxNumber"]/text()').extract()

            geolocation = ""
            scripts = response.xpath('//script/text()').extract()
            for script in scripts:
                values = re.search(r'google.maps.LatLng\((.*?)\);', script, re.M|re.I|re.S)
                if values is not None:
                    geolocation = values.group(1)

        if len(company_contact_div) > 0 and len(company_profile_div) > 0:
            item["CompanyName"] = " ".join(company_name)
            item["Country"] = country
            item["City"] = city
            item["State"] = state
            item["Address"] = address
            item["Zipcode"] = postal_code
            item["Category"] = category
            item["Description"] = description
            item["YearEstablished"] = ""
            item["Products"] = product

            item["Tel"] = tel
            item["Fax"] = fax
            item["Email"] = email
            item["Geolocation"] = geolocation
            item["Contact"] = contact
            item["URL"] = response.url

            yield item
