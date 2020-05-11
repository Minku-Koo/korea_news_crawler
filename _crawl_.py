
# made by Koo Minku
#journal crawling engine

import requests
from bs4 import BeautifulSoup
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
import selenium
from selenium.webdriver.support.ui import WebDriverWait
import time
import re

print('crawl '*5)

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('--disable-gpu')
options.add_argument('lang=ko_KR')

driver = webdriver.Chrome('./crawler/drivers/chromedriver.exe', chrome_options=options)
#driver = webdriver.Chrome('./crawler/drivers/chromedriver.exe')
driver.implicitly_wait(5)
result_link, result_title = [], []

# 페이지 개수 계산 함수/ 총 게시글 표시된 부분 xPath (string), 페이지당 기사 개수 (int)
def pageCount(countPath, article_per_page):
    hg = re.compile('[가-힣 (),]')
    #기사 총 개수 출력된 부분 찾기
    num =driver.find_element_by_xpath(countPath).text
    num = int(re.sub(hg, '', num))

    page_count = int(num/article_per_page) +1
    #기사 개수가 (페이지당 기사개수)의 배수 경우 보정
    if num%article_per_page ==0:
        page_count -=1
    #총 페이지 갯수 반환 - return (int)
    return page_count


class crawling:
    def __init__(self, search, dateStart, dateEnd, includeWord,includeWhere,img_exist):
        self.search = search
        self.dateStart = dateStart
        self.dateEnd = dateEnd
        self.includeWord = includeWord
        self.includeWhere = includeWhere
        self.img_exist = img_exist
        self.result_link, self.result_title, self.result_date = [], [], []
        pass
    
    #키워드 포함 위치와 포함 단어 체크/ 기사 제목, 기사 태그 종류, 기사 태그 클래스 이름, 기사 url, 날짜
    def include_check(self, title_text, tag, tagAttr, tagName, url, date):
        head = {'User-Agent': 'Mozilla/5.0', 'referer': url}
        req = urllib.request.Request(url, headers=head)
        html = urllib.request.urlopen(req)
        bs = BeautifulSoup(html, 'lxml')
        #기사 내용 불러오기
        if tagAttr == 'class': 
            article_sub = bs.find(tag, class_=tagName)
            p = re.compile('<li>.*</li>') #쓸데없는 관련기사 제거 위한 정규표현식 / 동아일보
            
        elif tagAttr == 'id':
            article_sub = bs.find(tag, id=tagName)
            p = re.compile('<li>.*</li>') #쓸데없는 관련기사 제거 위한 정규표현식 / 동아일보
        
        article = p.sub('', str(article_sub))  #<li> 태그 전부 삭제
            
        # 단어 포함 여부 확인 
        success = True
        for word in self.includeWord:
            if word not in article: #하나라도 기사 내용에 포함되지 않는 경우
                success=False
                print('this is fail ...')
                break
        
        # 모두 기사 내용에 포함된 경우
        if success :
            print('this is success!!')
            #결과 링크-제목 저장
            self.result_link.append(url)
            self.result_title.append(title_text)
            self.result_date.append(date)
            
        return 0
    
    #이미지 포함 여부 확인
    def img_checker(self, url, tagName, tagAttr,className):
        head = {'User-Agent': 'Mozilla/5.0', 'referer': url}
        req = urllib.request.Request(url, headers=head)
        html = urllib.request.urlopen(req)
        bs = BeautifulSoup(html, 'lxml')
        #기사 내용에 이미지 태그 있는지 확인
        if tagAttr == 'class':
            img_check = bs.find(tagName, class_=className)
        elif tagAttr == 'align':
            img_check = bs.find(tagName, align=className)
        elif tagAttr == 'id':
            img_check = bs.find(tagName, id=className)
        
        #이미지 포함된 경우
        if img_check != None:
            print('img on')
            return 1
        else: #이미지 없는 경우
            print('NO img')
            return 0
            
    # 조건 검사 종합 함수 / 제목 텍스트, 기사 url , 기사 태그 종류, 기사 속성, 속성 이름 , 이미지 태그 종류, 이미지 속성, 이미지 속성 이름
    def conditionChecker(self, title, article_url, date,content_tag, content_attr, content_name, img_tag, img_attr, img_name):
        #이미지 포함인데 실제 포함되지 않은 경우 --> pass
        if self.img_exist == 1 and self.img_checker(article_url, img_tag, img_attr,img_name) == 0:
            print('there is not photo')
            pass
        
        # 제목에만 키워드 포함 and 실제로 포함된 경우  -->본문에 포함단어 존재 여부 확인
        elif self.includeWhere == 'title' and self.search in title:
            print('only title and success')
            #기사 내용에 단어 포함여부 확인
            self.include_check(title, content_tag, content_attr, content_name, article_url, date)
            pass
        # 제목에 키워드 포함되어야 하는데 그렇지 않은 경우 --> pass
        elif self.includeWhere == 'title':
            print('only title but not exist')
            pass
        # 제목 + 본문에 키워드 포함 (일반 검색) --> 포함 단어 있다면, 기사 url에서 조사
        else:
            print('title + content')
            #기사 내용에 단어 포함여부 확인
            self.include_check(title, content_tag, content_attr, content_name, article_url, date)
            pass
        
    #페이지 별로 기사 제목 출력
    def khan_crawl(self, page):
        for r in range(1,10): #경향신문은 한 페이지 당 10개의 기사
            #제목 path
            path = '//*[@id="container"]/div[2]/div[2]/dl['+str(r)+']/dt/a'
            date_path = '//*[@id="container"]/div[2]/div[2]/dl['+str(r)+']/dt/span'
            try:
                title = driver.find_element_by_xpath(path)
                print('=='*10)
                title_text = title.text #기사 제목
                article_url = title.get_attribute("href") #기사 링크
                date = driver.find_element_by_xpath(date_path).text
                date = date.replace('(', '').replace(' ', '')
                date = date[:10]
                
                print(title.text)
            #마지막에 페이지가 10개가 아닐 경우/ 에러
            except(selenium.common.exceptions.NoSuchElementException):
                print('page article over')
                break
        
            self.conditionChecker( title_text, article_url, date,'div', 'id', 'articleBody', 'div', 'class',"art_photo_wrap")
        
        # 페이지가 마지막에 도달하면 다음 버튼 클릭
        if page%10==0:
            try:
                driver.find_element_by_class_name('btn_num.next').click()
            except(selenium.common.exceptions.NoSuchElementException):
                print('page article over')
                return
        #마지막이 아닐 경우 다음 페이지 숫자 클릭
        else:
            try:
                btn_path = '//*[@id="container"]/div[2]/div[3]/span/span['+str(page%10+2)+']'
                driver.find_element_by_xpath(btn_path).click()
            except(selenium.common.exceptions.NoSuchElementException):
                print('page article over')
                return


    def khan(self):
        self.result_link, self.result_title, self.result_date = [], [], []
        time.sleep(2)
        url = "http://www.khan.co.kr/"
        driver.get(url)
        driver.implicitly_wait(3) # 로딩까지 3초 기다리기
        
        #돋보기 클릭
        driver.find_element_by_xpath('//*[@id="main_top_search_btn"]').click()
        #검색창에 검색어 입력
        elm = driver.find_element_by_xpath("""//*[@id="main_top_search_input"]""")
        elm.send_keys(self.search)
        #돋보기 클릭
        driver.find_element_by_xpath('//*[@id="main_top_search_btn"]').click()

        driver.implicitly_wait(1)
        #전체보기 클릭
        driver.find_element_by_xpath('//*[@id="container"]/div[2]/div[2]/div/a').click()

        #기간 설정- 언제부터 언제까지
        date1 = driver.find_element_by_xpath('//*[@id="search_date1"]')
        driver.execute_script('arguments[0].value="'+self.dateStart+'";', date1)

        date2 = driver.find_element_by_xpath('//*[@id="search_date2"]')
        driver.execute_script('arguments[0].value="'+self.dateEnd+'";', date2)

        # 기간 적용하기 클릭 
        driver.find_element_by_xpath('//*[@id="container"]/div[3]/div[1]/div[2]/ul/li[6]/span[2]/button').click()


        #총 검색 기사 개수 구함
        hg = re.compile('[가-힣 (),]')
        num =driver.find_element_by_xpath('//*[@id="container"]/div[2]/div[2]/h3/span').text
        num = int(re.sub(hg, '', num))

        page_count = int(num/10) +1
        #기사 개수가 10의 배수 경우 보정
        if num%10 ==0:
            page_count -=1

        #페이지 계산해서 끝까지 keep going
        for i in range(1,page_count+1):
            self.khan_crawl(i)
            print('=*='*15)
            
        time.sleep(2)
        print('Article Close')
        #driver.close()
        return [self.result_link, self.result_title, self.result_date]


    #페이지 별로 기사 제목 출력
    def kmib_crawl(self, page):
        print('kmib')
        for r in range(1,11): #국민일보는 한 페이지 당 10개의 기사
            #제목 path
            path = '//*[@id="searchList"]/div['+str(r)+']/dl/dt/a'
            date_path = '//*[@id="searchList"]/div['+str(r)+']/dl/dd[2]/ul/li/em'
            try:
                title = driver.find_element_by_xpath(path)
                print('=='*10)
                title_text = title.text #기사 제목
                article_url = title.get_attribute("href") #기사 링크
                date = driver.find_element_by_xpath(date_path).text
                date = date.replace('-', '.')
                print(title.text)
                print(article_url)
                print('date : ',date)
            #마지막에 페이지가 10개가 아닐 경우/ 에러
            except(selenium.common.exceptions.NoSuchElementException):
                print('page article over')
                return
            self.conditionChecker( title_text, article_url, date, 'div','id','articleBody','div', 'align', 'center')
        
        # 페이지가 마지막에 도달하면 다음 버튼 클릭
        print('page click')
        if page%10==0:
            print('10 next click '*5)
            em = driver.find_element_by_class_name('next')
            time.sleep(1)
            em.click()
        
        #마지막이 아닐 경우 다음 페이지 숫자 클릭
        else:
            print('not 10  '*5)
            try:
                btn_path = '//*[@id="paging"]/span['+str(page%10)+']/a'
                driver.find_element_by_xpath(btn_path).click()
            except(selenium.common.exceptions.NoSuchElementException):
                print('page article over')
                return
    
    #국민일보 메인 함수
    def kmib(self):
        print('kmib start')
        self.result_link, self.result_title, self.result_date = [], [], []
        url = "http://www.kmib.co.kr/news/index.asp"
        time.sleep(2)
        driver.get(url)
        driver.implicitly_wait(3) # 로딩까지 3초 기다리기
        
        #검색창에 검색어 입력
        elm = driver.find_element_by_xpath("""//*[@id="search"]""")
        elm.send_keys(self.search)
        #돋보기 클릭
        driver.find_element_by_xpath('//*[@id="header"]/div[2]/div[2]/input[2]').click()
        driver.implicitly_wait(1)
        
        #상세검색 클릭
        driver.find_element_by_xpath('//*[@id="searchForm"]/div[1]/div[2]/a').click()
        
        #기간 설정- 언제부터 언제까지
        date1 = driver.find_element_by_xpath('//*[@id="searchInputStartDate"]')
        date1.send_keys(self.dateStart)
        
        date2 = driver.find_element_by_xpath('//*[@id="searchInputEndDate"]')
        date2.send_keys(self.dateEnd)
        
        #상세검색 검색 클릭
        driver.find_element_by_xpath('//*[@id="detailSearchAtricle"]').click()

        page_count = pageCount('//*[@id="searchTotalItemCnt"]', 10)
        #페이지 계산해서 끝까지 keep going
        for i in range(1,page_count+1):
            self.kmib_crawl(i)
            print('=*='*15)
            
        time.sleep(2)
        print('Article Close')
        return [self.result_link, self.result_title, self.result_date]


    #동아일보 페이지 별로 기사 제목 출력
    def donga_crawl(self, page):
        
        for r in range(1,16): #동아일보는 한 페이지 당 15개의 기사
            #제목 path  
            path = '//*[@id="contents"]/div[3]/div[1]/div['+str(r)+']'
            date_path = '//*[@id="contents"]/div[3]/div/div['+str(r)+']/div[2]/p[1]/span'
            
            try:
                title_tag = driver.find_element_by_xpath(path).find_element_by_class_name('tit')
                title = title_tag.find_element_by_tag_name('a')
                
                title_text = title.text #기사 제목
                date = title_tag.text[-17:-6]
                article_url = title.get_attribute("href") #기사 링크
            #마지막에 페이지가 10개가 아닐 경우/ 에러
            except(selenium.common.exceptions.NoSuchElementException):
                print('page article over')
                return
                
            self.conditionChecker(title_text, article_url, date, 'div','class', 'article_txt','div', 'class','articlePhotoC')
            
        nb=0  #동아일보 특성 상, 10 이상 페이지부터 태그 내용 변경 -- 보정 위해 nb 삽입
        if page >10:
            nb =1
        
        # 페이지가 마지막에 도달하면 다음 버튼 클릭
        if page%10==0:
            try:
                print("click next")
                btn =driver.find_element_by_class_name('right')
                time.sleep(0.5)
                btn =driver.find_element_by_xpath('//*[@title="다음"]')
                time.sleep(0.5)
                print(btn.text)
                
                btn.click()
            except(selenium.common.exceptions.NoSuchElementException):
                print('page article over')
                return
            
        #마지막이 아닐 경우 다음 페이지 숫자 클릭
        else:  
            try:
                print("click ok")
                # nb는 페이지 다음 누를때마다 xpath 번호 보정
                btn_path = '//*[@id="contents"]/div[3]/div[2]/a['+str(page%10 +nb)+']'
                driver.find_element_by_xpath(btn_path).click()
            except(selenium.common.exceptions.NoSuchElementException):
                print('page article over')
                return
        
    def donga(self):
        self.result_link, self.result_title, self.result_date = [], [], []
        time.sleep(1)
        url = "http://www.donga.com/"
        driver.get(url)
        driver.implicitly_wait(3) # 로딩까지 기다리기
        
        #검색창 열기
        time.sleep(1)
        btn = driver.find_element_by_class_name('icon_com.icon_search')
        btn.click()
        driver.implicitly_wait(3)
        
        #검색창에 검색어 입력
        elm = driver.find_element_by_xpath("""//*[@id="query"]""")
        elm.send_keys(self.search)
        #돋보기 클릭
        driver.find_element_by_xpath('//*[@id="search_form"]/div/div/input').click()
        driver.implicitly_wait(3)
        time.sleep(0.3)
        
        #상세검색 클릭
        driver.find_element_by_xpath('//*[@id="header"]/div/div[2]/ul/li[6]/a').click()
        #기간 직접 입력 클릭 
        driver.find_element_by_xpath('//*[@id="d_term_5"]').click()
        time.sleep(1)
        #기간 설정- 언제부터 언제까지
        date1 = driver.find_element_by_xpath('//*[@id="v1"]')
        date1.send_keys(self.dateStart)
        
        date2 = driver.find_element_by_xpath('//*[@id="v2"]')
        date2.send_keys(self.dateEnd)
        time.sleep(1)
        
        #상세검색 검색 클릭 
        btn = driver.find_element_by_xpath('//*[@id="search_form_detail"]/div[2]/input[2]')
        btn.click()
        driver.implicitly_wait(2)
        time.sleep(1)
        
        # 더보기 클릭 
        driver.execute_script("window.scrollTo(0, 800);")
        btn = driver.find_element_by_class_name('more02')
        print(btn.text)
        btn.click()
        time.sleep(1)

        page_count = pageCount('//*[@id="contents"]/div[3]/div/h2/span[1]', 15)
        
        #페이지 계산해서 끝까지 keep going
        for i in range(1,page_count+1):
            self.donga_crawl(i)
            print('=*='*15)
            print(i)
            
        time.sleep(1)
        print('Article Close')
        
        return [self.result_link, self.result_title, self.result_date]

    #페이지 별로 기사 제목 출력, YTN 미완성
    def ytn_crawl(self, page, num):
        print('ytn')
        '''
        ytn  인코딩에러뜸
        '''
        if num <=5:
            for r in range(1,num+1): #ytn은 한 페이지 당 20개의 기사
                #제목 path
                
                path = '//*[@id="main"]/div[1]/dl['+str(r)+']/dt/a'
                try:
                    title = driver.find_element_by_xpath(path)
                    print('=='*10)
                    title_text = title.text #기사 제목
                    article_url = title.get_attribute("href") #기사 링크
                    print(title.text)
                    print(article_url)
                #마지막에 페이지가 10개가 아닐 경우/ 에러
                except(selenium.common.exceptions.NoSuchElementException):
                    print('page article over')
                    return
                
                self.conditionChecker( title_text, article_url, 'div','id','CmAdContent','div', 'class', 'imgArea')
        
        else:
            for r in range(1,21): #ytn은 한 페이지 당 20개의 기사
                #제목 path
                
                path = '//*[@id="main"]/div/dl['+str(r)+']/dt/a'
                try:
                    title = driver.find_element_by_xpath(path)
                    print('=='*10)
                    title_text = title.text #기사 제목
                    article_url = title.get_attribute("href") #기사 링크
                    print(title.text)
                    print(article_url)
                #마지막에 페이지가 10개가 아닐 경우/ 에러
                except(selenium.common.exceptions.NoSuchElementException):
                    print('page article over')
                    return
                
                self.conditionChecker( title_text, article_url, 'div','id','CmAdContent','div', 'class', 'imgArea')
            
        
        
        nb=0  #ytn 특성 상, 10 이상 페이지부터 태그 내용 변경 -- 보정 위해 nb 삽입
        if page >10:
            nb =1
        
        # 페이지가 마지막에 도달하면 다음 버튼 클릭
        print('page click')
        if page%20==0:
            print('20 next click '*5)
            em = driver.find_element_by_class_name('next')
            time.sleep(1)
            em.click()
        
        #마지막이 아닐 경우 다음 페이지 숫자 클릭
        else:
            print('not 20  '*5)
            try:
                btn_path = '//*[@id="paging"]/a['+str(page%10+nb)+']'
                driver.find_element_by_xpath(btn_path).click()
            except(selenium.common.exceptions.NoSuchElementException):
                print('page article over')
                return
    
    #국민일보 메인 함수
    def ytn(self):
        print('ytn start')
        self.result_link, self.result_title = [], []
        url = "https://www.ytn.co.kr/"
        time.sleep(2)
        print(url)
        driver.get(url)
        driver.implicitly_wait(5) # 로딩까지 3초 기다리기
        
        #돋보기 클릭
        driver.find_element_by_xpath('//*[@id="YTN_main_2017"]/div[1]/div[2]/div[3]/ul/li[4]/a').click()
        driver.implicitly_wait(2)
        #검색창에 검색어 입력
        elm = driver.find_element_by_xpath("""//*[@id="q"]""")
        elm.send_keys(self.search)
        print(driver.current_url)
        #돋보기 클릭
        driver.find_element_by_xpath('//*[@id="search"]/form/fieldset/input').click()
        driver.implicitly_wait(10)
        
        #iframe 변경
        driver.switch_to_frame("sList") 
        #기간 직접 입력 클릭
        radio = driver.find_element_by_css_selector("input[id='se_date3']")
        radio.click()
        #기간 설정- 언제부터 언제까지
        #value="" title="YYYY-MM-DD"
        date1 = driver.find_element_by_xpath('//*[@title="검색기간시작일"]')
        sdate = self.dateStart.replace('.','')
        print(sdate)
        driver.execute_script('arguments[0].value='+sdate, date1)
        
        date2 = driver.find_element_by_xpath('//*[@title="검색기간종료일"]')
        edate = self.dateEnd.replace('.','')
        driver.execute_script('arguments[0].value='+edate, date2)
        
        # 본문이냐 제목이냐 클릭
        if self.includeWhere == 'title':
            driver.find_element_by_xpath('//*[@id="target1"]').click()
            driver.implicitly_wait(5)

        # 상세 검색 다시 검색  
        driver.implicitly_wait(5)
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="dsrchBox"]/li[2]/ul/li[3]/input').click()
        driver.implicitly_wait(5)
        print(driver.current_url) #현재 페이지 URL
        driver.switch_to_frame("sList") 
        print('switch to frame')
        number= driver.find_element_by_xpath('//*[@id="main"]/div[1]/ul/li[1]/b').text
        number =  str(number).replace(',', '').replace('(', '').replace(')', '')
        print(number)
        num = int(number)
        page_count = pageCount('//*[@id="main"]/div[1]/ul/li[1]/b', 20)
        
        if num >5:
            # n개 미만일 경우 더보기 클릭 없음
            driver.find_element_by_xpath('//*[@id="main"]/div[1]/span/a').click()
            driver.implicitly_wait(5)
        
        #page_count 따라서 구분짓기
        #페이지 계산해서 끝까지 keep going
        for i in range(1,page_count+1):
            self.ytn_crawl(i, num)
            print('=*='*15)
            
        time.sleep(2)
        print('Article Close')
        return [self.result_link, self.result_title]


