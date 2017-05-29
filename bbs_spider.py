# -*- coding: utf-8 -*-
import urllib.request;
import chardet
import re
import pandas
import sys
import os
import time
from selenium import webdriver
from selenium.common.exceptions import WebDriverException,TimeoutException,NoSuchElementException
from bs4 import BeautifulSoup, Comment, Tag
from urllib.error import URLError;
from collections import Counter


def has_class(tag):
    return tag.has_attr('class')

def findTag(content):
    while type(content) != Tag:
        content = content.parent
    while has_class(content) == False:
        content = content.parent
    return content.attrs

def tag_without_text(tag):
    data = tag.get_text().strip()
    if len(data) == 0:
        return True
    return False


#用正则表达式匹配时间
#reg = re.compile("\d{4}[- ./]\d{1}[- ./]\d{1}|\d{4}[- ./]\d{1}[- ./]\d{2}|\d{4}[- ./]\d{2}[- ./]\d{1}|\d{4}[- ./]\d{2}[- ./]\d{2}|\d{2}[- ./]\d{2})
pattern1 = re.compile('(^发表于: [0-9]{4}-[0-9][0-9]?-[0-9][0-9]? [0-9]{2}:[0-9]{2})|(^发表于 [0-9]{4}-[0-9][0-9]?-[0-9][0-9]? [0-9]{2}:[0-9]{2})|(^[0-9]{4}-[0-9][0-9]?-[0-9][0-9]? [0-9]{2}:[0-9]{2})')
pattern2 = re.compile('(^发表日期: [0-9]{4}-[0-9][0-9]?-[0-9][0-9]? [0-9]{2}:[0-9]{2})|(^发表于 [0-9]{4}-[0-9][0-9]?-[0-9][0-9]? [0-9]{2}:[0-9]{2})|(^[0-9]{4}-[0-9][0-9]?-[0-9][0-9]? [0-9]{2}:[0-9]{2})')
pattern3 = re.compile('(^发布于: [0-9]{4}-[0-9][0-9]?-[0-9][0-9]? [0-9]{2}:[0-9]{2})|(^发表于 [0-9]{4}-[0-9][0-9]?-[0-9][0-9]? [0-9]{2}:[0-9]{2})|(^[0-9]{4}-[0-9][0-9]?-[0-9][0-9]? [0-9]{2}:[0-9]{2})')

def isdate(tag):
    match1 = pattern1.match(tag.get_text())
    if match1 != None:
        return True
    match2 = pattern2.match(tag.get_text())
    if match2 != None:
        return True
    match3 = pattern3.match(tag.get_text())
    if match3 != None:
        return True
    return False

def p_text(texts, threshold):
    total = 0.0
    diff = 0.0
    average = 0.0
    
    if (len(texts) < threshold / 4):
        return 0
    
    if (threshold > 0 and len(texts) > threshold):
        return 0
    
    for text in texts:
        total += len(text)

    average = total / len(texts)

    for text in texts:
        diff += abs(len(text) - average)
    #print(diff / len(texts))
    if (abs(diff / len(texts)) < 2 and len(texts) > 2):
        return 0
    
    return (total)

    # 获取静态网页
    # response = urllib.request.urlopen(dataURL)
    # html = response.read()
    # #猜测字符编码
    # htmlCharsetGuess = chardet.detect(html)
    # htmlCharsetEncoding = htmlCharsetGuess["encoding"]
    # htmlCode_decode = html.decode(htmlCharsetEncoding, 'ignore')
    # htmlCode_encode = htmlCode_decode.encode("UTF-8")

