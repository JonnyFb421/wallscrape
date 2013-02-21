from HTMLParser import HTMLParser 
import urllib2, re, base64, os, time, threading, Queue

queue = Queue.Queue()
decode_queue = Queue.Queue()
img_src = []

class MyHTMLParser(HTMLParser):  
  def handle_starttag(self, tag, attrs):
    for attr_name, attr_value in attrs:
      if not attr_name == "href":
        continue
      wallpaper_url = re.search(r"(?<=http://wallbase.cc/)wallpaper/[\d]+", attr_value)
      if wallpaper_url:
        decode_queue.put(attr_value)
        
class TestyClass(HTMLParser):
  def handle_data(self, data):
    base64_imgsrc = re.search(r"(?<=(%s))[\S]*(?=%s)" % (re.escape("'+B(\\'"), re.escape("\\')")), (repr(data)))
    if base64_imgsrc:
      img_src.append(base64.standard_b64decode(base64_imgsrc.group()))
              
class MyThreadedHTMLParser(threading.Thread, HTMLParser):
  """Decode base64 image and adds the resulting complete URL to list: img_src"""
  def __init__(self, decode_queue):
    threading.Thread.__init__(self)
    self.decode_queue = decode_queue
  def run(self):
    while True:
      foobar = self.decode_queue.get()
      html = open_url(foobar)
      parser2 = TestyClass()
      parser2.feed(html)
      print
      print foobar
      print
      self.decode_queue.task_done()   
      
class ThreadDownload(threading.Thread):
  """Threaded Download Attempt"""
  def __init__(self, queue):
    threading.Thread.__init__(self)
    self.queue = queue 
  def run(self):
    while True:
      try:
        img_url = self.queue.get()
        img_data = urllib2.urlopen(img_url).read()
        try:
          filename = re.search(r"(wallpaper)[\S]+", str(img_url))
          output = open(str(filename.group()), 'wb')
          output.write(img_data)
          output.close()
          print "Image has been succesfully downaloaded to %s!" % (os.path.abspath(filename.group()))
          self.queue.task_done()
        except IOError as e:
          print "{} failed to download: {}".format(filename.group(), e.strerror)
      except urllib2.HTTPError, e:
        print('HTTPError = ' + str(e.code))
      except urllib2.URLError, e:
        print('URLError = ' + str(e.reason))
      except httplib.HTTPException, e:
        print('HTTPException')
             
def open_url(url):
  """Opens URL and returns html"""
  request = urllib2.Request(url)
  response = urllib2.urlopen(request)
  link = response.geturl()
  html = response.read()
  response.close()
  return html
    
def main():
  download_location = '.\pics'
  os.chdir(download_location)
  while True:
    try:
      download_count = int(input("How many wallpapers would you like to download? (Must be a multiple of 60): "))
    except:
      print "Please pick a valid number."
    start_time = time.time()
    file_count = len([file for file in os.listdir('.') if os.path.isfile(file)])
    current_download_count = file_count
    while True:
      url = "http://wallbase.cc/toplist/" + str(current_download_count) + "/23/eqeq/0x0/0/110/60/0"
      parser = MyHTMLParser()
      html = open_url(url)
      parser.feed(html)
      #Request and retrieve image source
      for i in range(10):
        t = MyThreadedHTMLParser(decode_queue)
        t.setDaemon(True)
        t.start()
      decode_queue.join()
      for img in img_src:
        queue.put(img)
      #download
      for i in range(10):
        td = ThreadDownload(queue)
        td.setDaemon(True)
        td.start()
      queue.join()
      current_download_count += 60
      if not current_download_count > (int(download_count) + file_count): continue
      else: break
    break
  print "%.2f" % (time.time() - start_time)
main()