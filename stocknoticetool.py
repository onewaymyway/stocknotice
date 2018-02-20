#! /usr/bin/env python3
#coding=utf-8
import urllib.parse
import urllib.request
import json
import time
import datetime
import re
import pandas as pd
import tushare as ts
import sys
import os

stockBasicInfo=None
myG={}

savePath="notices/"
url = 'http://query.sse.com.cn/security/stock/queryCompanyStatementNew.do'

user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
valuesSH = {
          #'cb' : 'jQuery110209612188022583723_1405057078072',
          'jsonCallBack' : 'jsonpCallBack334',
     'isPagination' : True,
     'productId' : '601918',
     'keyWord' : '',
     'isNew' : 1,
     'reportType2' : '',
     'reportType' : 'ALL',
     'beginDate' : '2017-10-31',
          'endDate' : '2018-01-30',
           'pageHelp.pageSize' : 999,
     'pageHelp.pageCount' : 50,
     'pageHelp.pageNo' : '1',
     'pageHelp.beginPage' : '1',
     'pageHelp.cacheSize' : '1',
     'pageHelp.endPage' : '5',
          '_' : '1405057078095'
         }


headersSH = {
    'Accept' : '*/*',
           'Accept-Encoding' : 'gzip,deflate,sdch',
            'Accept-Language' : 'zh-CN,zh;q=0.9',
            'Connection' : 'keep-alive',
            'Cookie' : '',
            'Host' : 'query.sse.com.cn',
            'Referer' : 'http://www.sse.com.cn/disclosure/listedinfo/announcement/',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153',
            'X-Requested-With' : 'XMLHttpRequest'
            }

p=re.compile(r'class=\'td2\'>(.*?)span\>\</td\>', re.DOTALL)
pnest=re.compile(r'href=\'(.*?)\'(.*?)target=\"new\"\>(.*?)\</a\>(.*?)\[(.*?)\]', re.DOTALL)
ppage=re.compile(r'\<td\>当前第 \<span\>(.*?)\</span\> 页  共 \<span\>(.*?)\</span\> 页\</td\>')


valuesSZ = {
          #'cb' : 'jQuery110209612188022583723_1405057078072',
          'leftid' : 1,
     'lmid' : "drgg",
     'pageNo' : 1,
     'stockCode' : '000615',
     'keyword' : "",
     'noticeType' : '',
     'startTime' : '2001-02-01',
     'endTime' : '2018-02-15',
          'imageField.x' : 30,
           'imageField.y' : 12,
     'tzy' : ""
         }


headersSZ = {
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           'Accept-Encoding' : 'gzip, deflate',
            'Accept-Language' : 'zh-CN,zh;q=0.9',
            'Connection' : 'keep-alive',
            'Cookie' : '',
            'Host' : 'disclosure.szse.cn',
    'Origin' : 'http://disclosure.szse.cn',
            'Referer' : 'http://disclosure.szse.cn/m/search0425.jsp',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153',
            'X-Requested-With' : 'XMLHttpRequest'
            }


def doOneStock(htmlstr):
    #print(htmlstr)
    tnotice=pnest.findall(htmlstr)[0]
    #print(tnotice,len(tnotice))
    nt={}
    nt["date"]=tnotice[4]
    nt["url"]=tnotice[0]
    nt["title"]=tnotice[2]
    return nt

def getStockFromHTML(htmlStr):
    msp=p.findall(htmlStr);
    #print(msp)
    mList=[]
    for tt in msp:
        mList.append(doOneStock(tt))

    pageinfo=ppage.findall(htmlStr)[0]

    pageO={}
    pageO["page"]=int(pageinfo[0])
    pageO["total"]=int(pageinfo[1])
    return (mList,pageO)

def getSZNotice(code,begin="2006-01-31",end="2018-02-20",page=1):
    url="http://disclosure.szse.cn/m/search0425.jsp"
    valuesSZ["stockCode"]=code
    valuesSZ["pageNo"]=page
   
    valuesSZ["startTime"]=begin
    valuesSZ["endTime"]=end
    data = urllib.parse.urlencode(valuesSZ)
    turl=url+"?"+data;
    req = urllib.request.Request(turl, None, headersSZ)
    response = urllib.request.urlopen(req)
    the_page = response.read()
    tStr=the_page.decode("gbk")
    return getStockFromHTML(tStr)
def getSZStock(code,begin="2006-01-31",end="2018-02-20"):
    rstList=[]
    tList,pageO=getSZNotice(code,begin,end,1)
    rstList=rstList+tList
    while pageO["page"]<pageO["total"]:
        
        tList,pageO=getSZNotice(code,begin,end,pageO["page"]+1)
        rstList=rstList+tList
    
    return rstList

def removeJsonPStr(jsonpStr):
    pos=jsonpStr.find("(")
    jsonStr=jsonpStr[pos+1:]
    pos=jsonStr.rfind(")")
    jsonStr=jsonStr[:pos]
    return jsonStr
