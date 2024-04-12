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
import argparse


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
		authors = article.find_elements(By.CSS_SELECTOR, "span.cl-paper-authors")
		authors_names = ""
		for author in authors:
			names = author.find_elements(By.CSS_SELECTOR, "span[data-heap-id=heap_author_list_item]")
			for name in names:
				authors_names += name.text + ", "
			authors_names = authors_names.strip()[:-1]
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
		data.append((title, authors_names, abstract_text, link))
	return data


def defineNumberOfPages(search_url, browser, max_pages):
	guess = 10
	last_bigger = 0
	while True:
		if max_pages is not None:
			if guess > max_pages:
				return max_pages
		browser.get(search_url + f"&page={guess}")
		if not contentPresentInPage(browser):
			last_bigger = guess
			guess //= 2
			browser.get(search_url+f"&page={guess}")
			if contentPresentInPage(browser):
				break
		else:
			guess += guess // 2

	logger.info(f"Last bigger: last_bigger")
	lower, upper = guess, last_bigger
	while not (upper - lower) == 1:
		browser.get(search_url+f"&page={(upper + lower) // 2}")
		present = contentPresentInPage(browser)
		if present:
			lower = (upper + lower) // 2
		else:
			upper = (upper + lower) // 2
		logger.info(f"lower: {lower} | Upper: {upper}")
	return lower
	


def main(save_file, prompt_file, mode, max_pages):
	base_url = "https://www.semanticscholar.org/"
	with open(prompt_file, "r") as fprompt:
		prompt = fprompt.read()
	if mode == "sentence_prompt":
		search_part = prompt.replace(" ", "%20") + "&sort=relevance"
		search_url = base_url + "search?q=" + search_part
	elif mode == "tags_prompt":
		keywords = list(map(lambda x: x.strip(), prompt.split(",")))
		search_part = "%2C%20".join(keywords).replace(" ", "%20") + "&sort=relevance"
		search_url = base_url + "search?q=" + search_part

	csv_file = open(save_file, "w")
	contentWriter = csv.writer(csv_file)
	contentWriter.writerow(["TITLE", "AUTHORS NAMES", "ABSTRACT", "LINK"])
	
	# Initialize web driver and enter search page
	options = webdriver.ChromeOptions()
	options.add_argument("headless")
	browser = webdriver.Chrome(options=options)
	browser.get(search_url)

	# Calculate number of pages to parse
	n_pages = defineNumberOfPages(search_url, browser, max_pages)
	logger.info(f"Number of pages to parse: {n_pages}")

	# Get data from earch page
	for page_number in range(1, n_pages+1):
		browser.get(search_url + f"&page={page_number}")
		data = getDataFromPage(browser)
		logger.info(f"Number of parsed articles from page {page_number} is {len(data)}")
		for title, authors_names, abstract, url in data:
			contentWriter.writerow([title, authors_names, abstract, url])
		logger.info(f"Page {page_number} written!")
	
	csv_file.close()
	


if __name__ == "__main__":

	# ./main.py --tags_prompt=fileprompt.txt --max_pages=5

	parser = argparse.ArgumentParser()

	parser.add_argument("save_file", help="File to save data")

	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument("--sentence_prompt", help="File with prompt")
	group.add_argument("--tags_prompt", help="File with tags")

	parser.add_argument("--max_pages", help="Maximum pages to parse", type=int)

	args = parser.parse_args()

	logger = logging.getLogger(__name__)
	logging.basicConfig(level=logging.INFO)

	logger.info(f"Argument values: {args}")

	# Choose either search by sentence prompt or keyword prompt
	if args.sentence_prompt:
		# Work with sentence prompt
		main(args.save_file, args.sentence_prompt, "sentence_prompt", args.max_pages)
	else:
		main(args.save_file, args.tags_prompt, "tags_prompt", args.max_pages)
		# Work with tags prompt
