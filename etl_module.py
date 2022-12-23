# Importing Packages
import time
import json
import spacy
import boto3
import re
import hashlib
import pyaes, pbkdf2, binascii, os, secrets

from tweepy.streaming import Stream
from tweepy import OAuthHandler
from tweepy import Stream
from kafka import KafkaProducer
from nltk.corpus import stopwords
from textblob import TextBlob
from cleantext import clean

stop_words = set(stopwords.words('english'))


# Loading the spacy model
NER = spacy.load("en_core_web_sm")

# Entity groups to be masked
conf_corpus = ['ORG', 'GPE', 'PERSON']

# Twitter developer account credentials
access_token = 'ENTER YOUR TWITTER ACCESS TOKEN'
access_secret = 'ENTER YOUR TWITTER ACCESS SECRET'
consumer_key = 'ENTER YOUR TWITTER CONSUMER KEY'
consumer_secret = 'ENTER YOUR TWITTER CONSUMER SECRET'

# Creating Boto3 client
client = boto3.client('s3', aws_access_key_id='ENTER YOUR AWS ACCESS KEY ID', aws_secret_access_key='ENTER YOUR AWS SECRET ACCESS KEY')


# Function to perform hashing and encryption
def security_module(raw_tweet_text):    
    
    # Preprocessing - handling quotes and emojis
    tweet_text = raw_tweet_text.replace('"', '\\"')
    tweet_text = clean(tweet_text, no_emoji=True)
    
    # Hashing the user handle using SHA-256
    lines = tweet_text.split('\n')

    handle_masked_tweet = ""

    for line in lines:
        for word in line.split():
            if('@' in word):
                handle_masked_tweet += hashlib.sha256(word.encode()).hexdigest() + ' '
            else:
                handle_masked_tweet += word + ' '
        handle_masked_tweet += '\n'

    hashed_tweet_text = handle_masked_tweet.rstrip()
    
    
    # Identifying the confidential entities and hashing them using SHA-256
    conf_extracted = []
    text1= NER(tweet_text)
    for word in text1.ents:
        if word.label_ in conf_corpus:
            conf_extracted.append(word.text)

    for conf_word in conf_extracted:
        hashed_tweet_text = hashed_tweet_text.replace(conf_word, hashlib.sha256(conf_word.encode()).hexdigest())
        
    # Defining the AES encryption key
    password = "hashed_encrypted_key"
    passwordSalt = os.urandom(16)
    key = pbkdf2.PBKDF2(password, passwordSalt).read(32)
    
    # Performing AES-256 encryption
    iv = secrets.randbits(256)
    aes = pyaes.AESModeOfOperationCTR(key, pyaes.Counter(iv))
    ciphertext = aes.encrypt(hashed_tweet_text)

    return binascii.hexlify(ciphertext)


# Function to perform Sentiment Analysis on extracted tweets
def sentiment_classifier(tweet):
    # Preprocessing
    tweet = tweet.lower()
    tweet = re.sub("\s+"," ", tweet)
    tweet = re.sub("\W"," ", tweet)
    tweet = re.sub(r"http\S+", "", tweet)
    tweet = ' '.join(word.lower() for word in tweet.split() if word not in stop_words and len(word) > 3)
    tweet = re.sub(r'\b\w{1,3}\b', '', tweet)
    
    res = TextBlob(tweet)
    sentiment = res.sentiment.polarity
    if sentiment > 0:
        return 'positive'
    elif sentiment < 0:
        return'negative'
    return 'neutral'


class StdOutListener(Stream):
    def __init__(self, *args):
        super().__init__(*args)
        
    def on_data(self, data):
        json_ = json.loads(data) 
        if not json_:
            return
        
        # Parsing the tweet and writing to s3 bucket
        if "extended_tweet" in json_:            
            raw_tweet_text = json_['extended_tweet']['full_text']
        else:
            raw_tweet_text = json_['text']
            
            msg = security_module(raw_tweet_text)
            sentiment = sentiment_classifier(raw_tweet_text)
            json_str = {'msg' : raw_tweet_text, 'senti' : sentiment}
            producer.send("team-17", json.dumps(json_str).encode('utf-8'))
            
            timestr = time.strftime("%Y%m%d-%H%M%S")
            file_name = 'encrypted_tweets/team17/'+timestr
            response = client.put_object( 
                Bucket='ENTER YOUR BUCKET NAME',
                Body=msg,
                Key=file_name,
                ContentType='text'
            )
            print(msg)
        
        return True
    
    
    def on_error(self, status):
        print (status)
        

if __name__ == "__main__":        
    producer = KafkaProducer(bootstrap_servers='127.0.0.1:9092')
    l = StdOutListener(consumer_key, consumer_secret, access_token, access_secret)
    l.filter(track='layoff', languages=["en"])
