from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options as EdgeOptions

# 這邊是用Edge作為範例，可以依照你使用瀏覽器的習慣做修改
options = EdgeOptions()
edge = webdriver.Edge(EdgeChromiumDriverManager().install(), options=options)
edge.get('https://www.google.com.tw/')

try:
    WebDriverWait(edge, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@aria-label='搜尋']")))
    input_block = edge.find_element(By.XPATH,"//input[@aria-label='搜尋']")
    input_block.send_keys("中央大學")
    input_block.send_keys(Keys.ENTER)
    
except TimeoutException as e:
    print(e)    