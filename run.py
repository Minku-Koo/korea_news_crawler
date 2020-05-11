# made by Koo Minku
# 20200416
# Korean News Crawl with condition program
# python flask
# Maria DB
#developer email : corleone@kakao.com

import pymysql
from flask import Flask
from flask import Flask, redirect, url_for, request, render_template, session
from _crawl_ import crawling
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import urllib.request
import re
import os
import datetime

"""
MariaDB database information
db name : mynews

CREATE TABLE news_condition(
    no int AUTO_INCREMENT,
    keyword varchar(20) NOT NULL,
    include_word varchar(40) ,
    period varchar(30) NOT NULL,
    position varchar(10) NOT NULL,
    img varchar(4) NOT NULL,
    journal varchar(30) ,
    PRIMARY KEY (NO)
);

CREATE TABLE news_<NUMBER>(
    no int AUTO_INCREMENT,
    title varchar(60) NOT NULL,
    link varchar(90) NOT NULL,
    date date,
    PRIMARY KEY (NO)
);
"""
db = pymysql.connect(
                    host="localhost", 
                    user="root", 
                    passwd="", #rnalsrn12
                    database="mynews",
                    port = 3306
                    )


app = Flask(__name__)
app.secret_key = 'd0nt/look6acK_1nA2ger'

#생성된 테이블에 링크, 제목, 날짜 입력
def input_article(tablename, articleList):
    sql = "INSERT INTO "+tablename+" (title, link, day) VALUES (%s, %s, %s);"
    cursor = db.cursor()
    for i in range(len(articleList[0])):
        #날짜 형식 변경
        articleList[2][i] = articleList[2][i].replace('.', '-')
        # 날짜 string을 datetime으로 변경
        cursor.execute("SELECT STR_TO_DATE('"+articleList[2][i]+"', '%Y-%m-%d');")
        datetime = cursor.fetchone()[0]
        cursor.execute(sql ,( articleList[1][i], articleList[0][i], articleList[2][i]))
    db.commit()
    cursor.close()
    return 0

#테이블 생성 / 크롤링한 기사 링크, 제목, 날짜 입력 테이블
def crtable(number):
    cursor = db.cursor()
    cursor.execute( """CREATE TABLE  %s (
                        no int AUTO_INCREMENT,
                        title varchar(60) NOT NULL,
                        link varchar(90) NOT NULL,
                        day date,
                        PRIMARY KEY (NO)
                    );""" %('news_'+number))
    db.commit()
    cursor.close()
    return 'news_'+number


#테이블에 조건 데이터 입력이
def condition_db(keyword, word_list, position, start, end, img, journalList):
    include_word =""
    #포함 단어가 여러개일 경우 ?-?로 구분
    for n in word_list:
        include_word += n+"?-?"
    include_word = include_word[:-3]
    period = start+'~'+end
    #언론사 선택, 지금 언론사 선택은 제외하였음
    if journalList == []:
        journal = ""
    cursor = db.cursor()
    cursor.execute("""INSERT INTO news_condition (keyword, include_word,period, 
                position, img, journal) VALUES 
                ("%s", "%s", "%s", "%s", "%s", "%s")"""%(keyword, include_word, period, position, img, journal))
    db.commit()
    #제일 마지막 auto_increment 가져옴
    cursor.execute("""SELECT AUTO_INCREMENT FROM information_schema.tables
                WHERE table_name = 'news_condition' 
                AND table_schema = DATABASE() ;""")
    number = int(cursor.fetchone()[0])-1
    db.commit()
    cursor.close()
    return str(number)

