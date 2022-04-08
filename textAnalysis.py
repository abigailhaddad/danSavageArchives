# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 15:32:21 2020
This scrapes Dan Savage archives from the Chicago Reader site and cleans them up
and lets us do some text analysis on them

"""
from itertools import chain
from bs4 import BeautifulSoup
import urllib.request
from bs4.element import Comment
import nltk
import pandas as pd
import re
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
import collections
from nltk.corpus import stopwords

def getAllUrls():
    # this finds and opens and parses all the urls from the url below
    parser = 'html.parser'
    allLinks={}
    for pageNumber in range(0, 53):
        url=f"https://www.chicagoreader.com/chicago/ArticleArchives?author=847366&page={pageNumber}"
        resp = urllib.request.urlopen(url)
        soup = BeautifulSoup(resp, parser, from_encoding=resp.info().get_param('charset'))
        allLinks[pageNumber]=[]
        for link in soup.find_all('a', href=True):
            allLinks[pageNumber].append(link['href'])
    return(allLinks)

def cleanUrls(dictionary):
    cleanDict={}
    for pageNumber in list(dictionary.keys()):
       cleanDict[pageNumber]=list(set([i for i in dictionary[pageNumber] if "savage" in i.lower()]))
       if len(cleanDict[pageNumber])<25:
           print(pageNumber)
    return(cleanDict)
    
def flatten_dict_values(dictionary):
    return chain(*dictionary.values())

def tag_visible(element):
    #thank you stackexchange
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return(False)
    if isinstance(element, Comment):
        return(False)
    return(True)

def text_from_html(soup):
    #thank you stackexchange
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def getText(url):
    parser = 'html.parser'
    resp = urllib.request.urlopen(url)
    soup = BeautifulSoup(resp, parser, from_encoding=resp.info().get_param('charset'))
    text=text_from_html(soup)
    return(text)
    
def mainPullData():
    urls=getAllUrls()
    cleanThem=cleanUrls(urls)
    allUrls=list(set(flatten_dict_values(cleanThem)))
    textList=[]
    for url in allUrls:
        try:
            text=getText(url)
            textList.append(text)
            print("did")
        except:
            print(url)
    return(textList)

def genSubstrings():  
    substrings=["Send questions to Savage Love, Chicago Reader, 11 E. Illinois, Chicago 60611.",
                "Care to comment? See this column at chicagoreader.com . Send questions to mail@savagelove.net . Download a new Savage Lovecast every Tuesday at thestranger.com/savage .",
                "\u2002v  Download the Savage Lovecast every Tuesday at savagelovecast.com .           Tags: Savage Love", "© Dan Savage",
                "Find more info at Jointheimpact.com .  ","Care to comment? Find this column at chicagoreader.com .", "Send questions to mail@savagelove.net .", "And download a new Savage Lovecast every Tuesday at thestranger.com/savage .",
                "Download the Savage Lovecast every Tuesday at thestranger.com .",
                "Download the Savage Lovecast at savagelovecast.com .",
                "Download the Savage Lovecast every Tuesday at thestranger.com/savage .",
                "Download the Savage Lovecast every Tuesday at savagelovecast.com .",
                "Send questions to Savage Love, Chicago Reader, 11 E. Illinois, Chicago 60611 or to letters@savagelove.net.",
                "Download the Savage Lovecast every \nTuesday at thestranger.com/savage ",
                "Send questions to Savage Love, Chicago Reader, 11 E. Illinois, 60611, or  to letters@savagelove.net.",
                "Download the Savage Lovecast every Tuesday at savagelovecast.com.",
                "Send letters to mail@savagelove.net .", 
                "Find the Savage Lovecast every Tuesday at thestranger.com/savage .",
                "Download the Savage Lovecast every week at savagelovecast.com .",
                "Send questions to Savage Love, Chicago Reader, 11 E. Illinois, Chicago 60611.",
                "© Dan Savage",
                "Download the S avage Lovecast at savagelovecast.com",
                "By  Dan Savage  @fakedansavage",
                "click to enlarge",
                "Columns & Opinion"]
    return(substrings)

def cleanString(string):
    substrings=genSubstrings()
    pattern = re.compile(
    "(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|"
    "Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|"
    "Dec(ember)?)\s+\d{1,2},\s+\d{4}")
    try:
        date=pattern.search(string).group()
        try:
            cleaned=string.split("Subscribe")[1]
        except:
            cleaned=string.split("Donate")[1]
        realCleaned=cleaned.split("More Savage Love")[0].split("Tags:")[0]
        stripped=realCleaned.strip()
        for sub in substrings:
            stripped=stripped.replace(sub,"")
        return([date,stripped.strip()])
    except:
        print(string)
        pass

def main():
    textList=mainPullData()
    dropDupsList=list(set(textList))
    cleanList=[cleanString(i) for i in dropDupsList]
    lengthsOfList=[[i[0], i[1]] for i in cleanList if i]
    df = pd.DataFrame(lengthsOfList, columns =['Date', 'Text']) 
    df['Date']=pd.to_datetime(df['Date'])
    df['Year']=df['Date'].dt.year
    df['Text']=df['Text'].str.strip()
    #this is not doing what it should
    df['Text']=df['Text'].str.replace("\\", "") 
    return(df)
    

def getTopWords(df):
    listOfLists=df['Text'].str.split()
    flat_list = [item for sublist in listOfLists for item in sublist]
    stop_words = set(stopwords.words('english'))
    flat_list_no_stopwords=[i for i in flat_list if i not in stop_words and len(i)>2]
    clean_words=[i.lower().replace(".","") for i in flat_list_no_stopwords]
    topWords=collections.Counter(clean_words)
    return(topWords)
    
df=main()
topWords=getTopWords(df)