def getOneSHStock(code,begin="2006-01-31",end="2018-02-20"):
    valuesSH["productId"]=code
    valuesSH["isPagination"]=False
    valuesSH["beginDate"]=begin
    valuesSH["endDate"]=end
    data = urllib.parse.urlencode(valuesSH)
    turl=url+"?"+data;
    req = urllib.request.Request(turl, None, headersSH)
    response = urllib.request.urlopen(req)
    the_page = response.read()
    tStr=the_page.decode("utf8")
    tStr=removeJsonPStr(tStr) 
    
    jsonData=json.loads(tStr);
    #print(jsonData)
    nlist=jsonData["result"]
    mlist=[]
    for tnotice in nlist:
        nt={}
        nt["date"]=tnotice["SSEDate"]
        nt["url"]=tnotice["URL"]
        nt["title"]=tnotice["title"]
        #print(nt["date"])
        mlist.append(nt)
    #print(mlist)
    #print(len(mlist))
    return mlist

def getDayPairs(begin_date,end_date,dDate=1000):
    pairList=[]
    begin_date = datetime.datetime.strptime(begin_date, "%Y-%m-%d")  
    end_date = datetime.datetime.strptime(end_date,"%Y-%m-%d")  
    delta=datetime.timedelta(days=dDate)
    while begin_date<=end_date:
        nextDate=begin_date+delta
        if nextDate>end_date:
            nextDate=end_date
        pairList.append([begin_date.strftime("%Y-%m-%d"),nextDate.strftime("%Y-%m-%d")])
        begin_date = nextDate+datetime.timedelta(days=1) 
    return pairList
def sortKeyFun(stock):
    return stock["date"]

def sortDataList(tList):
    tList.sort(key=sortKeyFun)
def getSHStock(code,begin="2006-01-31",end="2018-02-20"):
    pairs=getDayPairs(begin,end,1000)
    nlist=[]
    for pair in pairs:
        nlist=nlist+getOneSHStock(code,pair[0],pair[1])
    sortDataList(nlist)
    #print(nlist)
    return nlist

def list2DF(dataList,keys):
    data=[]
    for td in dataList:
        tData=[]
        for key in keys:
            tData.append(td[key])
        data.append(tData)
    df=pd.DataFrame(data, columns=keys) 
    return df
def getStockSavePath(code):
    return savePath+code+".csv"  
  
def saveStockData(code,dataList):
    sortDataList(dataList)
    df=list2DF(dataList,["date","title","url"])
    df.to_csv(getStockSavePath(code),index=False)

def getToday():
    now=datetime.datetime.now()
    nowstr=now.strftime("%Y-%m-%d")
    return nowstr


def getOKStockCode(code):
    code=str(code)
    for i in range(0,6):
        if len(code)<6:
            code="0"+code
    return code

def initStockBasic(useNet=False):
    global stockBasicInfo,myG

    
    if not useNet:
        myG["basicfromcsv"]=True;
        stockBasicInfo=pd.read_csv("stockinfo.csv",index_col="code")
    else:
        myG["basicfromcsv"]=False;
        stockBasicInfo=ts.get_stock_basics()


    #print(stockBasicInfo)
    codes=list(stockBasicInfo.index)
    for i in range(0,len(codes)):
        codes[i]=getOKStockCode(codes[i])
    print(codes)
    myG["codes"]=codes

        
    stockBasicInfo.to_csv("stockinfo.csv",encoding="utf8")

    
def getStockBeginDay(stock):
    global stockBasicInfo
    df = stockBasicInfo
    #print(df)
    if myG["basicfromcsv"]==True:
        stock =int(stock)
    #print(stock)
    date = df.ix[stock]['timeToMarket'] #上市日期YYYYMMDD
    #print(df.ix[stock])
    #print(date)
    print(date,df.ix[stock])
    timeArray = time.strptime(str(date),'%Y%m%d')
    newdate=time.strftime("%Y-%m-%d",timeArray)
    return newdate

codeType={
    "6":"sh",
    "0":"sz",
    "3":"sz"
    }
def getStockType(code):
    return codeType[code[0]]

def getStockNotice(code):
    stockType=getStockType(code)
    if stockType=="sh":
        datas=getSHStock(code,getStockBeginDay(code),getToday())
    elif stockType=="sz":
        datas=getSZStock(code,"2001-01-01",getToday())
    else:
        return None
    saveStockData(code,datas)
    
def beginWork(reverse=False,skipExist=False):
    initStockBasic(False)
    stocks=myG["codes"]
    if reverse==True:
        print("reverse")
        stocks.reverse()
    for stock in stocks:
        try:
            print("work:",stock)
            if skipExist and os.path.exists(getStockSavePath(stock)):
                continue;
            getStockNotice(stock)
        except Exception as err:
            print(err)
            print("fail:",stock)
            time.sleep(5)
        
        
#beginWork()
print(sys.argv)
print(__name__)
if __name__=="__main__" :
    
    print(sys.argv)
    if len(sys.argv)==2:
        workType=sys.argv[1]
        print(workType)
        if workType=="getdataR":
            beginWork(True,True)
        if workType=="getdata":
            beginWork(False,True)
    else:
        #beginWork()
        pass