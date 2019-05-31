from urllib import parse
import requests


class Client(object):

    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password

    def login(self):
        from splinter import Browser
        browser = Browser('chrome')
        browser.visit('https://www.pornhubpremium.com/premium/login')
        browser.find_by_id('username').first.fill(self.username)
        browser.find_by_id('password').first.fill(self.password)
        # browser.find_by_id('remember_me').first.fill('on')
        browser.check('remember_me')
        browser.find_by_id('submitLogin').first.click()
        #
        # url = 'https://www.pornhubpremium.com/front/authenticate'
        #
        # posts = {
        #     'username': self.username,
        #     'password': self.password,
        #     # 'remember_me': 'on',
        #     'remember_me': True,
        #     # 'email': None,
        #     # 'mobile': None,
        #     # 'account': None,
        #     # 'captcha': capthcha
        # }
        # url_parse = parse.urlsplit(url)
        # headers = {
        #     "Host": url_parse.netloc,
        #     'X-SS-TC': "0",
        #     'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
        #     'Accept-Encoding': "gzip",
        #     'Connection': "keep-alive",
        #     'X-Tt-Token': "",
        #     'sdk-version': "1",
        # }
        # response = requests.post(url, headers=headers, data=posts)
        # return response
        return None
