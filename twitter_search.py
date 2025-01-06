import os
import time
import jsonlines
from datetime import datetime
import configurations as config
from bs4 import BeautifulSoup
from selenium import webdriver
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import random

DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 3
SCROLL_HEIGHT = 10

LOGIN_URL = os.environ.get('LOGIN_URL')
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
PASSWORD = os.environ.get('PASSWORD')
USERNAME = os.environ.get('USERNAME')

login_url = 'https://x.com/i/flow/login'
email_address = 'bidemi.ajiboye@gmail.com'
password = 'Businessweek$123'
username = 'carliecode'
logger = config.setup_logging()

def get_random_user_agent() -> str:
    ua = UserAgent()
    agent = ua.random
    logger.info(f"Initiating user agent, {agent} ...")
    return agent

def configure_chrome_driver() -> webdriver.Chrome:
    try:
        logger.info("Configuring Chrome ...")
        options = ChromeOptions()
        #options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--enable-unsafe-swiftshader")
        options.add_argument('--disable-devtools')
        options.add_argument(f"user-agent={get_random_user_agent()}")       
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(120)
        return driver
    except Exception as e:
        logger.error(f"configure_chrome_driver(): {str(e)}")
        raise

def restart_driver(driver: webdriver.Chrome ) -> webdriver.Chrome:    
    if driver.service.process.poll() is not None:
        logger.info("WebDriver is disconnected. Restarting...")
        driver.quit()
        driver = configure_chrome_driver() 
    return driver

def is_logged_in(driver: webdriver.Chrome) -> bool:
    try: 
        profile_link = BeautifulSoup(driver.page_source, 'html.parser').find('a', class_='css-175oi2r r-6koalj r-eqz5dr r-16y2uox r-1habvwh r-13qz1uu r-1mkv55d r-1ny4l3l r-1loqt21', attrs={'aria-label':'Profile', '':''})
        if profile_link:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"is_logged_in(): {str(e)}")
        raise

def login_to_X(driver: webdriver.Chrome, login_url: str, email_address: str, user_name: str, password: str, browser_number: int = 1) -> webdriver.Chrome:
    try:
        
        if not is_logged_in(driver):
            driver = restart_driver(driver)
            driver.get(login_url)
            logger.info(f"Logging in from Browser ({browser_number})...")
            time.sleep(3)  
            
            input_field = driver.find_element(By.XPATH, "//input[@name='text']")   
            input_field.send_keys(email_address)   
            next_button = driver.find_element(By.XPATH, "//button[contains(., 'Next')]")   
            next_button.click()
            time.sleep(3)  

            try:
                input_field = driver.find_element(By.XPATH, "//input[@name='text']")   
                input_field.send_keys(username)   
                next_button = driver.find_element(By.XPATH, "//button[contains(., 'Next')]")   
                next_button.click()
                time.sleep(3)
            except NoSuchElementException as e:
                pass

            password_input = driver.find_element(By.XPATH, "//input[@name='password']")  
            password_input.send_keys(password)  
            login_button = driver.find_element(By.XPATH, "//span[contains(., 'Log in')]")  
            login_button.click()
            time.sleep(3)

        return driver
        
    except Exception as e:
        logger.error(f"login_to_twitter(): {str(e)}")
        raise e

