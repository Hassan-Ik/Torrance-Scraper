import scrapy
import os
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy_splash import SplashRequest
import random
import json
import time

class TorrancemembershipSpider(CrawlSpider):
    name = 'torrancemembership'
    allowed_domains = ['www.torrancechamber.com']
    start_urls = ['http://www.torrancechamber.com/']

    rules = (
        Rule(LinkExtractor(allow=r'Items/'), callback='parse_item', follow=True),
    )
    
    # For using current project path to open config.json file
    current_path = os.getcwd()
    current_path = current_path.replace("\\", "/")
    current_path = os.path.join(current_path, "torrancechamber")
    config_file = os.path.join(current_path, "config.json")
    config_file = config_file.replace("\\", "/")
    
    script = """
        function main(splash, args)
            assert(splash:go(args.url))
            assert(splash:wait(args.wait))
            treat=require("treat")
            result = {}
            assert(splash:runjs("document.querySelector(".chosen-container.chosen-container-single").click()"))
            assert(splash:wait(args.wait))
            assert(splash:runjs("document.getElementsByClassName(".chosen-search-input")[0].value = args.category)
            assert(splash:wait(args.wait))
            assert(splash:runjs("if(document.getElementsByClassName("no-results").length) == 0 {document.querySelector(".active-result.cn-term-level-0.highlighted").click()}"))
            assert(splash:wait(args.wait))
            result = splash:html()
            return treat.as_array(result)
        end
    """
    
    with open(config_file) as cf:
        con_f = json.load(cf)
    
    categories = con_f["categories"]
    random_wait_list = con_f["wait"]
    
    url = "https://www.torrancechamber.com/member-directory/"
    
    def start_requests(self):
        yield SplashRequest(url=self.url,  callback=self.parse, endpoint="render.html", args={"wait": random.choice(self.random_wait_list)})
        
    def parse(self, response):
        if self.categories == None or self.categories == []:
            no_of_pages = self.get_no_of_pages(response)
            for company_div in response.xpath("//div[@data-entry-type = 'organization']"):
                company_contact = [
                    company_div.xpath(".//span[@class='cn-contact-block']/span[3]/text()").extract_first(), company_div.xpath(".//span[@class='cn-contact-block']/span[4]/text()").extract_first()
                ]
                company_contact = [x for x in company_contact if x is not None]
                
                if company_contact == []:
                    company_contact = "N/A"
                else:
                    company_contact = ' '.join(company_contact)
                
                company_address = [
                    company_div.xpath(".//span[@class='address-block']/span/span[2]/text()").extract_first(),
                    company_div.xpath(".//span[@class='address-block']/span/span[3]/text()").extract_first(),
                    company_div.xpath(".//span[@class='address-block']/span/span[4]/text()").extract_first(),
                    company_div.xpath(".//span[@class='address-block']/span/span[5]/text()").extract_first()
                                   ]
                company_address = [x for x in company_address if x is not None]
                
                if company_address == []:
                    company_address = "N/A"
                else:
                    company_address = ' '.join(company_address)
                
                yield {
                    "company": company_div.xpath(".//h2/a/span/text()").extract_first(),
                    "company_logo_url": company_div.css("div > div > div > span.cn-image-style > span > a > img::attr(srcset)").extract_first(),
                    "company_url": company_div.css("div > div > div > span.cn-image-style > span > a::attr(href)").extract_first(),
                    "company_contact": company_contact,
                    "company_address": company_address,
                    "company_telephone": company_div.xpath(".//span[@class='phone-number-block']/span/a/text()").extract_first(),
                    "company_email": company_div.xpath(".//span[@class='email-address-block']/span/span[3]/a/text()").extract_first(),
                    "company_website": company_div.xpath(".//span[@class='link-block']/span/a/text()").extract_first(),
                    "company_category": company_div.css("::attr(class)").extract_first().split(" ")[-1]
                }
            for i in range(2, no_of_pages):
                url = response.request.url
                url = url.split("pg")[0]
                url = url + f"pg/{i}/"
                time.sleep(random.choice(self.random_wait_list))
                yield scrapy.Request(url=url,  callback=self.parse_other_pages)
        else:
             for category in self.categories:
                 yield SplashRequest(url=self.url, callback=self.parse_category_page, endpoint="execute", args={"wait": random.choice(self.random_wait_list), "lua_source": self.script, "category": category}, dont_filter=True)
                            
        
    def parse_category_page(self, response):
        no_of_pages = self.get_no_of_pages(response)
        for company_div in response.xpath("//div[@data-entry-type = 'organization']"):
            company_category = company_div.xpath("/@class")
            print(company_category)
            company_contact = [
                company_div.xpath(".//span[@class='cn-contact-block']/span[3]/text()").extract_first(), company_div.xpath(".//span[@class='cn-contact-block']/span[4]/text()").extract_first()
            ]
            company_contact = [x for x in company_contact if x is not None]
            
            if company_contact == []:
                company_contact = "N/A"
            else:
                company_contact = ' '.join(company_contact)
            
            company_address = [
                company_div.xpath(".//span[@class='address-block']/span/span[2]/text()").extract_first(),
                company_div.xpath(".//span[@class='address-block']/span/span[3]/text()").extract_first(),
                company_div.xpath(".//span[@class='address-block']/span/span[4]/text()").extract_first(),
                company_div.xpath(".//span[@class='address-block']/span/span[5]/text()").extract_first()
                                ]
            company_address = [x for x in company_address if x is not None]
            
            if company_address == []:
                company_address = "N/A"
            else:
                company_address = ' '.join(company_address)
            
            yield {
                    "company": company_div.xpath(".//h2/a/span/text()").extract_first(),
                    "company_logo_url": company_div.css("div > div > div > span.cn-image-style > span > a > img::attr(srcset)").extract_first(),
                    "company_url": company_div.css("div > div > div > span.cn-image-style > span > a::attr(href)").extract_first(),
                    "company_contact": company_contact,
                    "company_address": company_address,
                    "company_telephone": company_div.xpath(".//span[@class='phone-number-block']/span/a/text()").extract_first(),
                    "company_email": company_div.xpath(".//span[@class='email-address-block']/span/span[3]/a/text()").extract_first(),
                    "company_website": company_div.xpath(".//span[@class='link-block']/span/a/text()").extract_first(),
                    "company_category": company_div.css("::attr(class)").extract_first().split(" ")[-1]
                }
        
        for i in range(2, no_of_pages):
            url = response.request.url
            url = url.split("pg")[0]
            url = url + f"pg/{i}/"
            time.sleep(random.choice(self.random_wait_list))
            yield scrapy.Request(url=url,  callback=self.parse_other_pages)
    
    def parse_other_pages(self, response):
        for company_div in response.xpath("//div[@data-entry-type = 'organization']"):
                company_contact = [
                    company_div.xpath(".//span[@class='cn-contact-block']/span[3]/text()").extract_first(), company_div.xpath(".//span[@class='cn-contact-block']/span[4]/text()").extract_first()
                ]
                company_contact = [x for x in company_contact if x is not None]
                
                if company_contact == []:
                    company_contact = "N/A"
                else:
                    company_contact = ' '.join(company_contact)
                
                company_address = [
                    company_div.xpath(".//span[@class='address-block']/span/span[2]/text()").extract_first(),
                    company_div.xpath(".//span[@class='address-block']/span/span[3]/text()").extract_first(),
                    company_div.xpath(".//span[@class='address-block']/span/span[4]/text()").extract_first(),
                    company_div.xpath(".//span[@class='address-block']/span/span[5]/text()").extract_first()
                                   ]
                company_address = [x for x in company_address if x is not None]
                
                if company_address == []:
                    company_address = "N/A"
                else:
                    company_address = ' '.join(company_address)
                
                yield {
                    "company": company_div.xpath(".//h2/a/span/text()").extract_first(),
                    "company_logo_url": company_div.css("div > div > div > span.cn-image-style > span > a > img::attr(srcset)").extract_first(),
                    "company_url": company_div.css("div > div > div > span.cn-image-style > span > a::attr(href)").extract_first(),
                    "company_contact": company_contact,
                    "company_address": company_address,
                    "company_telephone": company_div.xpath(".//span[@class='phone-number-block']/span/a/text()").extract_first(),
                    "company_email": company_div.xpath(".//span[@class='email-address-block']/span/span[3]/a/text()").extract_first(),
                    "company_website": company_div.xpath(".//span[@class='link-block']/span/a/text()").extract_first(),
                    "company_category": company_div.css("::attr(class)").extract_first().split(" ")[-1]
                }

    def get_no_of_pages(self, response):
        for pag_nav in response.xpath("//div[@class='cn-list-foot']"):
            page_number = pag_nav.xpath("//a[@class='page-numbers']/text()").extract()
            if len(page_number) > 0:
                page_number = page_number[-1]
                page_number = int(page_number)
                return page_number
            else:
                return 0
    
    
    def parse_item(self, response):
        item = {}
        #item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
        #item['name'] = response.xpath('//div[@id="name"]').get()
        #item['description'] = response.xpath('//div[@id="description"]').get()
        return item
