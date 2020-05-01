# made by Koo Minku
# 20200416
# Korean News Crawl with condition program
# python flask
# Maria DB

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
                    passwd="rnalsrn12", 
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
        articleList[2][i] = articleList[2][i].replace('.', '-')
        cursor.execute("SELECT STR_TO_DATE('"+articleList[2][i]+"', '%Y-%m-%d');")
        datetime = cursor.fetchone()[0]
        print(articleList[1][i])
        print(articleList[0][i])
        print(articleList[2][i])
        cursor.execute(sql ,( articleList[1][i], articleList[0][i], articleList[2][i]))
    db.commit()
    cursor.close()
    return 0

#테이블 생성
def crtable(number):
    cursor = db.cursor()
    cursor.execute( """CREATE TABLE  %s (
                        no int AUTO_INCREMENT,
                        title varchar(60) NOT NULL,
                        link varchar(90) NOT NULL,
                        day date,
                        PRIMARY KEY (NO)
                    );""" %('news_'+number))
    print("make table number 000 ", number)
    db.commit()
    cursor.close()
    return 'news_'+number


#테이블에 조건 데이터 입력이
def condition_db(keyword, word_list, position, start, end, img, journalList):
    include_word =""
    for n in word_list:
        include_word += n+"?-?"
    include_word = include_word[:-3]
    period = start+'~'+end
    if journalList == []:
        journal = ""
    cursor = db.cursor()
    cursor.execute("""INSERT INTO news_condition (keyword, include_word,period, 
                position, img, journal) VALUES 
                ("%s", "%s", "%s", "%s", "%s", "%s")"""%(keyword, include_word, period, position, img, journal))
    db.commit()
    
    cursor.execute("""SELECT AUTO_INCREMENT FROM information_schema.tables
                WHERE table_name = 'news_condition' 
                AND table_schema = DATABASE() ;""")
    number = int(cursor.fetchone()[0])-1
    db.commit()
    cursor.close()
    return str(number)

#페이지 넘길때 필요한 함수, 최근 조건값 읽어들이고 해당 페이지 기사 10개 리스트로 반환
def page_move(page, sort):
    
    if sort == 'yng':
       sort_sql = "desc"
    else: # old
       sort_sql = "asc"
    
    cursor = db.cursor()
    #cursor.execute("SELECT COUNT(*) FROM news_condition;")
    #cursor.execute("SHOW TABLES;")
    cursor.execute("""SELECT AUTO_INCREMENT FROM information_schema.tables
                WHERE table_name = 'news_condition' 
                AND table_schema = DATABASE() ;""")
    table_num = str(int(cursor.fetchone()[0])-1)
    print(table_num)
    cursor.execute("SELECT COUNT(*) FROM news_"+table_num+";")
    article_num =  int(cursor.fetchone()[0])
    count = int(article_num / 10) +1
    if article_num %10 ==0:
        count -=1
    
    art_no = int(page)*10-10
    print('sort_sql',sort_sql)
    sql = "SELECT * FROM news_"+table_num+" ORDER BY day "+sort_sql+" limit %s, %s;"
    print(sql)
    cursor.execute(sql ,(art_no, art_no+11))
    tempList = cursor.fetchall()
    title, link=[], []
    for r in tempList:
        title.append(r[2])
        link.append(r[1])
        
        
    result = [title, link]
    print('table number is --',table_num)
    cursor.execute("SELECT * FROM news_condition WHERE no="+table_num+";")
    #print(cursor.fetchone())
    condList = list(cursor.fetchone())
    del condList[0]
    
    print(condList)
    cond_result = cond_print(condList[0],  condList[2].split('~')[0],condList[2].split('~')[1],\
                            condList[1].split('?-?'), condList[3], condList[4] )
    
    cursor.close()
    print("page function result :",result)
    return (result, cond_result, count)
    
    
