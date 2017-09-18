DOWNLOADER_MIDDLEWARES = {
        'scrapy.contrib.downloadermiddleware.retry.RetryMiddleware': 90,
        'tutorial.randomproxy.RandomProxy': 100,
        'scrapy.contrib.downloadermiddleware.httpproxy.HttpProxyMiddleware': 110,
        'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware' : None,
        'tutorial.spiders.rotate_useragent.RotateUserAgentMiddleware' :400,

    }