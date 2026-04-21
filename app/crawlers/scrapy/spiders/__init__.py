"""Scrapy spiders for university program crawling."""

from app.crawlers.scrapy.spiders.base_spider import BaseProgramSpider
from app.crawlers.scrapy.spiders.university_spider import UniversityProgramSpider

__all__ = ["BaseProgramSpider", "UniversityProgramSpider"]
