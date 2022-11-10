import requests
import os
import zipfile
import json
import getpass
import re
import io
import sys
import xml.etree.ElementTree as ET
from os import path
from datetime import date
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service

_k1 = "_n"
_k2 = "_s"

current_dir = os.getcwd()
selenium_path = f"{current_dir}\\msedgedriver.exe"


def checkCred():
    cre_u = os.getenv(_k1, default=None)
    cre_p = os.getenv(_k2, default=None)
    if str(cre_u) == "None" or str(cre_p) == "None":
        print("Not found any credentials! \nPlease enter email/password (This will be asked only one time and make sure you run this with admin prev while entering creds)")
        u = str(input("Username: "))
        p = str(getpass.getpass())
        try:
            set_1 = os.system('SETX {} {} /M'.format(_k1, u))
            set_2 = os.system('SETX {} {} /M'.format(_k2, p))
            print("Finished adding credentials to env! Please restart the cmd!")
            quit()
        except Exception as e:
            print('Error: {}'.format(e))
    else:
        print('[*] Accessing data of user {}'.format(cre_u))


def getLastestESver():
    rq_new_driver = requests.get("https://msedgedriver.azureedge.net/").content
    xml_response = ET.fromstring(rq_new_driver)
    return xml_response.find('Blobs').find('Blob').find('Name').text.split('/')[0]


def downloadES(VERSION):
    request_download_driver = requests.get(
        "https://msedgedriver.azureedge.net/"+VERSION+"/edgedriver_win64.zip")
    zip_file = zipfile.ZipFile(io.BytesIO(request_download_driver.content))
    zip_file.extractall(f"{current_dir}")
    print("Updated new web driver version! Please re-run the program")
    quit()

def getAccess():
    reTry = 1
    edge_options = EdgeOptions()
    edge_options.use_chromium = True
    edge_options.add_argument("--log-level=OFF")
    edge_options.add_argument("headless")
    edge_options.add_argument("disable-gpu")
    if not path.exists(selenium_path):
        print('[*] Get new dirver!!!')
        downloadES(getLastestESver())
    try:
        webdriver = Edge(executable_path=selenium_path, options=edge_options)
        reTry = 3
    except Exception as e:
        reTry += 1
        if reTry == 2:
            print("Error: ", str(e))
        version_notify = str(e)
        dr_version = re.findall(r"is ([\d.]*\d+)", version_notify)
        VERSION = dr_version[0]
        downloadES(VERSION)

    try:
        wait = WebDriverWait(webdriver, 4)
        webdriver.get("https://myfpt.fpt-software.vn/api/login-ms/adfs/login")
        f_soft = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/div/main/div/div/form/div[1]/div[4]/div/span'))).click()
        f_soft_lim = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/div[1]/div[2]/div/form/div[1]/div[2]/div/span'))).click()
        useEle = wait.until(EC.visibility_of_element_located((By.ID, 'userNameInput'))).send_keys(str(os.getenv(_k1, default=None)))
        pasEle = wait.until(EC.visibility_of_element_located((By.ID, "passwordInput"))).send_keys(str(os.getenv(_k2, default=None)))
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="submitButton"]'))).click()
    except Exception as e:
        print("Error: ", str(e))

    html = webdriver.page_source
    site_content = BeautifulSoup(html, 'html.parser')
    response = json.loads(site_content.text)
    return response


def getResult(months):
    net = 0
    print('''    [-] Month/Year: {}/{}
        [+] INCOME_001: {}
        [+] INCOME_002: {}
        [+] INCOME_003: {}
        [+] INCOME_004: {}
        [+] INCOME_005: {}
        [+] INCOME_NET: {}'''.format(months['FPT_FL_MONTHOFYEAR'], months['FPT_FL_YEAR'], months['FPT_FL_INCOME_001'], months['FPT_FL_INCOME_002'], months['FPT_FL_INCOME_003'], months['FPT_FL_INCOME_004'], months['FPT_FL_INCOME_005'], months['FPT_FL_INCOME_NET']))
    net += int(months['FPT_FL_INCOME_NET'])
    return net


def accessSite(year, month, response):
    c_year, c_month, c_day = str(date.today()).split('-')
    f_month = month
    if month == 'a':
        f_month = int(c_month) if int(c_day) >= 19 else int(c_month) - 1

    _headers = {
        'User-Agent': 'myFPT/4.10.9 iPhone12,1 iOS/14.3',
        'X-Access-Token': response['token'],
        'Adfsidtoken': response['adfsIdToken']
    }
    _url = "https://myfpt.fpt-software.vn/api/fpt-services-ms/public/payslip/my-income?monthYear={}-{}".format(year, f_month)

    try:
        _ps = requests.get(_url, headers=_headers).json()
        ps = _ps['Data']
    except Exception as e:
        print(str(e))
        quit()
    ic_month = ps['API_FPT_PAYSLIP_INCOME']
    total_net = 0
    try:
        print('''==========================================================
[#] YOUR DETAILS INCOMES
[*] Employee ID: {}
[*] Employee Name: {}
[*] Department: {} - {}
[*] Job Code: {}
[*] Nationnal ID: {}
[*] Details Income Month(s):'''.format(ps['EMPLID'], ps['NAME_DISPLAY'], ps['DEPT_DESCRSHORT'], ps['DEPT_DESCR'], ps['JOBCODE'], ps['NATIONALID'], ps['FPT_FL_BAS_SAL']))
        for months in ic_month:
            if month != 'a':
                if months['FPT_FL_MONTHOFYEAR'] == int(month):
                    total_net = getResult(months)
            else:
                total_net += getResult(months)
        print(f'''[*] Total NET income: {total_net}
==========================================================''')
    except Exception as e:
        print('[!] Key Error: '+str(e) +'\n[!] Perhalf your contract is not yet started, try change the date time value!')


def argRun():
    for x in range(0, len(sys.argv), 1):
        if sys.argv[x].lower() == '-h':
            print(
                'Instructions: python(3) ps.py -y [--year] -m [--month]')
        if sys.argv[x].lower() == '-y':
            try:
                year = sys.argv[x+1].strip()
            except Exception as e:
                print('Exception: ', str(e))
                quit()
        else:
            continue
    for y in range(0, len(sys.argv), 1):
        if sys.argv[y].lower() == '-m':
            try:
                month = sys.argv[y+1].strip()
            except:
                print('Exception: ', str(e))
    return year, month


def main():
    checkCred()
    try:
        if len(sys.argv) != 5:
            print('Instructions: python(3) ps.py -y [--year] -m [--month]')
        else:
            year, month = argRun()
            response = getAccess()
            accessSite(year, month, response)
    except Exception as e:
        print(e)
        print(
            f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")
        print('Instructions: python(3) ps.py -y [--year] -m [--month]')
        quit()


if __name__ == "__main__":
    main()
