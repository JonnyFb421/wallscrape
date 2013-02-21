from bs4 import BeautifulSoup
from HTMLParser import HTMLParser 
import urllib2, re, base64, os

class MyHTMLParser(HTMLParser):
  wall_src = []
  
  def handle_starttag(self, tag, attrs):
 #   print "Encountered a start tag:", attrs
    for attr_name, attr_value in attrs:
      #This was used to select the thumbnail ID to construct the URL to get to the page containing the img src. 
      #I'm an idiot and wasted time doing this when I should have been grabbing the href to begin with. fuck.
      #foobar = re.search(r"(?<=thumb)([\d]+)", attr_value)
      if not attr_name == "href":
        continue
      wallpaper_url = re.match(r"http://wallbase.cc/wallpaper/[\d]+", attr_value)
      if wallpaper_url:
        self.wall_src.append(attr_value)
 
class MyOtherHTMLParser(MyHTMLParser):  
  img_src = []
  
  def handle_data(self, data):
  ###FIX THIS. SHIT WILL GO SLOW UNTIL I FIGURE OUT HOW TO ONLY SELECT THE JAVASCRIPT###
  #  print "Handling data"
    base64_imgsrc = re.search(r"(?<=(%s))[\S]*(?=%s)" % (re.escape("'+B(\\'"), re.escape("\\')")), (repr(data)))
    if base64_imgsrc:
      self.img_src.append(base64.standard_b64decode(base64_imgsrc.group()))
      
def open_url(url):
  """Opens URL and returns html"""
  request = urllib2.Request(url)
  response = urllib2.urlopen(request)
  link = response.geturl()
  html = response.read()
  response.close()
  return html
  
def download_images(img_src):
  """Traverses through img_src list for the URLs and downloads the images."""
  for img in img_src:
    img_data = urllib2.urlopen(img).read()       
    try:
        filename = img.split('/')[-1]
        output = open(filename, 'wb')
        output.write(img_data)
        output.close()
        print "Image has been succesfully downaloaded to %s!" % (os.path.abspath(filename))
    except IOError as e:
        print "{} failed to download: {}".format(filename, e.strerror)

download_location = './pics'
os.chdir(download_location)
url = "http://wallbase.cc/toplist/0/23/eqeq/0x0/0/110/32/0"
parser = MyHTMLParser()
parser2 = MyOtherHTMLParser()
html = open_url(url)
parser.feed(html)
#parser.feed(page)
#parser.feed(soup.find_all('a'))
#parser.feed('<div class="thumb" id="thumb111111" tags="sunset|7932|0||trees|8188|0||scenic|13485|0">'
#            '<div class="thumb" id="thumb222222222" tags="sunset|7932|0||trees|8188|0||scenic|13485|0">'
#            '<div class="thumb" id="thumb333" tags="sunset|7932|0||trees|8188|0||scenic|13485|0">'
#            '<a href="http://wallbase.cc/wallpaper/2164920" id="drg_thumb2164920" class="thdraggable thlink" target="_blank"><img src="http://ns3002439.ovh.net/thumbs/manga-anime/thumb-2164920.jpg" style="width:250px;height:188px"></a>'
#           )
#parser.feed('<script type="text/javascript">document.write(\'<img alt="sunset trees scenic  / 1920x1080 Wallpaper" src="\'+B(\'aHR0cDovL25zMjIzNTA2Lm92aC5uZXQvbWFuZ2EtYW5pbWUvMjYyZmQwYjM2OWIwY2EwZDQxYjYzZjFhMjVhZjNjMzUvd2FsbHBhcGVyLTIxNjQ5MjAuanBn\')+\'" />\');</script>')

#parser.x = document.write('<img alt="sunset trees scenic  / 1920x1080 Wallpaper" src="'+B('aHR0cDovL25zMjIzNTA2Lm92aC5uZXQvbWFuZ2EtYW5pbWUvMjYyZmQwYjM2OWIwY2EwZDQxYjYzZjFhMjVhZjNjMzUvd2FsbHBhcGVyLTIxNjQ5MjAuanBn')+'" />');
#match_object = re.search(r"(?<=(%s))[\S]*(?=%s)" % (re.escape("'+B(\\'"), re.escape("\\')")), (repr(parser.x)))
#if not match_object.group():
#  print "Something terrible happened while extracting the image source from the base64 blah blah blah"

for foo in parser.wall_src:
  html = open_url(foo)
  parser2.feed(html)
  
download_images(parser2.img_src)