from time import sleep


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
        sleep(0.1)  # Time in seconds
        browser.find_by_id('submitLogin').first.click()
        tries = 0
        while browser.url != 'https://www.pornhubpremium.com/':
            if tries > 10:
                raise RuntimeError('We can not reach the homepage')
            sleep(1)  # Time in seconds
            tries += 1
        return browser