def collect(dataURL, urlCount):
    page = 1
    TEXT = []
    print("处理 URL: %s" % (dataURL))
    # 除了PhantomJS也可以尝试Chrome等浏览器
    # option = webdriver.ChromeOptions()
    # prefs = {'profile.default_content_setting_values' : 
    #     {
    #        'images' : 2,
    #        'plugins': 2
    #     }
    # }
    # option.add_experimental_option('prefs',prefs)
    # driver = webdriver.Chrome(chrome_options=option)

    driver = webdriver.PhantomJS(service_args=['--load-images=false'])
    #不加载图片以加快网页加载速度
    #driver.implicitly_wait(10)
    #每个网页最多加载30秒，30秒内加载不出来就跳到下一个网页
    driver.set_page_load_timeout(30)

    try:
        driver.get(dataURL)
    except Exception as e:
        print (e)
        return

    html = driver.page_source
    soup = BeautifulSoup(html,"lxml")

    #去噪
    [script.extract() for script in soup.find_all('script')]
    [style.extract() for style in soup.find_all('style')]
    [img.extract() for img in soup.find_all('img')]
    [meta.extract() for meta in soup.find_all('meta')]
    #[form.extract() for form in soup.find_all('form')]
    [inputs.extract() for inputs in soup.find_all('input')]
    [select.extract() for select in soup.find_all('select')]
    [button.extract() for button in soup.find_all('button')]
    [dd.extract() for dd in soup.find_all('dd')]
    [dt.extract() for dt in soup.find_all('dt')]
    [li.extract() for li in soup.find_all('li')]
    [br.extract() for br in soup.find_all('br')]
    [ui.extract() for ui in soup.find_all('ui')]

    #去除所有注释
    for element in soup(text=lambda text: isinstance(text, Comment)):
        element.extract()

    #去除所有含有链接的标签
    def has_href(tag):
        return tag.has_attr('href')
    [tag_with_href.extract() for tag_with_href in soup.find_all(has_href)]

    [tag_without_text.extract() for tag_without_text in soup.find_all(tag_without_text)]


    #用正则表达式匹配时间
    #reg = re.compile("\d{4}[- ./]\d{1}[- ./]\d{1}|\d{4}[- ./]\d{1}[- ./]\d{2}|\d{4}[- ./]\d{2}[- ./]\d{1}|\d{4}[- ./]\d{2}[- ./]\d{2}|\d{2}[- ./]\d{2})
    #dates = soup.find_all(text = reg)
    dates = soup.find_all(isdate)
    date_tags = []

    #找出date对应的标签
    for date in dates:
        date_tags.append(''.join(findTag(date)['class']))

    #print (dates.string)

    #找出时间出现的次数
    date_appears = dict((a,date_tags.count(a)) for a in date_tags)
    if len(date_tags) == 0:
        date_count = 0
    else:
        date_tag = max(date_tags, key=date_tags.count)
        TEXT.append(soup.find(isdate).string)
        date_count = date_appears[date_tag]


    deepest_classes = []
    #找到所有最深层的，带有class属性的节点
    all_class = soup.body.find_all(has_class)
    class_and_text = {}
    for descedent in all_class:
        if descedent.find(has_class) == None:
            deepest_classes.append(descedent)

    #利用停用词进行过滤
    stop_words = []
    rF = open(os.path.dirname(__file__) + '/stop_words.txt', "r")
    stop_words = rF.readlines()
    st = []
    for stop_word in stop_words:
        st.append(stop_word.strip('\n'))
    sw = tuple(st)


    #以tag的class名为key，tag所包含的所有文本为value，构建字典
    for classes in deepest_classes:
        name = classes.attrs.get('class')[0]
        data = classes.get_text().replace("\n","").replace("\r","").replace(" ","").replace("\t","")
        if len(data) > 0:
            if data.startswith(sw) or data.endswith(sw):
                continue
            elif not name in class_and_text:
                class_and_text[name] = [data]
            else:
                class_and_text[name].append(data)

    class_and_probility = {}

    for key in class_and_text.keys():
        class_and_probility[key] = p_text(class_and_text[key], date_count)

    #利用评估函数对这些class进行排序，选出最有可能是正文的
    text_class = max(class_and_probility.items(), key=lambda x:x[1])[0]

    #自动翻页
    while True:
        print ("page=%s"%page)
        for tag in soup.select('.'+text_class):
            TEXT.append(tag.get_text().replace("\n","").replace("\r","").replace(" ","").replace("\t",""))
        try:
            #driver.find_element_by_partial_link_text("下一页").click()
            driver.find_element_by_xpath("//a[contains(text(),'下一页')]").click()
            time.sleep(2)
        except TimeoutException:
            print("页面 %s 打开超时"%(page))
            page += 1
            continue
        except NoSuchElementException:
            break
        except WebDriverException as e:
            print(e)
            break
        soup = BeautifulSoup(driver.page_source, "lxml")
        page += 1

    #将文本以csv格式存入
    driver.quit()
    data = pandas.DataFrame({
        'TEXT' : TEXT
        })
    data.to_csv(os.path.dirname(__file__) + '/data/' + str(urlCount) +'.csv', encoding='utf-8', index=True)
    
if __name__ == '__main__':
    with open(os.path.dirname(__file__) + '/url_lists.txt', 'r') as url_lists:
        url_count = 0
        status = 200
        while True:
            url = url_lists.readline()
            if not url:
                break
            try:
                urllib.request.urlopen(url)
            except URLError as e:
                print("get URL:%s Failed!" % (url))
                print (e)
                continue
            else:
                collect(url,url_count)
                url_count += 1

            

