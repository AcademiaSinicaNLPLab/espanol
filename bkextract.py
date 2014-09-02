# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup
import re
import datetime
import pymongo

mapping = {
    u"&gt;" : u">",
    u"&lt;" : u"<",
    u"&amp;": u"&",
    u"&quot;":u'"',
    u"&ldquo;":u'“',
    u"&rdquo;":u'”',
    u"&lsquo;":u"‘",
    u"&rsquo;":u"’"
}

def convert_special_html(mapping, text):
    for old in mapping:
        new = mapping[old]
        text = text.replace(old, new)
    return text

def getGender(text):

    try:
        gender_cht = text.split(u'性別')[1].replace(':', '').strip().split(u"感謝")[0]
    except:
        return 'unknown'

    if u'女' in gender_cht:
        gender = 'F'
    elif u'男' in gender_cht:
        gender = 'M'
    else:
        gender = 'unknown'

    return gender

def getPostTextNum(text):
    """
    text: u"客棧之光&nbsp;文章:2,073性別: 女生感謝: 372次/338篇註冊日期: 2006-08-19"
    """
    res = re.findall(u"文章"r":\s?([0-9,?]+)", text, re.IGNORECASE)
    res = [int(x.replace(',','')) for x in res]
    if res:
        return res[0]
    else:
        return None
    # postNum = re.findall(r"(?i):[0-9],[0-9]{3}",text)[0]

def getPostOfThanksNum(text):
    # 感謝: 3次/2篇
    # thanksNum_cht = text.split(u'')[1].replace(':', '').strip()
    res = re.findall(u"感謝"r":\s*([0-9,]+)"u"次"r"/([0-9,]+)"u"篇",text)
    if res:
        thanksNum = tuple( map(lambda x: int(x.replace(',', '')), res[0]) )
    else:
        thanksNum = (None, None)
    return thanksNum

def getTitleDate(text):
    # e.g., icon and title5月份開始馬德里機場進出補3歐 -status icon and datestatus icon and date2012-05-23, 07:41/ status icon and date
    title = text.split('-status')[0].split('icon and title')[-1].strip()

    ## get 2012-05-23, 07:41
    ## date_str_tpl: ('2012', '05', '23', '07', '41')
    date_str_tpl = re.findall(r'([0-9]{4})-([0-9]{2})-([0-9]{2}),\s([0-9]{2}):([0-9]{2})', text)[0]
    ## date_tpl: (2012, 5, 23, 7, 41)
    date_tpl = tuple(map(lambda x:int(x), date_str_tpl))

    ## this yields a datetime object, e.g., datetime.datetime(2012, 5, 23, 7, 41)
    # datetime.datetime(date_tpl[0], date_tpl[1], ...)

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
    content_raw = post.find(id='post_message_'+post_id)
    ## remove quotation
    content =[]

    for post_content in content_raw:

        ## check if current content is a quote or not
        isQuote = False
        try:
            quote = post_content.find(attrs={'class':'alt2 inner-quote'})
            isQuote = True if quote else False
        except TypeError:
            isQuote = False

        ## do nothing if a quote shows up
        if isQuote:
            continue
        else:
            ## NavigableString --> str(...)
            text = ""
            try:
                text = post_content.text
            except AttributeError:
                text = unicode(post_content)
                text = text.strip()
            if not text:
                continue
            # print 'post_content:', [text]

            ## chang &gt; to >...etc
            pruned = convert_special_html(mapping, text=text)
            ## eliminate urls, </div>.
            cleancontent = content_filter(pruned)
            # print cleancontent
            content.append(cleancontent)            

    ## get gender, title and date
    date, gender, title = None, None, None
    # print '>>>> post'
    for x in post.findAll(attrs={"class": "smallfont"}):
        # print x.text
        # print u'性別' in x.text
        # print u'文章' in x.text
        # print u'感謝' in x.text
        # print '<<'
        # raw_input()
        ## get gender
        if u'性別' in x.text:
            gender = getGender(x.text)
        ## get No.post 
        if u"文章" in x.text:
            post_frequency = getPostTextNum(x.text)
        ## get No.be thanked / posts
        if u'感謝' in x.text:
           post_of_thanks_number= getPostOfThanksNum(x.text)
        ## get title and date
        if x.text.startswith('icon and title'):
            title, date = getTitleDate(x.text)


    data = {
        'username': username,
        'content': content,
        #'content_raw': content_raw,
        'date': date,
        'title': title,
        'gender': gender,
        ## post_frequency: int or None
        'No._of_post': post_frequency,
        ## post_of_thanks_number: tuple ( <int>次, <int>篇)
        'thanks(times,articles)': post_of_thanks_number
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

    src = "all_bkcont_test/10.html"

    ## load html file
    raw_html = open(src).read()
    soup = BeautifulSoup(raw_html)

    ## find all posts
    posts = soup.findAll(id=re.compile(r"^edit[0-9]+$"))

    for post in posts:

        data = extract_post_content(post)

        if not data:
            ## not a valid post. Ad perhaps
            continue

        data['source'] = src
      
        display(data)
        raw_input()

        ## uncomment this line to performa mongo insertion
        # co.insert(data)
