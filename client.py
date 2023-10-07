from time import sleep


class Client(object):

    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
        from splinter import Browser
        self.browser = Browser('chrome')

    def login(self, url='https://www.pornhubpremium.com/premium/login', homepage='https://www.pornhubpremium.com/'):
        browser = self.browser
        browser.visit(url)
        # age verification check
        if len(browser.find_by_css('.ageDisclaimer.isVisibleMTubes')) > 0:
            browser.find_by_css('#modalWrapMTubes > div > div > button').first.click()
        browser.find_by_css('#cookieBannerWrapper > .cbPrimaryCTA').click()
        browser.find_by_id('username').first.fill(self.username)
        browser.find_by_id('password').first.fill(self.password)
        # browser.find_by_id('remember_me').first.fill('on')
        browser.check('remember_me')
        sleep(0.1)  # Time in seconds
        browser.find_by_id('submitLogin'if 'pornhubpremium' in homepage else 'submit').first.click()
        tries = 0
        while browser.url != homepage:
            if tries > 10:
                raise RuntimeError('We can not reach the homepage')
            sleep(1)  # Time in seconds
            tries += 1
        return browser
