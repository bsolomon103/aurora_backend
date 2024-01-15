from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from selenium.webdriver import ActionChains
from .fuzzymatch import check_similarity
import time
from .seleniumfuncs import pull_details_out
from .emailfuncs import send_email



class Driver:
  """Builds a chrome driver object capable of headless browser automation."""
  def __init__(self):
    chrome_driver = ChromeDriverManager().install()
    options = webdriver.ChromeOptions()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("window-size=1400,1500")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    options.add_argument("enable-automation")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    self.driver = webdriver.Chrome(service=Service(chrome_driver), options=options)
    self.driver.maximize_window()
  
  def getbinday(self, url, street_name):
    """
    Gets the scheduled bin collection days for inputted street name
    Attributes:
     street_name(str): Street name to perform the lookup for
    """
    res = ''
    self.driver.get(url)
    try:
        # Pull XPATH required to input street name
        print(1)
        input_street = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/main/div/section/div[1]/div/form/fieldset/div/div/input')))
        input_street.send_keys(street_name)
        
        # Accept Cookies
        print(2)
        cookies_button = self.driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/button[1]')
        cookies_button.click()
        
        # Reject Subscription
        print(3)
        subscribe_button = self.driver.find_element(By.XPATH, '/html/body/div[3]/div[2]/div/div[1]/button')
        subscribe_button.click()
        
        # Find search button
        print(4)
        search_button = self.driver.find_element(By.XPATH, '/html/body/div[2]/main/div/section/div[1]/div/form/fieldset/footer/div/div/button')
        ActionChains(self.driver).move_to_element(search_button).perform()
        search_button.click()
        
        # Click on Street Name
        print(5)
        get_street = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/main/div/section/div[1]/ul/li/a')))
        get_street.click()
        
        contents = WebDriverWait(self.driver, 1.5).until(EC.visibility_of_element_located((By.CLASS_NAME, 'page-content')))
     
        # Find all dt and dd elements within the page_content_div
        dt_elements = contents.find_elements(By.TAG_NAME, 'dt')
        dd_elements = contents.find_elements(By.TAG_NAME, 'dd')
        
        for dt, dd in zip(dt_elements, dd_elements):
            heading = dt.text.strip()
            content = dd.text.strip()
            res = res +  f"{heading}: {content}\n"

        self.driver.quit()
    
        
    except Exception as e:
        res = 'Search the directory http://tinyurl.com/yn4xxbo3 to check your collection days'
    return res
        
    
  def checkvehtax(self, url, reg_no):
    """
    Searches for vehicle registration details for e.g. color, make, year, tax status
    Attributes:
     url(str): The url link for the resource that selenium's driver attaches to.
     reg_no(str): Alphanumeric string registration no of the vehicle to perform the look up for e.g. CU57ABC.
    """
    res = ''
    check_vehicle = {}
    self.driver.get(url)
    try:
        print(1)
        input_reg_no = WebDriverWait(self.driver, 2.5).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div/main/div[2]/div/form/fieldset/div/input')))
        input_reg_no.send_keys(reg_no)
        
        print(2)
        # Search Button
        search_button = self.driver.find_element(By.XPATH, '/html/body/div/main/div[2]/div/form/button')
        search_button.click()
        
        print(3)
        # Click Yes Button 
        yes_button = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div/main/div[2]/div/form/div/fieldset/div/div[1]/input')))
        yes_button.click()
        
        print(4)
        # Click Continue Button
        continue_button = WebDriverWait(self.driver,5).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div/main/div[2]/div/form/button')))
        continue_button.click()
        
        print(5)
        # Registration Summary
        summary = WebDriverWait(self.driver, 2).until(EC.visibility_of_element_located((By.CLASS_NAME, 'summary-no-action')))
        
        print(6)
        # Find all dt and dd elements within the page_content_div
        dt_elements = summary.find_elements(By.TAG_NAME, 'dt')
        dd_elements = summary.find_elements(By.TAG_NAME, 'dd')
        
        for dt, dd in zip(dt_elements, dd_elements):
            heading = dt.text.strip()
            content = dd.text.strip()
            res = res +  f"{heading}: {content}\n"

        self.driver.quit()
       

        
        
    except Exception as e:
        res = f'Click the link https://tinyurl.com/ywzhpx23 to report this vehicle'
    
    return res
    
 
  def checkrecycling(self, url, item):
    """
    Gets the scheduled bin collection days for inputted street name
    Attributes:
     street_name(str): Street name to perform the lookup for
    """
    res = ''
    dc = {}
    self.driver.get(url)
    try:
        # Pull XPATH required to input item type
        print(1)
        input_item = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/main/div/section/div[1]/div/form/fieldset/div/div/input')))
        input_item.send_keys(item)
        
        # Accept Cookies
        print(2)
        try:
            cookies_button = self.driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/button[1]')
            cookies_button.click()
        except:
            pass
        
        # Reject Subscription
        print(3)
        subscribe_button = self.driver.find_element(By.XPATH, '/html/body/div[3]/div[2]/div/div[1]/button')
        subscribe_button.click()
        
        # Search Button 
        print(4)
        search_button = self.driver.find_element(By.XPATH, '/html/body/div[2]/main/div/section/div[1]/div/form/fieldset/footer/div/div/button')
        search_button.click()
        
        # Search Results
        print(5)
        results_list = WebDriverWait(self.driver, 2.5).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/main/div/section/div[1]/ul')))
        
        print(6)
        time.sleep(0.5)
        list_items = results_list.find_elements(By.TAG_NAME, 'li')
        #print(len(list_items))
        #if len(list_items) > 1:
        # Run through a matching excercise
        for list_item in list_items:
            if check_similarity(item, list_item.text):
                match = list_item.find_element(By.CLASS_NAME, 'list__link')
                #print(match.text)
                dc[match.text.lower()] = match
            
        # 100% match
        if item in dc:
            link = dc[item]
            time.sleep(0.5)
            link.click()
            print('Link clicked')
            contents = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.CLASS_NAME, 'page-content')))
                
            # Find all dt and dd elements within the page_content_div
            dt_elements = contents.find_elements(By.TAG_NAME, 'dt')
            dd_elements = contents.find_elements(By.TAG_NAME, 'dd')
                
            for dt, dd in zip(dt_elements, dd_elements):
                heading = dt.text.strip()
                content = dd.text.strip()
                res = res +  f"{heading}: {content}\n"
        else:
            res = f"Search the directory below to find out how to dispose of different items http://tinyurl.com/ywmnnaul"
        
        self.driver.quit()
                
                
    except Exception as e:
        res = f"Search the directory below to find out how to dispose of different items http://tinyurl.com/ywmnnaul"
    
    return res
    
  def checkcatchmentarea(self, url, postcode):
    """
     Gets the primary and secondary schools avaialable within the catchment area for a given Postcode.
     Attributes:
      url(str): The url for the schools directory
      postcode(str): Alphanumeric for the postcode to search for
    """
    res = ""
    dc = {}
    self.driver.get(url)
    try:
        # Input the postcode
        print(1)
        input_item = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/main/div/section/div[1]/div/form/fieldset/div/div/input')))
        input_item.send_keys(postcode)
        
            
        # Accept Cookies
        print(2)
        try:
            cookies_button = self.driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/div[2]/button[1]')
            cookies_button.click()
        except:
            pass
            
        # Reject Subscription
        print(3)
        subscribe_button = self.driver.find_element(By.XPATH, '/html/body/div[3]/div[2]/div/div[1]/button')
        subscribe_button.click()
        
        # Search Button 
        print(4)
        search_button = self.driver.find_element(By.XPATH, '/html/body/div[2]/main/div/section/div[1]/div/form/fieldset/footer/div/div/button')
        search_button.click()
            
        # Search Results
        print(5)
        results_list = WebDriverWait(self.driver, 2.5).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/main/div/section/div[1]/ul')))
        
        print(6)
        time.sleep(0.5)
        list_item = results_list.find_element(By.TAG_NAME, 'li')
     
        match = list_item.find_element(By.XPATH, '/html/body/div[2]/main/div/section/div[1]/ul/li/a')
        
        if match:
            print(match.text)
            #WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "ccc-content--dark  ccc-content--highlight "))).click()
            #(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/main/div/section/div[1]/ul/li/a')))
            match.click()
            
                
            contents = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.CLASS_NAME, 'page-content')))
                
            # Find all dt and dd elements within the page_content_div
            dt_elements = contents.find_elements(By.TAG_NAME, 'dt')
            dd_elements = contents.find_elements(By.TAG_NAME, 'dd')
                
            for dt, dd in zip(dt_elements, dd_elements):
                heading = dt.text.strip()
                content = dd.text.strip()
                res = res +  f"{heading}: {content}\n"
        else:
            res = f"Search the directory for schools in your catchment area http://tinyurl.com/yq2634ny"
        
        self.driver.quit()
        
    
        
    except Exception as e:
        print(e)
        res = f"Search the directory for schools in your catchment area http://tinyurl.com/yq2634ny"
    
    return res

  def login(self, url, idx, password, request):
      """Add description later"""
      res = ""
      dc = {}
      self.driver.get(url)
      
      try:
          # input id and password
          print(1)
          input_id = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/section/div[2]/div/div/div[2]/div[1]/fieldset[1]/div[1]/div[1]/input')))
          input_id.send_keys(idx)
          
          print(2)
          input_password = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/section/div[2]/div/div/div[2]/div[1]/fieldset[1]/div[2]/div[1]/input')))
          input_password.send_keys(password)
          
          print(3)
          signin = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/section/div[2]/div/div/div[2]/div[1]/fieldset[1]/div[3]/input[2]')))
          signin.click()
          print('Signin successful')
         
          print(4)
          detailcont = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/header/div[1]/div[2]/div/div/div/a[1]')))
          detailcont.click()
          
          print(5)
          details = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/header/div[1]/div[1]/div/div/div[2]/div')))
          payload = pull_details_out(details.text)
          payload['candidate_id'] = idx
          payload['request'] = request
          
          send_email(payload)
          
          
          signout = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/header/div[1]/div[1]/div/div/div[3]/div/a')))
          signout.click()
          print('Signout successful')
          
          response = "I've successfully pulled your user details and sent details of your request to a member of staff who'll be in touch shortly"
          
          '''
          print(5)
          accountdetailscont = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/section/div[2]/nav/div[2]/ul/li[1]/a')))
          accountdetailscont.click()
          
          print(6)
          accountdetails = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/section/div[2]/nav/div[2]/ul/li[1]/ul/li[1]/a')))
          accountdetails.click()
          '''
          
          
      except:
          pass
      return response
  
        
        
    
    
    
     
