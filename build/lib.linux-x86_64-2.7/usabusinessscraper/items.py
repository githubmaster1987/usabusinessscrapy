# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class UsabusinessscraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    CompanyName = scrapy.Field()
    Country = scrapy.Field()
    City = scrapy.Field()
    State = scrapy.Field()
    Address = scrapy.Field()
    Zipcode = scrapy.Field()
    Category = scrapy.Field()
    Description = scrapy.Field()
    YearEstablished = scrapy.Field()
    Products = scrapy.Field()

    Tel = scrapy.Field()
    Fax = scrapy.Field()
    Email = scrapy.Field()
    Geolocation = scrapy.Field()
    Contact = scrapy.Field()
    URL = scrapy.Field()
