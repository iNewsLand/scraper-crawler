import requests
import multiprocessing
import re
import validators

from bs4 import BeautifulSoup

import time

from Models.Article.article import Article
from Models.Feed.feed import Feed

base_url = "https://www.eluniversal.com.mx"

#Simulates our DB
data = {
    "Feeds" : [],
    "News" : [],
}

session = None

def set_global_session():
    global session
    if not session:
        session = requests.Session()

def get_urls():
    page = requests.get(base_url) 
    soup = BeautifulSoup(page.content, 'html.parser')
    #Find main menu that contains all the sections of articles
    news_menu = soup.find(id="menu-navegacion_Noticias")
    #Fetch tags and its urls
    tags = [e.string for e in news_menu.find_all("a")]
    urls = [base_url + e["href"] for e in news_menu.find_all("a", href=True)]
    return urls

"""
get_attributes_article gathers a whole article from a feed
There are some custom tag in some articles
Example :
tag : h2 with class : h1
"""
def get_attributes_article(article):
    header_article = r"(Encabezado-Articulo|ceh-InteriorVideoCamara)"
    reg_title = r"h1"
    reg_subtitle = r"h2"
    reg_date = r".+DatosArticulo_ElementoFecha"
    reg_time = r".+DatosArticulo_ElementoMetaHora"
    reg_author = r".+DatosArticulo_autor"
    reg_image = r".+ImagenArticulo"
    reg_div_content = r".+7nota"
    classes_content = "field field-name-body field-type-text-with-summary field-label-hidden"

    div_content = article.find("div", re.compile(reg_div_content))
    if div_content != None:
        content = div_content.find("div", {"class": classes_content }).text
    else:
        return None
    div_header = article.find("div", re.compile(header_article))
    title = div_header.find(["h1","h2"],re.compile(reg_title))
    if div_header.find("h2", re.compile(reg_subtitle)):
        subtitle = div_header.find("h2", re.compile(reg_subtitle)).text.rstrip("\n")
    else:
        subtitle = None
    date = div_header.find("span", re.compile(reg_date))
    time = div_header.find("span", re.compile(reg_time))
    authors_tags = div_header.find_all("span", re.compile(reg_author))
    authors = [" ".join(e.text.split()) for e in authors_tags]

    if div_header.find("figure", re.compile(reg_image)):
        image_content = div_header.find("figure", re.compile(reg_image))
        image = image_content.find("img")
        image = image["src"]
    else:
        image = None
    
    new_article =  Article(title.text.rstrip("\n"), subtitle, image, content, authors, date.text.rstrip("\n"), " ".join(time.text.split()))
    print(new_article)
    return new_article

"""
get_attributes_feed gathers all the attributes of one feed, 
there are some conditions to be a valid feed. It must contain : 
* Valid URL
* Title
"""
def get_attributes_feed(feed):
    title_reg_exp = r'.+_Titulo'
    date_reg_exp = r'.+_Hora'
    img_reg_exp = r'.+_Imagen'
    content_reg_exp = r'.+(_Resumen|_Nota)'
    url = feed.find('a', href=True)["href"]
    if not validators.url(url):
        return None 
    
    img = feed.find('img', re.compile(img_reg_exp))
    if img == None:
        img = ""
    else:
        img = img["src"]

    if feed.find(class_=re.compile(title_reg_exp)) == None:
        print(feed)
        return
    title = feed.find(class_=re.compile(title_reg_exp)).text
    title = " ".join(title.split())

    date = feed.find('span', re.compile(date_reg_exp))  
    if date == None:
        date = "00:00"
    else:
        date = date.text.rstrip("\n")
  
    if feed.find("p", re.compile(content_reg_exp)) == None:
        content = ""
    else:
        content = feed.find("p", re.compile(content_reg_exp)).text
    new_feed = Feed(title,img,content,date,url)
    print(new_feed)
    return new_feed

#parse_page_articles receives a feed's URL and returns an article
def parse_page_articles(url):
    page = requests.get(url)
    if page.status_code == requests.codes.ok:
        bs = BeautifulSoup(page.content, "html.parser")
        article = get_attributes_article(bs)
        return article

def parse_feeds(url):
    with session.get(url) as response :
        bs = BeautifulSoup(response.content, "html.parser")
        articles = [e for e in bs.find_all(["div", "a"], "type-article")]
        for e in articles:
            feed = get_attributes_feed(e)
            if feed != None:
                article = parse_page_articles(feed.get_url())

def download_all_sites(urls):
    with multiprocessing.Pool(initializer=set_global_session) as pool:
        pool.map(parse_feeds, urls)

if __name__ == "__main__":
    start_time = time.time()
    download_all_sites(get_urls())
    duration = time.time() - start_time
    print(f"Downloaded  {duration} seconds")