from flask import Flask, session, render_template, request, redirect
from bs4 import BeautifulSoup
from konlpy.tag import Kkma
import selenium
import requests
import pymysql
import base64
import os

app = Flask(__name__, template_folder='./templates')
app.env = 'development'
app.debug = True
app.secret_key = 'day9assignment-secretkey'

def getConnection():
    db = pymysql.connect(host='localhost', 
                         port=3306, 
                         user='root',
                         password='csman114',
                         db='day9', charset='utf8',
                         cursorclass=pymysql.cursors.DictCursor)
    
    return db

def checkUser(username, password):
    try:
        db = getConnection()
        cursor = db.cursor()
        cursor.execute('select username, password from users')
        validate = False
        for user in cursor.fetchall():
            if user['username'] == username and user['password'] == password:
                validate = True
                break
        
        db.close()
        return validate
    except Exception as ex:
        print(ex)
        return False    

@app.route('/')
def index():
    print('index')
    if session.get('username'):
        username = session.get('username')    
        return render_template('logout.html', username=username)
    else:
        return render_template('login.html', message='')

@app.route('/login', methods=['GET', 'POST'])
def login():
    print('login')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(username, password)
        print(checkUser(username, password))
        if checkUser(username, password):
            session['username'] = username
            return render_template('logout.html',username=username)
        else:
            return render_template('login.html', message="username 혹은 password가 잘못되었습니다.")

    return render_template('login.html', message='')

@app.route('/logout')
def logout():
    session['username'] = False
    return redirect('/login')

def saveUser(username, password):
    try:
        db = getConnection()
        cursor = db.cursor()
        sql = """insert into users(username,password)
                values (%s, %s)"""
        cursor.execute(sql, (username, password))
        db.commit()
        db.close()
        return True
    except Exception as ex:
        print(ex)
        return False

@app.route('/join',methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        saveUser(username, password)

        return redirect('/login')

    return render_template('join.html')
    
def deleteUser(username):
    try:
        print(username)
        db = getConnection()
        cursor = db.cursor()
        sql = f"delete from users where username='{username}'"
        cursor.execute(sql)
        db.commit()
        db.close()
        return True
    except Exception as ex:
        print(ex)
        return False

@app.route('/withdrawl/<username>')
def withdrawl(username):
    deleteUser(username)
    return render_template('login.html',message='')


@app.route('/news/ranking',methods=['GET','POST'])
def news():
    result = []
    if request.method == 'GET':
        url = request.args.get('url')
        if url != None:
            content = requests.get(url).content
            soup = BeautifulSoup(content,'html.parser')
            result=[{'link':f"/news/words?url={title['href']}", 'title':title.get_text()} for title in soup.select('ul.list_news2 a.link_txt')]
    else:
        regdate = request.form.get('regdate')     
        url = f'/news/ranking?url=https://media.daum.net/ranking/?regDate={regdate}'
        return redirect(url)
    
    return render_template('news.html',result=result)

@app.route('/news/words')
def coutner():
    url = request.args.get('url')
    content = requests.get(url).content
    soup = BeautifulSoup(content, 'html.parser')
    title = soup.select('.tit_view')[0].get_text()
    summary = soup.select('.summary_view')[0].get_text()
    pharas = [ phara.get_text() for phara in soup.select('.article_view p')]
    article = title+' '+summary+' '+' '.join(pharas)
    kkma = Kkma()
    result = [ word for word, kind in kkma.pos(article) if kind in ['NNG', 'NNP']]
    result = [ (word, result.count(word)) for word in set(result)]
    result = sorted(result, key=lambda x: x[1], reverse=True)
    return render_template('words_count.html', result=result)

from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
import base64
import requests
import os


app = Flask(__name__, template_folder='./templates')
app.env = 'development'
app.debug = True

def saveImage(keyword, base64List, dataSrcList):
    os.makedirs(f'./download/image/{keyword}', exist_ok=True)

    for i, link in enumerate(dataSrcList):
        res = requests.get(link)
        with open(f'./download/image/{keyword}/src-{i}.jpg', 'wb') as f:
            f.write(res.content)
    
    for i, link in enumerate(base64List):
        with open(f'./download/image/{keyword}/binary-{i}.jpg', 'wb') as f:
            f.write(link)

@app.route('/downloads/<keyword>')
def downloads(keyword):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    url = f'https://www.google.com/search?q={keyword}&rlz=1C1SQJL_koKR823KR823&source=lnms&tbm=isch&sa=X&ved=2ahUKEwijp-q537TpAhUUFogKHSXiAugQ_AUoAXoECBkQAw&biw=1036&bih=674&dpr=1.25'
    driver = webdriver.Chrome('chromedriver', options=options)
    driver.implicitly_wait(3)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    binaryList = [ tag.get('src') for tag in soup.select('img') if tag.has_attr('src') ]
    dataSrcList = [ tag.get('data-src') for tag in soup.select('img') if tag.has_attr('data-src')]
    base64List = [ base64.b64decode(link.split(',')[1]) for link in binaryList ]
    
    # 이미지 저장하기
    saveImage(keyword, base64List, dataSrcList)
    return render_template('download.html', result = binaryList+dataSrcList)

app.run(port=4000)