def get_tweets(driver: webdriver.Chrome, query: str, number_of_tweets: int, scroll_index: int, retries: int = DEFAULT_RETRIES, backoff: int = DEFAULT_BACKOFF) -> list:
    tweets = []
    tweet = {}
    browser = webdriver.Chrome()
    content_scroll_index = scroll_index

    try:
        #if not is_logged_in(driver): 
        driver = login_to_X(driver, login_url, email_address, username, password)
        browser = login_to_X(browser, login_url, email_address, username, password, 2)
        
        if driver is not None:
            driver.get(f"https://x.com/search?q={query}&src=typed_query&f=live")
            time.sleep(3)
        else:
            logger.error("Driver is None")
            raise Exception("Driver is None")
        
        
        

        if content_scroll_index > 0:
            for i in range(content_scroll_index):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
        
        content_element = driver.find_element(By.TAG_NAME, 'body')
        while len(tweets) < number_of_tweets:
                        
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            tweet_tags = soup.find_all('div', class_='css-175oi2r', attrs={'data-testid': 'cellInnerDiv'})
            
            for tag in tweet_tags:
                anchor = tag.find('a', class_='css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-16dba41 r-xoduu5 r-1q142lx r-1w6e6rj r-9aw3ui r-3s2u2q r-1loqt21', attrs={'role': 'link'})
                tweet_url = f'https://x.com{anchor.get("href")}'

                tweet = read_tweet(browser, tweet_url)
                if (tweet not in tweets) and (tweet['tweet_text'] is not None):
                    tweets.append(tweet)
                    datalog.info(f"Tweet: {tweet}")
            
            for i in range(SCROLL_HEIGHT):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
            
            content_scroll_index = content_scroll_index + SCROLL_HEIGHT
            if driver.execute_script('return document.body.scrollHeight') == driver.execute_script('return window.scrollY + window.innerHeight'):
                break
        
        logger.info(f"Fetched a total of {len(tweets)} tweets")
    except Exception as e:
        if retries > 0:
            wait_time = random.uniform(backoff, backoff * 2)
            logger.error(f'Browser is disconnected within get_tweets()')
            logger.info(f"Retrying get_tweets() {'again' if retries < 3 else '' } in {wait_time}s... ({retries - 1} retries left)")
            time.sleep(wait_time)
            driver = configure_chrome_driver()
            result = get_tweets(driver, query, number_of_tweets, content_scroll_index, retries - 1, backoff)
            logger.info(f'get_tweets() retry successful')
            return result
        else:
            logger.info(f"get_tweets() failed after {DEFAULT_RETRIES} attempts")
            logger.error(f"get_tweets(): {str(e)}")
            raise e
    finally:
        browser.quit()
        driver.quit()    
    return tweets

def read_tweet(browser: webdriver.Chrome, url: str, retries: int = DEFAULT_RETRIES, backoff: int = DEFAULT_BACKOFF) -> dict:
    try:
        browser.get(url)
        time.sleep(3)
        soup = BeautifulSoup(browser.page_source, "html.parser")
        tweet = {}

        try:
            user_name_soup = soup.find('div', class_='css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-b88u0q r-1awozwy r-6koalj r-1udh08x r-3s2u2q')
            if user_name_soup:
                user_name_soup = user_name_soup.find('span', class_='css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3')
            tweet_text_soup = soup.find('div', attrs={'data-testid':'tweetText'} ,class_='css-146c3p1 r-bcqeeo r-1ttztb7 r-qvutc0 r-37j5jr r-1inkyih r-16dba41 r-bnwqim r-135wba7')
        except Exception as e:
            pass
       
        tweet['username'] = user_name_soup.text if user_name_soup else None
        tweet['tweet_text'] = tweet_text_soup.find('span', class_='css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3').text if tweet_text_soup else None
        tweet['language'] = tweet_text_soup.get('lang') if tweet_text_soup else None
        tweet['tweet_time'] = soup.find('time').get('datetime') if soup.find('time') else None
        tweet['url'] = url  
        return tweet
    except WebDriverException  as e:
        if retries > 0:
            wait_time = random.uniform(backoff, backoff * 2)
            logger.error(f'Browser is disconnected within get_tweets()')
            logger.info(f"Retrying read_tweet() {'again' if retries < 3 else '' } in {wait_time}s... ({retries - 1} retries left)")
            time.sleep(wait_time)
            driver = configure_chrome_driver()
            result = read_tweet(browser, url, retries - 1, backoff)
            logger.info(f'read_tweet() retry successful')
            return result
        else:
            logger.info(f"read_tweet() failed after {DEFAULT_RETRIES} attempst")
            logger.error(f"Error in read_tweet(): {str(e)}")
            return {} 
    

def execute() -> None:
    driver = webdriver.Chrome()
    try:
        driver = configure_chrome_driver()
        driver = login_to_X(driver, login_url, email_address, username, password)
        tweets = get_tweets(driver, 'stress management', 1000, 0)
        print(tweets)
    except Exception as e:
        logger.error(f"Error in execute(): {str(e)}")
    finally:
        driver.quit()
        logger.info(f"X posts collector is exiting, is exiting.")


if __name__ == '__main__':
    execute()
