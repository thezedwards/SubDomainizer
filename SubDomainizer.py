#!/usr/bin/env python3

#######################################
#    Author: Neeraj Sonaniya          #
#    Twitter: neeraj_sonaniya         #
#    Linkedin: neerajsonaniya         #
#    Facebook: neeraj.sonaniya        #
#    Medium: neerajedwards            #
#    Email: nsonaniya2010@gmail.com   #
#######################################


import termcolor
import base64
import json
import argparse
from bs4 import BeautifulSoup
import requests
import re
import htmlmin
import urllib.parse as urlparse
from urllib.parse import urljoin
from urllib.parse import unquote
import tldextract
import sys
import socket
from multiprocessing.dummy import Pool as ThreadPool
from itertools import repeat
from collections import Counter
from math import log2


parse = argparse.ArgumentParser()
parse.add_argument('-u', '--url', help="Enter the URL in which you want to find (sub)domains.")
parse.add_argument('-l', '--listfile', help="List file which contain list of URLs to be scanned for subdomains")
parse.add_argument('-o', '--output',
                   help="Enter the file name to which you want to save the results of subdomains found.")
parse.add_argument('-c', '--cookie',
                   help="Cookies which needs to be sent with request. User double quotes if have more than one.")
parse.add_argument('-cop', '--cloudop',
                   help="Enter the file name in which you want to save results of cloud services finding.")
parse.add_argument('-d', '--domain', help="Enter the TLD to extract all the subdomain for that TLD.")
parse.add_argument('-gt','--gittoken', help="Finding subdomains from github")
parse.add_argument('-g', '--gitscan', help="Give this option if you wants to search for subdomain from github", action='store_true')


args = parse.parse_args()
url = args.url
listfile = args.listfile
cloudop = args.cloudop
gitToken = args.gittoken
isGit = args.gitscan


if args.cookie:
    heads = {'Cookie': args.cookie,
             'User-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'}
else:
    heads = {'User-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'}


def argerror(urls, listfile):
    if (urls == None and listfile == None) or (urls != None and listfile != None):
        print("Either and atmost one of -u/--url or -l/--listfile argument is required.Exiting...")
        sys.exit(1)
    else:
        pass

def gitArgError(gitToken,isGit):
    if (gitToken == None and isGit != None ) or (gitToken != None and isGit == None):
        print('Either both \'-g\' and \'-gt\' arguments are required or none required. Exiting...')
        sys.exit(1)
    else:
        pass

def getUrlsFromFile():
    with open(args.listfile, 'rt') as f:
        urllst = f.readlines()
    urllst = [x.strip() for x in urllst]
    return urllst


jsLinkList = list()
jsname = list()
finalset = set()
cloudurlset = set()
ipv4list = set()
finallist = list()
secretList = set()

class JsExtract:
    def IntJsExtract(self, url, heads):
        if url.startswith('http'):
            req = requests.get(url, headers=heads)
        else:
            req = requests.get('http://' + url, headers=heads)

        print(termcolor.colored("Searching for Inline Javascripts.....", color='yellow', attrs=['bold']))

        try:
            html = unquote(req.content.decode('unicode-escape'))
            minhtml = htmlmin.minify(html, remove_empty_space=True)
            minhtml = minhtml.replace('\n', '')
            finallist.append(minhtml)
            print(termcolor.colored("Successfully got all the Inline Scripts.", color='blue', attrs=['bold']))
        except UnicodeDecodeError:
            print(termcolor.colored("Decoding error...", color='red', attrs=['bold']))

    def ExtJsExtract(self, url, heads):
        domain = urlparse.urlparse(url).netloc
        print(termcolor.colored("Searching for External Javascript links in page.....", color='yellow', attrs=['bold']))
        if url.startswith('http'):
            req = requests.get(url, headers=heads)
        else:
            req = requests.get('http://' + url, headers=heads)
        try:
            html = unquote(req.content.decode('unicode-escape'))
            soup = BeautifulSoup(html, features='html.parser')

            for link in soup.find_all('script'):
                if link.get('src'):
                    text = urljoin(url, link.get('src'))
                    jsLinkList.append(text)
                    jsLinkList.append(text + link.get('src').strip())
            print(termcolor.colored("Successfully got all the external js links", color='blue', attrs=['bold']))
        except UnicodeDecodeError:
            print("Decoding error, Exiting...")
            sys.exit(1)

    def SaveExtJsContent(self, js):
        try:
            content = unquote(requests.get(js).content.decode('utf-8'))
            finallist.append(content)
        except:
            pass


