
import authentication  as auth
from imgurpython import ImgurClient
from prettySleep import pretty_sleep

import praw
import urllib2, re
#import Image
from PIL import Image
import os,sys
import image_slicer
import json
import time
import string

POSTED_HASH = "/home/nickfrosst/crossXparallel/CrossXParallelBot/postedHash.txt"

AGENT_NAME = "CrossXParallel"

TEMP_NAME = "temp.jpg"

TARGET_SUB = "parallelview"
#TARGET_SUB = "reddit_api_test"
SOURCE_SUB = "crossview"

SEARCH_LIMIT = 20

POST_LIMIT = 5

ImgurConfig = {
        'album': "OWRXY",
        'name':  None,
        'title': None,
        'description': None
    }

black_listed_authors = ['chrisleblac79']
    
def flip(image):
    tiles = image_slicer.slice(image, 2, save=False)
    new_im = Image.new('RGB', (tiles[0].image.size[0]*2,tiles[0].image.size[1]))
    new_im.paste(tiles[1].image, (0,0))
    new_im.paste(tiles[0].image, (tiles[0].image.size[0],0))
    new_im.save(TEMP_NAME,"jpeg")

def flickr_download(url, save_name):
    html = urllib2.urlopen(url).read()
    img_url = re.findall(r'http[s]?\:[^" \\:]*_b\.jpg', html)[0]
    with open(save_name, "wb") as fp:
        fp.write(urllib2.urlopen(img_url).read())

def raw_download(url, save_name):
    with open(save_name, "wb") as fp:
        fp.write(urllib2.urlopen(url).read())

posted = json.load(open(POSTED_HASH))

downloaders = [(flickr_download,'.*www\.flickr\.com.*'),
               (raw_download,'.*\.jpg'),
               (raw_download,'.*\.png')]

imgur_client = ImgurClient(auth.client_id, auth.client_secret, auth.access_token, auth.refresh_token)

reddit = praw.Reddit(client_id=auth.reddit_client_id,
                client_secret=auth.reddit_secret,
                user_agent=AGENT_NAME,
                username = auth.reddit_username,
                password = auth.reddit_password)

if not reddit.read_only:
    print("obtained non read only reddit")

subreddit = reddit.subreddit(SOURCE_SUB)

submitted = 0
for submission in subreddit.hot(limit = SEARCH_LIMIT):
    if submitted == POST_LIMIT:
        break
        
    for downloader,patern in downloaders:
        s = str(submission.title.encode("utf-8"))
        if submission.author.name not in black_listed_authors and \
           not posted.has_key(submission.url) and \
           s.lower().find("r/parallelview") == -1 and \
           re.match(patern,submission.url):

            print ("matched " + patern)
            downloader(submission.url, TEMP_NAME)
            
            flip(TEMP_NAME)
            
            
            ImgurConfig['title'] = filter(lambda x: x in string.printable, s)
            print (ImgurConfig['title'])
                
            ImgurConfig['description'] = "parallel view version - original by " + str(submission.author.name) + " - " + str(submission.shortlink) + " - " + str(submission.url)  
            response = imgur_client.upload_from_path(TEMP_NAME, config=ImgurConfig, anon=False)
            
            while True:
                try:
                    print(str(response['link'][:-4]))     
                    print ("posting")
                    title =  s + " [by u/" + str(submission.author.name) + " converted]"
                    reddit_post = reddit.subreddit(TARGET_SUB).submit( title, url=str(response['link'][:-4]))
                    break
                except praw.exceptions.APIException as e:
                    if e.field == 'ratelimit':
                        print(e.message)
                        m = re.search("\d+",e.message)
                        pretty_sleep(60 * int(m.group(0)))
                    else:
                        print(e)
                        raise NameError('GiveUp')
                        
                    
            
            reddit_post.reply('''Hello, I am a bot :) \nI was writtten by nick_ok\n I cross post from r/crossview \n\n ''' + ImgurConfig['description'])        
            print ("adding comment")
            posted[submission.url] = reddit_post.shortlink
            print("submited " + posted[submission.url])
            submitted += 1 
            
            #write hash to disc
            json.dump(posted, open(POSTED_HASH,'w'))
            break
