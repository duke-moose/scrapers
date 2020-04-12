from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from datetime import datetime
import pandas as pd


def make_firefox_browser(preferences):
    profile = FirefoxProfile()
    for pref in preferences:
        profile.set_preference(pref, preferences[pref])
    firefox_browser = webdriver.Firefox(firefox_profile=profile)
    return firefox_browser


def make_firefox_preferences(save_location):
    # http: // kb.mozillazine.org / Firefox_: _FAQs_:_About: config_Entries  # Browser
    firefox_preferences = {
            'browser.download.folderList': 2,
            "browser.download.manager.showWhenStarting": False,
            'profile.set_preference(''browser.download.dir': save_location,
            'browser.helperApps.neverAsk.saveToDisk': 'text/csv',
        }
    return firefox_preferences


def wait_until_load(browser, delay, element):
        try:
            myElem = WebDriverWait(browser, delay).until(EC.presence_of_element_located(element))
            print('Found Element for ' + element[1])
        except TimeoutException:
            print("Loading took too much time!")


def run_selenium_scraper():
    # iframe_url = 'https://www.unacast.com/covid19/social-distancing-scoreboard' # This website has below website in iframe.
    url = 'https://covid19-scoreboard.unacast.com/'
    save_dir = '/covid_data'
    pref = make_firefox_preferences(save_dir)
    browser = make_firefox_browser(pref)
    browser.get(url)

    # Wait for page to load
    wait_until_load(browser, 10, (By.XPATH, "//div[@class='sc-fzpjYC gJohPa']"))

    # Scrape States
    states_grades = browser.find_elements_by_xpath("//div[@class='sc-fznWqX dAkvW']")
    states_grades = [c.text for c in states_grades]
    print('Scraped States and Grades, now to counties.')

    # Select counties label
    click_counties = browser.find_element_by_xpath("//div[@class='sc-fzpjYC gJohPa']/a[1]")
    click_counties.click()

    # Wait for page to load
    wait_until_load(browser, 10, (By.XPATH, "//div[@class='sc-fznWqX dAkvW']"))

    # Scrape counties and grades
    counties_grades = browser.find_elements_by_xpath("//div[@class='sc-fznWqX dAkvW']")
    counties_grades = [c.text for c in counties_grades]
    print('Scraped Counties and Grades, quitting session')
    browser.quit()

    # Get list human readable and organized by [location, grade].
    states_organized_list = [state.split('\n') for state in states_grades]
    counties_organized_list = [county.split('\n') for county in counties_grades]

    today = datetime.now().strftime('%m-%d-%Y')

    # Save to CSV
    labels = ['County', 'Grade']
    df_states = pd.DataFrame.from_records(states_organized_list, columns=labels)
    fp_states = 'covid_data/states_covid_grade_' + today + '.csv'
    print('Saving: ' + fp_states)
    df_states.to_csv(fp_states)

    df_counties = pd.DataFrame.from_records(counties_organized_list, columns=labels)
    fp_counties = 'covid_data/counties_covid_grade_'+today+'.csv'
    print('Saving: ' + fp_counties)
    df_counties.to_csv(fp_counties)


if __name__ == "__main__":
    run_selenium_scraper()

