#!.env/bin/python

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import sys
import csv


def contentPresentInPage():
	expand_buttons = [button 
			  	for button in browser.find_elements(By.CSS_SELECTOR, "span.cl-button__label")
			  	if "Expand" == button.text
			  	]
	if len(expand_buttons) == 0:
		return False
	else:
		return True


def getDataFromPage():
	data = []
	expand_buttons = [button 
			  	for button in browser.find_elements(By.CSS_SELECTOR, "span.cl-button__label")
			  	if "Expand" == button.text
			  	]
	wait = WebDriverWait(browser,30)
	time.sleep(1)
	for button in expand_buttons:
		browser.execute_script("arguments[0].scrollIntoView(true)", button)
		while not button.is_displayed():
			time.sleep(1)
			pass
		button = wait.until(EC.element_to_be_clickable(button))
		browser.execute_script("arguments[0].click()", button)
		time.sleep(0.1)
	
	articles = browser.find_elements(By.CSS_SELECTOR, "div.cl-paper-row.serp-papers__paper-row.paper-v2-cue.paper-row-normal")
	for article in articles:
		title = article.find_element(By.CSS_SELECTOR, "a > h2 > span").text
		link = article.find_element(By.CSS_SELECTOR, "a.link-button--show-visited").get_attribute("href")
		abstract = article.find_elements(By.CSS_SELECTOR, "div.cl-paper-abstract > span.full-abstract > *:not(button)")
		if len(abstract) == 0:
			continue
		abstract_text = ""
		for element in abstract:
			abstract_text += " " + element.text
	
		data.append((title, abstract_text, link))
	return data


def defineNumberOfPages():
	guess = 100
	last_bigger = 0
	while True:
		browser.get(search_url + f"&page={guess}")
		time.sleep(5)
		if not contentPresentInPage():
			last_bigger = guess
			guess //= 2
			browser.get(search_url+f"&page={guess}")
			time.sleep(5)
			if contentPresentInPage():
				break
		else:
			guess += guess // 2

	lower, upper = guess, last_bigger
	while not (upper - lower) == 1:
		time.sleep(5)
		browser.get(search_url+f"&page={(upper + lower) // 2}")
		if contentPresentInPage():
			lower = (upper + lower) // 2
		else:
			upper = (upper + lower) // 2
		print(lower, upper)
	return upper
	


contentWriter = csv.writer(open("articles.csv", "w"))
contentWriter.writerow(["TITLE", "ABSTRACT", "LINK"])

# Initialize web driver
browser = webdriver.Chrome()
# Get response from one page
keywords = ["sustainability", "regulation", "innovation", "compliance", "standards", "risk management"]
base_url = "https://www.semanticscholar.org/"
headers = {
	"user-agent" : """Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"""
}
KEYWORDS_SEPARATOR = "%2C%20"
search_part = KEYWORDS_SEPARATOR.join(keywords).replace(" ", "%20") + "&sort=relevance"
search_url = base_url + "search?q=" + search_part

browser.get(search_url + f"&page=100")
#browser.get(search_url)
time.sleep(1)
print(defineNumberOfPages())