#페이지 넘길때 필요한 함수, 최근 조건값 읽어들이고 해당 페이지 기사 10개 리스트로 반환
def page_move(page, sort):
    #최신순/오래된순
    if sort == 'yng':
       sort_sql = "desc"
    else: # old
       sort_sql = "asc"
    
    cursor = db.cursor()
    cursor.execute("""SELECT AUTO_INCREMENT FROM information_schema.tables
                WHERE table_name = 'news_condition' 
                AND table_schema = DATABASE() ;""")
    table_num = str(int(cursor.fetchone()[0])-1)
    cursor.execute("SELECT COUNT(*) FROM news_"+table_num+";")
    article_num =  int(cursor.fetchone()[0])
    count = int(article_num / 10) +1
    if article_num %10 ==0:
        count -=1
    
    art_no = int(page)*10-10
    sql = "SELECT * FROM news_"+table_num+" ORDER BY day "+sort_sql+" limit %s, %s;"
    cursor.execute(sql ,(art_no, art_no+11))
    tempList = cursor.fetchall()
    title, link=[], []
    #DB에서 가져온 링크/제목 정보를 리스트에 저장
    for r in tempList:
        title.append(r[2])
        link.append(r[1])
        
    result = [title, link]
    cursor.execute("SELECT * FROM news_condition WHERE no="+table_num+";")
    # 검색 조건 가져옴
    condList = list(cursor.fetchone())
    del condList[0]
    
    cond_result = cond_print(condList[0],  condList[2].split('~')[0],condList[2].split('~')[1],\
                            condList[1].split('?-?'), condList[3], condList[4] )
    
    cursor.close()
    return (result, cond_result, count)
    
    
#그냥 메인 url 함수
@app.route('/')
def index():
    return render_template('index.html', article_list =[[],[]], count=0, page=0, condList=[])

#날짜 계산 함수
def period_calc(day):
    #python에서 날짜 계산
    start_str = str(datetime.datetime.today() + datetime.timedelta(days=- day)).split(' ')[0]
    end_str = str(datetime.datetime.today()).split(' ')[0]
    #년/월/일로 나눠줌
    start_list = start_str.split('-')
    end_list = end_str.split('-')
    # (년.월.일) 형식으로 변경
    startDate = start_list[0]+'.'+start_list[1]+'.'+start_list[2]
    endDate = end_list[0]+'.'+end_list[1]+'.'+end_list[2]
    # string으로 return
    return (str(startDate), str(endDate))

# 조건 검사하고 조건에 따라 뉴스 크롤링 해주는 곳
@app.route('/news/<page>', methods = ['GET', 'POST'])
def search_news(page):
    
    #페이지를 넘길 경우
    if request.method=='GET':
        #페이지번호
        page_n = page.split("_")[0]
        #정렬 기준
        sort_way = page.split("_")[1]
        
        result = page_move(page_n, sort_way)
        return render_template('index.html', article_list =result[0], count=result[2], page=int(page_n), condList=result[1], sort=sort_way)
    
    #최초 검색 경우
    
    result = [[],[],[]]
    # 웹에서 정보 받아들임
    keyword = request.form['inputKeyword'] #키워드
    includeKeyword = request.form['includeKeyword'] #포함 단어 
    include_position = request.form['include_position'] #포함 위치  title / both
    lastPeriod = request.form['lastPeriod'] #기간 설정  day / week / month / mydate
    startDate = 'startDate' #start date 기본 값
    endDate = 'endDate'  #end date 기본 값
    imgExist_value = request.form['imgExist_value'] #이미지 필수 여부 on/off
    sort_value = request.form['sort_value']
    
    #포함 단어 리스트로 구분
    includeKeywordList = includeKeyword.replace(' ', '').split(',')
    
    #날짜 설정
    if lastPeriod == 'mydate': # 기간 직접 입력일 경우, 웹에서 입력 값을 받음
        startDate = request.form['startDate'] #마지막 날짜
        endDate = request.form['endDate'] #마지막 날짜
        #날짜 string 형식 맞추기 ex> 2020.05.15
        startDate = startDate.replace('-', '.')
        endDate = endDate.replace('-', '.')
        
        
    else: # 직접설정 이외 radio 버튼 클릭 경우
        days = 0
        if lastPeriod == 'day': days=1  #하루
        elif lastPeriod == 'week': days=7  # 일주일
        else: days=30  # 한달
            
        #기간에 따라 다르게 날짜 설정
        startDate = period_calc(days)[0]
        endDate = period_calc(days)[1]
    
    # 이미지 포함 여부 on.off --> 1/0
    if imgExist_value == "off":
        imgExist = '0'
    else:
        imgExist = '1'
    
    #조건 검사 
    checking =  condition_right(keyword, includeKeywordList, startDate, endDate)
    if checking !='success' : # 조건 검사 성공하지 못한 경우
        print(checking)
        return render_template('index.html', article_list =[[],[]], warning = checking, count=0, page=1, condList=[], sort=sort_value)
    
    #조건 검사 성공한 경우
    cls = crawling(keyword, startDate,endDate, includeKeywordList,include_position,imgExist)
    
    #크롤링 class를 이용하여 언론사별 크롤링
    tempList = cls.donga()
    result[0].extend(tempList[0])
    result[1].extend(tempList[1])
    result[2].extend(tempList[2])
    
    tempList = cls.kmib()
    result[0].extend(tempList[0])
    result[1].extend(tempList[1])
    result[2].extend(tempList[2])
    
    tempList = cls.khan()
    result[0].extend(tempList[0])
    result[1].extend(tempList[1])
    result[2].extend(tempList[2])
    ''' ytn 아직 미완성
    tempList = cls.ytn()
    result[0].extend(tempList[0])
    result[2].extend(tempList[2])
    '''
    
    count = int(len(result[0]) / 10) +1
    if len(result[0]) %10 ==0:
        count -=1
    
    condList =cond_print(keyword,startDate,endDate,includeKeywordList,include_position,imgExist)
    number = condition_db(keyword, includeKeywordList, include_position, startDate, endDate, imgExist, [])
    tablename = crtable(number)  #테이블 생성
    input_article(tablename, result)
    
    #[1페이지, 최신순]으로 출력
    article_list = page_move(1, sort_value)[0]
    
    return render_template('index.html', article_list = article_list, count=count, page=1,condList=condList, sort=sort_value)
    

