#!.env/bin/python

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import sys
import csv
import logging


def contentPresentInPage(browser):
	wait = WebDriverWait(browser, 10)
	server_error = "div[data-test-id=error-message-block]"
	#papers_not_found = "h1[data-test-id=no-papers-found]"
	papers_not_found = "h1.bold"
	article_css_selector = "div.cl-paper-row.serp-papers__paper-row.paper-v2-cue.paper-row-normal"
	element = wait.until(EC.visibility_of_any_elements_located((By.CSS_SELECTOR, f"{server_error}, {article_css_selector}, {papers_not_found}")))
	if "Expand" in element[0].text:
		return True
	else:
		return False
	raise Exception("Could not load the page")


def getDataFromPage(browser):
	data = []
	wait = WebDriverWait(browser,30)
	article_css_selector = "div.cl-paper-row.serp-papers__paper-row.paper-v2-cue.paper-row-normal"
	element = wait.until(EC.visibility_of_any_elements_located((By.CSS_SELECTOR, f"{article_css_selector}")))
	expand_buttons = [button 
			  	for button in browser.find_elements(By.CSS_SELECTOR, "span.cl-button__label")
			  	if "Expand" == button.text
			  	]
	#elements = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "span.cl-button__label")))
	#expand_buttons = [button for button in elements if "Expand" == button.text]
	logger.info(f"Number of buttons: {len(expand_buttons)}")

	#time.sleep(1)
	for button in expand_buttons:
		browser.execute_script("arguments[0].scrollIntoView(true)", button)
		while not button.is_displayed():
			time.sleep(0.1)
			pass
		button = wait.until(EC.element_to_be_clickable(button))
		browser.execute_script("arguments[0].click()", button)
		#time.sleep(0.1)
	
	#articles = browser.find_elements(By.CSS_SELECTOR, "div.cl-paper-row.serp-papers__paper-row.paper-v2-cue.paper-row-normal")
	#for article in articles:
	#	title = article.find_element(By.CSS_SELECTOR, "a > h2 > span").text
	#	link = article.find_element(By.CSS_SELECTOR, "a.link-button--show-visited").get_attribute("href")
	#	abstract = article.find_elements(By.CSS_SELECTOR, "div.cl-paper-abstract > span.full-abstract > *:not(button)")
	#	if len(abstract) == 0:
	#		continue
	#	abstract_text = ""
	#	for element in abstract:
	#		abstract_text += " " + element.text

	articles = browser.find_elements(By.CSS_SELECTOR, "div.cl-paper-row.serp-papers__paper-row.paper-v2-cue.paper-row-normal")
	for article in articles:
		title = article.find_element(By.CSS_SELECTOR, "a > h2 > span").text
		link = article.find_element(By.CSS_SELECTOR, "a.link-button--show-visited").get_attribute("href")
		abstract = article.find_elements(By.CSS_SELECTOR, "div.cl-paper-abstract > span.full-abstract > *:not(button)")
		if len(abstract) == 0:
			abstract = article.find_elements(By.CSS_SELECTOR, "div > div > div > span")
			if len(abstract) != 0:
				abstract_text = abstract[-1].text
			else:
				continue
		else:
			abstract_text = ""
			for element in abstract:
				abstract_text += " " + element.text
		data.append((title, abstract_text, link))
	return data


def defineNumberOfPages(search_url, browser):
	guess = 10
	last_bigger = 0
	while True:
		browser.get(search_url + f"&page={guess}")
		if not contentPresentInPage(browser):
			last_bigger = guess
			guess //= 2
			browser.get(search_url+f"&page={guess}")
			if contentPresentInPage(browser):
				break
		else:
			guess += guess // 2

	print(last_bigger)
	lower, upper = guess, last_bigger
	while not (upper - lower) == 1:
		browser.get(search_url+f"&page={(upper + lower) // 2}")
		present = contentPresentInPage(browser)
		print(present)
		if present:
			lower = (upper + lower) // 2
		else:
			upper = (upper + lower) // 2
		print(lower, upper)
	return lower
	


def main():

	csv_file = open("articles.csv", "w")
	contentWriter = csv.writer(csv_file)
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
	
	browser.get(search_url)
	for page_number in range(1, defineNumberOfPages(search_url, browser)+1):
		browser.get(search_url + f"&page={page_number}")
		data = getDataFromPage(browser)
		logger.info(f"Number of parsed articles from page {page_number} is {len(data)}")
		for title, abstract, url in data:
			contentWriter.writerow([title, abstract, url])
		print(f"Page {page_number} written!")
	
	csv_file.close()


if __name__ == "__main__":
	
	logger = logging.getLogger(__name__)
	logging.basicConfig(level=logging.INFO)
	main()
	#browser = webdriver.Chrome()
	#browser.get("https://www.semanticscholar.org/search?q=sustainability%2C%20regulation%2C%20innovation%2C%20compliance%2C%20standards%2C%20risk%20management&sort=relevance&page=2")
	#wait = WebDriverWait(browser,30)
	#article_css_selector = "div.cl-paper-row.serp-papers__paper-row.paper-v2-cue.paper-row-normal"
	#element = wait.until(EC.visibility_of_any_elements_located((By.CSS_SELECTOR, f"{article_css_selector}")))
	#expand_buttons = [button 
	#		  	for button in browser.find_elements(By.CSS_SELECTOR, "span.cl-button__label")
	#		  	if "Expand" == button.text
	#		  	]
	##elements = wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "span.cl-button__label")))
	##expand_buttons = [button for button in elements if "Expand" == button.text]
	#logger.info(f"Number of buttons: {len(expand_buttons)}")
#
#	#time.sleep(1)
#	for button in expand_buttons:
#		browser.execute_script("arguments[0].scrollIntoView(true)", button)
#		while not button.is_displayed():
#			time.sleep(0.1)
#			pass
#		button = wait.until(EC.element_to_be_clickable(button))
#		browser.execute_script("arguments[0].click()", button)
#		#time.sleep(0.1)
#	
#	articles = browser.find_elements(By.CSS_SELECTOR, "div.cl-paper-row.serp-papers__paper-row.paper-v2-cue.paper-row-normal")
#	for article in articles:
#		title = article.find_element(By.CSS_SELECTOR, "a > h2 > span").text
#		link = article.find_element(By.CSS_SELECTOR, "a.link-button--show-visited").get_attribute("href")
#		abstract = article.find_elements(By.CSS_SELECTOR, "div.cl-paper-abstract > span.full-abstract > *:not(button)")
#		if len(abstract) == 0:
#			abstract = article.find_elements(By.CSS_SELECTOR, "div > div > div > span")
#			if len(abstract) != 0:
#				abstract_text = abstract[-1].text
#				print(abstract_text)
#		else:
#			abstract_text = ""
#			for element in abstract:
#				abstract_text += " " + element.text
		#print(title)
		#print(abstract_text)
		#print("**********************")