def logo():
    return """
      _____       _     _____                        _       _              
     / ____|     | |   |  __ \                      (_)     (_)             
    | (___  _   _| |__ | |  | | ___  _ __ ___   __ _ _ _ __  _ _______ _ __ 
     \___ \| | | | '_ \| |  | |/ _ \| '_ ` _ \ / _` | | '_ \| |_  / _ \ '__|
     ____) | |_| | |_) | |__| | (_) | | | | | | (_| | | | | | |/ /  __/ |   
    |_____/ \__,_|_.__/|_____/ \___/|_| |_| |_|\__,_|_|_| |_|_/___\___|_|Version 1.4                                                                                                                                          
Find interesting Subdomains and secrets hidden in page, External Javascripts and GitHub  \n"""

#https://www.reddit.com/r/dailyprogrammer/comments/4fc896/20160418_challenge_263_easy_calculating_shannon/
def entropy(s):
    return -sum(i/len(s) * log2(i/len(s)) for i in Counter(s).values())

def getDomain(url):
    if urlparse.urlparse(url).netloc != '':
        finalset.add(urlparse.urlparse(url).netloc)
    ext = tldextract.extract(str(url))
    return ext.registered_domain

def tldSorting(subdomainList):
    localsortedlist = list()
    finallist = list()
    for item in subdomainList:
        Reverseddomain = ".".join(str(item).split('.')[::-1])
        localsortedlist.append(Reverseddomain)

    sortedlist = sorted(localsortedlist)

    for item in sortedlist:
        reReverseddomain = ".".join(str(item).split('.')[::-1])
        finallist.append(reReverseddomain)

    return finallist

def PreCompiledRegexSecret():
    seclst = ['secret', 'secret_key', 'token', 'secret_token', 'auth_token', 'access_token', 'username', 'password',
              'aws_access_key_id', 'aws_secret_access_key', 'secretkey', 'authtoken', 'accesstoken', 'access-token',
              'authkey', 'client_secret','key','bucket','email','HEROKU_API_KEY','SF_USERNAME','PT_TOKEN','id_dsa',
              'clientsecret', 'client-secret', 'encryption-key', 'pass', 'encryption_key', 'encryptionkey', 'secretkey',
              'secret-key','bearer','JEKYLL_GITHUB_TOKEN','HOMEBREW_GITHUB_API_TOKEN',
              'api_key', 'api_secret_key', 'api-key', 'private_key', 'client_key', 'client_id', 'sshkey', 'ssh_key',
              'ssh-key', 'privatekey','DB_USERNAME','oauth_token','irc_pass', 'dbpasswd','xoxa-2','xoxr'
              'private-key', 'private_key', 'consumer_key', 'consumer_secret', 'access_token_secret', 'SLACK_BOT_TOKEN',
              'slack_api_token', 'api_token', 'ConsumerKey', 'ConsumerSecret', 'SESSION_TOKEN', 'session_key',
              'session_secret', 'slack_token', 'slack_secret_token', 'bot_access_token']
    equals = ['=',':','=>','=:']

    return re.compile(r'(["\']?[\w-]*(?:' + '|'.join(seclst) + ')[\w-]*[\s]*["\']?[\s]*(?:' +'|'.join(equals)  + ')[\s]*["\']?([\w\-/~!@#$%^*+=.]+)["\']?)',
                      re.MULTILINE | re.IGNORECASE)

