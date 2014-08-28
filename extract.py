# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup
import re
import datetime
import pymongo

def getGender(text):    
    gender_cht = text.split(u'性別')[1].split(u'生')[0].replace(':', '').strip()
    if gender_cht == u'女':
        gender = 'F'
    elif gender_cht == u'男':
        gender = 'M'
    else:
        gender = 'unknown'
    return gender

def getTitleDate(text):
    # e.g., icon and title5月份開始馬德里機場進出補3歐 -status icon and datestatus icon and date2012-05-23, 07:41/ status icon and date
    title = text.split('-status')[0].split('icon and title')[-1].strip()

    ## get 2012-05-23, 07:41
    ## date_str_tpl: ('2012', '05', '23', '07', '41')
    date_str_tpl = re.findall(r'([0-9]{4})-([0-9]{2})-([0-9]{2}),\s([0-9]{2}):([0-9]{2})', text)[0]
    ## date_tpl: (2012, 5, 23, 7, 41)
    date_tpl = tuple(map(lambda x:int(x), date_str_tpl))

    ## this yields a datetime object, e.g., datetime.datetime(2012, 5, 23, 7, 41)
    date = datetime.datetime(*date_tpl) 

    return (title, date)   

def content_filter(text):
    ## drop html tags
    text = re.sub(r'(?i)</?[a-z]+>', '', text)

    ## drop urls such as "http://www.backpackers.com.tw/forum/showthread.php?p=3995072"
    text = re.sub(r'(?i)http[s]?://[a-z0-9./?=&]+', '', text)

    ## trim spaces
    text = text.strip()
    return text

def extract_post_content(post):
    """
    Parameters
        post: a <BeautifulSoup.Tag> object

    Returns:
        extracted data in dictionary format
    """

    ## get current post id
    res = re.findall(r'^edit([0-9]+)$', post.attrMap['id'])
    if res:
        post_id = res[0]
    else:
        ## no id found: skip this post
        ## return empty dictionary
        return False

    ## get username
    username = post.find(attrs={"class": "bigusername"}).text

    ## get post content
    content_raw = post.find(id='post_message_'+post_id).text
    content = content_filter(content_raw)

    ## get gender, title and date
    date, gender, title = None, None, None
    for x in post.findAll(attrs={"class": "smallfont"}):
        
        ## get gender
        if u'性別' in x.text:
            gender = getGender(x.text)

        ## get title and date
        if x.text.startswith('icon and title'):
            title, date = getTitleDate(x.text)


    data = {
        'username': username,
        'content': content,
        'content_raw': content_raw,
        'date': date,
        'title': title,
        'gender': gender
    }

    return data

def display(data):
    for k, v in data.items():
        print k, ':', v

if __name__ == '__main__':

    ## connect to mongodb
    db = pymongo.Connection('doraemon.iis.sinica.edu.tw')['espanol']
    
    ## use certain collection
    co = db['bk.posts']

    ## load html file
    raw_html = open('data/8.html').read()
    soup = BeautifulSoup(raw_html)

    ## find all posts
    posts = soup.findAll(id=re.compile(r"^edit[0-9]+$"))

    for post in posts:

        data = extract_post_content(post)

        if not data:
            ## not a valid post. Ad perhaps
            continue

        display(data)
        raw_input()

        ## uncomment this line to performa mongo insertion
        # co.insert(data)