# 기사 간결하게 보여주기
@app.route('/article', methods = ['POST'])
def article_clean():
    link = request.form['url']
    
    head = {'User-Agent': 'Mozilla/5.0', 'referer': link}
    req = urllib.request.Request(link, headers=head)
    html = urllib.request.urlopen(req)
    bs = BeautifulSoup(html, 'lxml')
    #불필요한 태그 지우기
    ul = re.compile('<ul.*>.*</ul>')
    dv = re.compile('<div.*>.*</div>')
    js = re.compile('<script.*>.*</script>')
    tag = re.compile('<.*>')
    
    #script 태그 지우기
    selects = bs.findAll('script')
    for select in selects:
        select.decompose()
            
    if 'donga' in link: #동아일보
        title = bs.find("h1", class_="title")
        article_sub = bs.find("div", class_="article_txt")
        article = ul.sub('', str(article_sub))
        img_tag = bs.find("div",class_="articlePhotoC")
        
        #기사 내 다른div태그 지우기
        div_ = bs.findAll("div")
        for d in div_:
            if "articlePhotoC" not in str(d): #사진 태그 제외
                article = article.replace(str(d),'')
        
    elif 'kmib' in link: #국민일보
        title = bs.find("h3")
        article = bs.find("div", id="articleBody")
        img_tag = bs.find("div", align="center")
        div_ = bs.findAll("div")
        article = ul.sub('', str(article))
        for d in div_:
            if "center" not in str(d):
                article = article.replace(str(d),'')
        
    elif 'khan' in link: #경향신문
        title = bs.find("h1", id="article_title")
        article = bs.find("div", id="articleBody")
        img_tag = bs.find("div",class_="art_photo_wrap")
    
    style = "<head><style>body{width: 60%;margin:0 auto}</style></head><body>"
    # 스타일 태그 추가
    article = style+str(title)+article+"</body>"
    # render_template 없이 그대로 랜더링하여 보여줌
    return article


#조건 리스트로 만들어서 출력 편하게 함수
def cond_print(keyword,startDate,endDate,includeKeywordList,include_position,imgExist):
    print('includeKeywordList : ',includeKeywordList)
    for i in includeKeywordList:
        include = i +', '
    include = include[:-2]
    if include == "":
        include = '없음'
    
    if include_position =='both':
        position = '제목+본문'
    else:
        position = '제목'
        
    if imgExist == '0':
        img = '미포함 가능'
    else: 
        img = '필수 포함'
        
    return [keyword, startDate,endDate,include,position,img]

# 조건 값 검사 함수
def condition_right(keyword, includeKeyword, startDate, endDate):
    print('condition checking')
    if len(keyword) <1:
        return '최소 한 글자 이상은 입력해야합니다.'
    elif len(includeKeyword) >3:
        return '포함 단어는 최대 3개까지 입력할 수 있습니다.'
    elif startDate > endDate :
        return '날짜 입력이 잘못되었습니다.'
    else:
        return 'success'

if __name__ == '__main__':
    app.debug = True
    app.run(host = "127.0.0.1",  port =5000)
    app.run(debug = True)
    