def PreCompiledRegexCloud():
    # cloud services regex:
    cfreg = re.compile(r'([\w]+\.cloudfront\.net)', re.MULTILINE | re.IGNORECASE)
    gbureg = re.compile(r'([\w\-.]+\.appspot\.com)', re.MULTILINE | re.IGNORECASE)
    s3bucketreg = re.compile(r'([\w\-.]*s3[\w\-.]*\.?amazonaws\.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    doreg = re.compile(r'([\w\-.]*\.?digitaloceanspaces\.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    gsreg1 = re.compile(r'(storage\.cloud\.google\.com/[\w\-.]+)', re.MULTILINE | re.IGNORECASE)
    gsreg2 = re.compile(r'([\w\-.]*\.?storage.googleapis.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    gsreg3 = re.compile(r'([\w\-.]*\.?storage-download.googleapis.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    gsreg4 = re.compile(r'([\w\-.]*\.?content-storage-upload.googleapis.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    gsreg5 = re.compile(r'([\w\-.]*\.?content-storage-download.googleapis.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    azureg1 = re.compile(r'([\w\-.]*\.?1drv\.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    azureg2 = re.compile(r'(onedrive.live.com/[\w.\-]+)', re.MULTILINE | re.IGNORECASE)
    azureg3 = re.compile(r'([\w\-.]*\.?blob\.core\.windows\.net/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    rackcdnreg = re.compile(r'([\w\-.]*\.?rackcdn.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    dreamhostreg1 = re.compile(r'([\w\-.]*\.?objects\.cdn\.dream\.io/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    dreamhostreg2 = re.compile(r'([\w\-.]*\.?objects-us-west-1.dream.io/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    firebase = re.compile(r'([\w\-.]+\.firebaseio\.com)', re.MULTILINE | re.IGNORECASE)

    cloudlist = [cfreg, s3bucketreg, doreg, gsreg1, gsreg2, gsreg3, gsreg4, gsreg5,
                 azureg1, azureg2, azureg3, rackcdnreg, dreamhostreg1, dreamhostreg2, firebase, gbureg]

    return cloudlist

def PreCompiledRegexDomain(url):
    # domain regex
    regex = re.compile(r'([a-zA-Z0-9][a-zA-Z0-9\-.]*[a-zA-Z0-9]\.' + str(getDomain(str(url))) + ')', re.IGNORECASE)
    return regex

def PreCompiledRegexIP():
     # ip finding
    ipv4reg = re.compile('(([2][5][0-5]\.)|([2][0-4][0-9]\.)|([0-1]?[0-9]?[0-9]\.)){3}'
                          + '(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))')
    return ipv4reg

def getSubdomainsfromFile(file, cloudlist, p, regex,ipv4reg, url):

    file = str(file).replace('\n', ' ')
    # cloud services
    for x in cloudlist:
        for item in x.findall(str(file)):
            cloudurlset.add(item)

    matches = p.finditer(str(file))
    for matchNum, match in enumerate(matches):
            if entropy(match.group(2)) > 3.5:
                secretList.add(match.group())

    # try:
    #     st = file.split()
    #     for i in st:
    #         match = ipv4reg.search(i)
    #         if match:
    #             ipv4list.add(match.group())
    # except:
    #     pass


        # for subdomains
    for subdomain in regex.findall(str(file)):
        finalset.add(subdomain)

    # given domain regex
    if args.domain:
        domainreg = re.compile(r'([a-zA-Z0-9][0-9a-zA-Z\-.]*[a-zA-Z0-9]\.' + args.domain + ')', re.IGNORECASE)
        for subdomain in domainreg.findall(str(file)):
            finalset.add(subdomain)


def getUrlsFromData(gitToken, domain):
    data = requests.get('https://api.github.com/search/code?q=' + domain + '&access_token=' + gitToken + '&per_page=100').content.decode('utf-8')
    contentApiURLs = set()
    data = json.loads(data)
    for item in data['items']:
        for key, value in item.items():
            if key == 'url':
                contentApiURLs.add(value)
    return contentApiURLs


def getGithubData(item):
    locallist = list()
    item = item + '&access_token=' + gitToken
    apiUrlContent = requests.get(item).content.decode('utf-8')
    jsonData = json.loads(apiUrlContent)
    data = base64.b64decode(jsonData['content'])
    data = unquote(str(data, 'utf-8'))
    locallist.append(str(data.replace('\n',' ')))
    return locallist

def subextractor(cloudlist, p, regex, ipv4reg, url):
    jsfile = JsExtract()
    jsfile.IntJsExtract(url, heads)
    jsfile.ExtJsExtract(url, heads)
    jsthread = ThreadPool(300)
    jsthread.map(jsfile.SaveExtJsContent, jsLinkList)
    jsthread.close()
    jsthread.join()
    print(termcolor.colored("Finding Subdomains and cloud data of given domain in all Javascript files...",
                            color='yellow',
                            attrs=['bold']))
    threads = ThreadPool(300)
    threads.starmap(getSubdomainsfromFile, zip(finallist, repeat(cloudlist), repeat(p), repeat(regex),repeat(ipv4reg), repeat(url)))
    threads.close()
    threads.join()
    print(termcolor.colored("Searching completed...",color='blue',attrs=['bold']))
    finallist.clear()

def saveandprintdomains():
    print(termcolor.colored("\n~~~~~~~~~~~~~~~~~~~~~~~RESULTS~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n", color='red',
                            attrs=['bold']))
    if cloudurlset:
        print(termcolor.colored("\nSome cloud services url's found. They might be interesting, Here are the URLs:\n",
                                color='blue', attrs=['bold']))
        for item in cloudurlset:
            print(termcolor.colored(item, color='green', attrs=['bold']))
    else:
        print(termcolor.colored("\nNo cloud services url were found.\n", color='red', attrs=['bold']))

    print(termcolor.colored("\nSuccessfully got all the subdomains...\n", color='blue', attrs=['bold']))
    print(termcolor.colored("Total Subdomains: "+str(len(finalset)), color='red', attrs=['bold']))

    for item in tldSorting(finalset):
        print(termcolor.colored(item, color='green', attrs=['bold']))
    if ipv4list:
        print(termcolor.colored("\nGot Some IPv4 addresses:\n", color='blue', attrs=['bold']))
        for ip in ipv4list:
            if socket.getfqdn(ip) != ip:
                print(termcolor.colored(ip + ' - ' + socket.getfqdn(ip), color='green', attrs=['bold']))

    if args.output:
        print(termcolor.colored("\nWriting all the subdomains to given file...\n", color='yellow', attrs=['bold']))
        with open(args.output, 'w+') as f:
            for item in sorted(finalset):
                f.write(item + '\n')
        print(termcolor.colored("\nWriting Done..\n", color='yellow', attrs=['bold']))


def savecloudresults():
    with open(cloudop, 'w+') as f:
        for item in cloudurlset:
            f.write(item + '\n')


def printlogo():
    return termcolor.colored(logo(), color='red', attrs=['bold'])


if __name__ == "__main__":

    domainSet = set()
    compiledRegexCloud = PreCompiledRegexCloud()
    compiledRegexSecretList = PreCompiledRegexSecret()
    compiledRegexIP = PreCompiledRegexIP()

    try:
        print(printlogo())
        argerror(url, listfile)
        if isGit:
            gitArgError(gitToken,isGit)
        if listfile:
            urllist = getUrlsFromFile()
            if urllist:
                for i in urllist:
                    compiledRegexDomain = PreCompiledRegexDomain(i)
                    domainSet.add(str(getDomain(str(i))))
                    print(termcolor.colored("Extracting data from internal and external js for url:", color='blue',
                                            attrs=['bold']))
                    print(termcolor.colored(i, color='red', attrs=['bold']))
                    try:
                        try:
                            subextractor(compiledRegexCloud, compiledRegexSecretList, compiledRegexDomain,compiledRegexIP, i)
                        except requests.exceptions.ConnectionError:
                            print('An error occured while fetching URL, Might be URL is wrong, Please check!')
                    except requests.exceptions.InvalidSchema:
                        print("Invalid Schema Provided!")
                        sys.exit(1)
        else:
            try:
                try:
                    compiledRegexDomain = PreCompiledRegexDomain(url)
                    domainSet.add(str(getDomain(str(url))))
                    subextractor(compiledRegexCloud, compiledRegexSecretList, compiledRegexDomain,compiledRegexIP,url)
                except requests.exceptions.ConnectionError:
                    print(
                        'An error occured while fetching URL, Might be server is down, or domain does not exist, Please check!')
                    sys.exit(1)
            except requests.exceptions.InvalidSchema:
                print("Invalid Schema Provided!")
                sys.exit(1)

        if gitToken and isGit:
            for item in domainSet:
                compiledRegexDomain = PreCompiledRegexDomain(item)
                print(termcolor.colored('Finding Subdomains and secrets from Github..Please wait...', color='yellow',
                                        attrs=['bold']))
                print(termcolor.colored('Searching in github for : '+ termcolor.colored(item,color='green',attrs=['bold']), color='blue', attrs=['bold']))

                gitThread = ThreadPool(200)
                contentApiURLs = getUrlsFromData(gitToken, str(item))
                gitHublist = gitThread.map(getGithubData, contentApiURLs)
                gitContentThread = ThreadPool(200)

                for ghitem in gitHublist:
                    gitContentThread.starmap(getSubdomainsfromFile,zip(ghitem, repeat(compiledRegexCloud), repeat(compiledRegexSecretList), repeat(compiledRegexDomain), repeat(compiledRegexIP), repeat(item)))
                print(termcolor.colored('Completed finding from github...', color='blue',attrs=['bold']))

        print(termcolor.colored("Got all the important data.\n", color='green', attrs=['bold']))

        saveandprintdomains()

        if cloudop:
            print(
                termcolor.colored("\nWriting all the cloud services URL's to given file...", color='blue',
                                  attrs=['bold']))
            savecloudresults()
            print(
                termcolor.colored("\nWritten cloud services URL's in file: ", color='blue',
                                  attrs=['bold']) + cloudop + '\n')
    except KeyboardInterrupt:
        print(termcolor.colored("\nKeyboard Interrupt. Exiting...\n", color='red', attrs=['bold']))
        sys.exit(1)
    except FileNotFoundError:
        print(
            termcolor.colored("\nFile Not found, Please check filename. Exiting...\n", color='yellow', attrs=['bold']))
        sys.exit(1)
    if secretList:
        print(termcolor.colored("\nI have found some secrets for you (might be false positive):\n", color='blue', attrs=['bold']))
        for item in secretList:
            print(termcolor.colored(item, color='green', attrs=['bold']))
    print('\n')