#그냥 메인 url 함수
@app.route('/')
def index():
    cursor = db.cursor()
    
    cursor.close()
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
    print('condition on')
    
    #if page != "s":
    
    if request.method=='GET':
        print('pagepage ')
        print("href is " , page)
        #sList = session['resultList']
        page_n = page.split("_")[0]
        sort_way = page.split("_")[1]
        print(page_n)
        print(sort_way)
        print('123123123132')
        
        result = page_move(page_n, sort_way)
        print('result[1] is')
        print(result[1])
        # coundList db에서 읽기
        # article_list db에서 읽기
        return render_template('index.html', article_list =result[0], count=result[2], page=int(page_n), condList=result[1], sort=sort_way)
    
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
    
    #임시 설정 값
    '''
    imgExist_value = 'off'
    includeKeywordList = ['']
    keyword = "총선"
    include_position='both'
    lastPeriod='mydate'
    '''
    #-------
    
    #날짜 설정
    if lastPeriod == 'mydate': # 기간 직접 입력일 경우, 웹에서 입력 값을 받음
        startDate = request.form['startDate'] #마지막 날짜
        endDate = request.form['endDate'] #마지막 날짜
        #날짜 string 형식 맞추기 ex> 2020.05.15
        startDate = startDate.replace('-', '.')
        endDate = endDate.replace('-', '.')
        
        
        #임시 설정
        #startDate = '2020.04.19'
        #endDate = '2020.04.22'
        
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
    
    print(keyword)
    print(includeKeywordList)
    print(include_position)
    print(lastPeriod)
    print(startDate)
    print(endDate)
    
    print(imgExist_value)
    
    #조건 검사 
    checking =  condition_right(keyword, includeKeywordList, startDate, endDate)
    if checking !='success' : # 조건 검사 성공하지 못한 경우
        print('condition wrong')
        print(checking)
        return render_template('index.html', article_list =[[],[]], warning = checking, count=0, page=1, condList=[], sort=sort_value)
    
    '''
    result = [['http://news.khan.co.kr/kh_news/khan_art_view.html?artid=202004291649001&code=940202', \
    'http://news.kmib.co.kr/article/view.asp?arcid=0014514965', \
    'http://www.donga.com/news/Top/article/all/20200429/100862566/1',
    'http://news.khan.co.kr/kh_news/khan_art_view.html?artid=202004291942001&code=940100',\
    'http://news.khan.co.kr/kh_news/khan_art_view.html?artid=202004301041001&code=910100'], \
    ['이천물류창고 화재 사망자 최소 25명으로 늘어나', '“오거돈 부산시장 성추행 사건…총선 영향 미칠 중대사건 편의 봐준 것 아닌가”',\
    '일본·중국·홍콩·독일까지…해외 언론, KBO리그 개막전 취재 문의 쇄도',\
    '단국대 의대 교수 “조국 딸 입학 도움되라고 논문 1저자 등재”',\
    '정진석 “나한테 김종인 띄워달라더니··· 홍준표는 통합당의 미래 아니다” '], ['2020.04.25', '2020.04.24',\
    '2020.04.21','2020.04.22','2020.04.28']]
    
    
    
    count = int(len(result[0]) / 10) +1
    if len(result[0]) %10 ==0:
        count -=1
    
    condList =cond_print(keyword,startDate,endDate,includeKeywordList,include_position,imgExist)
    number = condition_db(keyword, includeKeywordList, include_position, startDate, endDate, imgExist, [])
    print('db input success-condition\n and table number is ', number)
    tablename = crtable(number)  #테이블 생성
    input_article(tablename, result)
    print("sort_value : ",sort_value)
    article_list = page_move(1, sort_value)[0]
    print("\nresult function result :",article_list)
    return render_template('index.html', article_list = article_list, count=count, page=1,condList=condList)
    '''
    
    
    #result = [ [], [] ]
    cls = crawling(keyword, startDate,endDate, includeKeywordList,include_position,imgExist)
    
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
    '''
    tempList = cls.ytn()
    result[0].extend(tempList[0])
    result[2].extend(tempList[2])
    '''
    
    print("-------\n"*10)
    print(result)
    print("-------\n"*10)
    count = int(len(result[0]) / 10) +1
    if len(result[0]) %10 ==0:
        count -=1
    
    condList =cond_print(keyword,startDate,endDate,includeKeywordList,include_position,imgExist)
    number = condition_db(keyword, includeKeywordList, include_position, startDate, endDate, imgExist, [])
    print('db input success-condition\n and table number is ', number)
    tablename = crtable(number)  #테이블 생성
    input_article(tablename, result)
    
    
    article_list = page_move(1, sort_value)[0]
    
    return render_template('index.html', article_list = article_list, count=count, page=1,condList=condList, sort=sort_value)
    

# 기사 간결하게 보여주기
@app.route('/article', methods = ['POST'])
def article_clean():
    link = request.form['url']
    
    file_start = re.compile('<.*>')
    file='./static/'
    
    head = {'User-Agent': 'Mozilla/5.0', 'referer': link}
    req = urllib.request.Request(link, headers=head)
    html = urllib.request.urlopen(req)
    bs = BeautifulSoup(html, 'lxml')
    ul = re.compile('<ul>.*</ul>')
    js = re.compile('<script.*>.*</script>')
    tag = re.compile('<.*>')
    img_name = str(datetime.datetime.now())
    img_name = img_name.replace(' ','-').replace('.','-').replace(':','-')+'.jpg'
    
    selects = bs.findAll('script')
    for select in selects:
        select.decompose()
            
    if 'donga' in link: #동아일보
        
        title = bs.find("h1", class_="title").text
        
        article_sub = bs.find("div", class_="article_txt")
        
        article = ul.sub('', str(article_sub))
        
        img_tag = bs.find("div",class_="articlePhotoC")
        
    elif 'kmib' in link: #국민일보
        title = bs.find("h3").text
        article = bs.find("div", id="articleBody")
        img_tag = bs.find("div", id="articleBody")
        
    elif 'khan' in link: #경향신문
        title = bs.find("h1", id="article_title").text
        article = bs.find("div", id="articleBody")
        img_tag = bs.find("div",class_="art_photo_wrap")
        
    try:
        imgURL = img_tag.find('img').get('src')
        urllib.request.urlretrieve(imgURL, './static/img_file/'+img_name)
    except(AttributeError):
        print("no img")
    
    
    print('that is result value')
    
    article = str(article).split('<br')
    
    articleList = []
    for art in article: #태그 다 지우고 리스트에 추가
        input = tag.sub('', str(art)).replace('/>','')
        articleList.append(input)
    
    #공백 리스트 count해서 나중에 html <br> 태그로 변경
    for n in range(articleList.count('')):
        articleList.remove('')
    
    result = [title, articleList]
    
    return render_template('article.html', article=result, img_name=img_name)


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
    