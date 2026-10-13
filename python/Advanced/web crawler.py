# spider.py
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

class ProductSpider(CrawlSpider):
    name = 'product_spider'
    allowed_domains = ['example.com']
    start_urls = ['http://example.com/products']
    
    rules = (
        Rule(LinkExtractor(allow=r'/products/page/'), callback='parse_product', follow=True),
        Rule(LinkExtractor(allow=r'/product/'), callback='parse_product_detail'),
    )
    
    def parse_product(self, response):
        for product in response.css('div.product'):
            yield {
                'title': product.css('h2::text').get(),
                'price': product.css('.price::text').get(),
                'url': response.urljoin(product.css('a::attr(href)').get()),
            }
    
    def parse_product_detail(self, response):
        yield {
            'title': response.css('h1::text').get(),
            'price': response.css('.price::text').get(),
            'description': response.css('.description::text').get(),
            'sku': response.css('.sku::text').get(),
            'url': response.url,
        }

# items.py
import scrapy

class ProductItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()
    description = scrapy.Field()
    sku = scrapy.Field()
    url = scrapy.Field()

# pipelines.py
class ProductPipeline:
    def process_item(self, item, spider):
        if item.get('price'):
            item['price'] = item['price'].replace('$', '').strip()
        return item

# settings.py
BOT_NAME = 'crawler'
SPIDER_MODULES = ['crawler.spiders']
USER_AGENT = 'MyBot (+http://example.com/bot)'
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 1
ITEM_PIPELINES = {'crawler.pipelines.ProductPipeline': 300}
FEED_FORMAT = 'json'
FEED_URI = 'output.json'

# Run: scrapy crawl product_spider -o products.json
