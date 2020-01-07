import requests
import bs4
import pandas as pd
import time
import re
from lxml import html  
import nltk, string
from sklearn.feature_extraction.text import TfidfVectorizer
from langdetect import detect

# ----------------Your Profile in differente Language--------
ge_profile_path=r"my GE profile.txt"  # Your GERMANY profile or CV as text file (.txt)
en_profile_path=r'my EN profile.txt' # Your ENGLISH profile or CV as text file (.txt)
fr_profile_path=r'my FR profile.txt' # Your FRENCH profile or CV as text file (.txt)

ge_profile=open(ge_profile_path,'r')
en_profile=open(en_profile_path,'r')
fr_profile=open(en_profile_path,'r')
ge_text_peofile=ge_profile.read()
en_text_peofile=en_profile.read()
fr_text_peofile=en_profile.read()
#----------------------------------------------
print('')
print("       insert your Linkedin Search link wich is test in real Linedin Website like:")
print("       https://www.linkedin.com/jobs/search/?geoId=103883259&keywords=data%20scientist&location=Austria")
search_path=input("       Your Link:  ")
# NLTK to find the correlation between two jobs ---------------------------
nltk.download('punkt') # if necessary...

stemmer = nltk.stem.porter.PorterStemmer()
remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)

def stem_tokens(tokens):
    return [stemmer.stem(item) for item in tokens]

'''remove punctuation, lowercase, stem'''
def normalize(text):
    return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))

vectorizer = TfidfVectorizer(tokenizer=normalize)

def cosine_sim(text1, text2):
    tfidf = vectorizer.fit_transform([text1, text2])
    return ((tfidf * tfidf.T).A)[0,1]
#-----------------------------------------------------------------------
df=[]

text=[['Link','Job Description', 'Correlation']]

text=pd.DataFrame(text)

Position_info=[]

page=requests.get(search_path)
soup=bs4.BeautifulSoup(page.content,features="lxml")

total_result=soup.find("span",{"class":"results-context-header__job-count"})
total_result=int(total_result.text)
for j in range(int(total_result/25)+1):
    
    page=requests.get(search_path+"&start="+str(j))
    soup=bs4.BeautifulSoup(page.content,features="lxml")
    for link in soup.findAll('a'):
        le=link.get('href')
#        le=pd.DataFrame(le)
        df.append(le)
df=pd.DataFrame(df)
df.drop_duplicates(inplace=True)
df['job_link']=df.loc[:,0].str.contains('/jobs/view')
#df['job_link']=df.loc[:,0].str.contains('/land/ad/')
dff=df[df.job_link == True]
dff.reset_index(inplace=True)
dff.drop('index',axis=1,inplace=True)

redundancy_character=['</em>','</p>','<p>','<em>','<trong>','</li>','<li>','<div class="description__text description__text--rich">',
                      '</ul>','<ul>','<u>','</u>','</div>', '<br>','</br>','<br/>','<br/>']  
for i in range(len(dff)):
    sub_page=requests.get(dff.loc[i,0])
    if (i%25 ==0):  # to avoid the detection of this code as hacker
        time.sleep(1)
    sub_soup=bs4.BeautifulSoup(sub_page.content,features="lxml")
    text1=sub_soup.findAll("div", {"class": "description__text description__text--rich"})
    text2=re.sub(r'/s+','',str(text1))
    for u in redundancy_character :
        text2=text2.replace(u,'')
    language=detect(text2)
    if language=='de':
        profile=ge_text_peofile
    elif language=='en':
        profile=ge_text_peofile
    elif language=='fr':
        profile=fr_text_peofile
    correlation=cosine_sim(text2,profile)
    Position_info=[dff.loc[i,0],text2, correlation]
    Position_info=pd.DataFrame(Position_info)
    Position_info=Position_info.T
    text=text.append(Position_info)

text.columns=text.iloc[0,:]
text.reset_index(inplace=True)

text=text.dropna(axis=0, how='any',inplace=True)
text=text.drop_duplicates(subset='Job Description',inplace=True)
writer = pd.ExcelWriter('linkedin.xlsx')   
text.to_excel(writer,'Job result description')

writer.save()

