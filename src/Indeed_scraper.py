import os
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

global total_jobs

def configure_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run headless to avoid detection
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    return driver

def search_jobs(driver, job_position, job_location, date_posted):
    base_url = "https://www.indeed.com"
    full_url = f"{base_url}/jobs?q={'+'.join(job_position.split())}&l={job_location}&fromage={date_posted}"
    print(f"Fetching: {full_url}")
    driver.get(full_url)
    time.sleep(5)
    print(driver.page_source)  # Add this after driver.get(full_url)
    global total_jobs
    try:
        job_count_element = driver.find_element(By.XPATH, '//div[starts-with(@class, "jobsearch-JobCountAndSortPane-jobCount")]')
        total_jobs = job_count_element.find_element(By.XPATH, './span').text
        print(f"{total_jobs} jobs found")
    except NoSuchElementException:
        print("No job count found")
        total_jobs = "Unknown"
    return base_url

def scrape_job_data(driver, base_url):
    df = pd.DataFrame(columns=['Link', 'Job Title', 'Company', 'Employer Active', 'Location'])
    job_count = 0
    while True:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        boxes = soup.find_all('div', {'data-testid': 'jobCard'})

        for i in boxes:
            link = i.find('a', {'data-jk': True})
            link_full = base_url + link.get('href') if link else None
            job_title = i.find('h2').text.strip() if i.find('h2') else None
            company = i.find('span', {'data-testid': 'company-name'}).text.strip() if i.find('span', {'data-testid': 'company-name'}) else None
            employer_active = i.find('span', class_='date').text.strip() if i.find('span', class_='date') else None
            location = i.find('div', {'data-testid': 'text-location'}).text.strip() if i.find('div', {'data-testid': 'text-location'}) else None
            new_data = pd.DataFrame({'Link': [link_full], 'Job Title': [job_title], 'Company': [company], 'Employer Active': [employer_active], 'Location': [location]})
            df = pd.concat([df, new_data], ignore_index=True)
            job_count += 1
        print(f"Scraped {job_count} of {total_jobs}")
        try:
            next_page = soup.find('a', {'aria-label': 'Next Page'})
            if next_page:
                driver.get(base_url + next_page.get('href'))
                time.sleep(3)
            else:
                break
        except:
            break
    return df

def save_csv(df, job_position, job_location):
    output_dir = "../data"
    os.makedirs(output_dir, exist_ok=True)
    csv_file = os.path.join(output_dir, f"{job_position}_{job_location}.csv")
    df.to_csv(csv_file, index=False)
    print(f"✅ Data saved to {csv_file}")

def main():
    driver = configure_webdriver()
    base_url = search_jobs(driver, "Artificial Intelligence", "United States", "7")
    job_data = scrape_job_data(driver, base_url)
    driver.quit()
    save_csv(job_data, "Artificial_Intelligence", "United_States")

if __name__ == "__main__":
    main()
