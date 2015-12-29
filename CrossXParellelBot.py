
import authentication  as auth
from imgurpython import ImgurClient
from prettySleep import pretty_sleep

import praw
import urllib2, re
import Image
import os,sys
import image_slicer
import json
import time

AGENT_NAME = "CrossXParallel"

TEMP_NAME = "temp.jpg"

TARGET_SUB = "parallelview"
#TARGET_SUB = "reddit_api_test"
SOURCE_SUB = "crossview"

SEARCH_LIMIT = 50

POST_LIMIT = 5

ImgurConfig = {
        'album': "OWRXY",
        'name':  None,
        'title': None,
        'description': None
    }
    
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

posted = json.load(open("postedHash.txt"))

downloaders = [(flickr_download,'.*www\.flickr\.com.*'),
               (raw_download,'.*\.jpg'),
               (raw_download,'.*\.png')]

imgur_client = ImgurClient(auth.client_id, auth.client_secret, auth.access_token, auth.refresh_token)

user_agent = (AGENT_NAME)
r = praw.Reddit(user_agent = user_agent)
r.login(auth.reddit_username, auth.reddit_password)

subreddit = r.get_subreddit(SOURCE_SUB)

submitted = 0
for submission in subreddit.get_hot(limit = SEARCH_LIMIT):
    if submitted == POST_LIMIT:
        break
        
    for downloader,patern in downloaders:
        if not posted.has_key(submission.url) and re.match(patern,submission.url):
            print ("matched " + patern)
            downloader(submission.url, TEMP_NAME)
            
            flip(TEMP_NAME)
            
            ImgurConfig['title'] = str(submission.title)
            ImgurConfig['description'] = "parallel view version - original by " + str(submission.author.name) + " - " + str(submission.short_link) + " - " + str(submission.url)  
            response = imgur_client.upload_from_path(TEMP_NAME, config=ImgurConfig, anon=False)
            
            while True:
                try:
                    print(str(response['link'][:-4]))
                    reddit_post = r.submit(TARGET_SUB, "[XPost CrossView] " + str(submission.title) + " by " + str(submission.author.name), url=str(response['link'][:-4]))
                    break
                except:
                    e = sys.exc_info()[0]
                    print(e)
                    pretty_sleep(600)
                    
            
            reddit_post.add_comment('''Hello, I am a bot :) \n\n I cross post from r/crossview \n\n ''' + ImgurConfig['description'])        
                    
            posted[submission.url] = reddit_post.short_link
            print("submited " + posted[submission.url])
            submitted += 1 
            
            #write hash to disc
            json.dump(posted, open("postedHash.txt",'w'))
            break

