from HTMLParser import HTMLParser 
import urllib2, re, base64, os, time, threading, Queue

queue = Queue.Queue()
decode_queue = Queue.Queue()
img_src = []

class DownloadCounter():
  download_success = 0
  def track_downloads(self, file_count):
    self.file_count = file_count
    self.current_download_count = file_count
    #self.download_success = 0
  def total_downloads(self):
    while True:
      try:
        self.download_count = int(input("How many wallpapers would you like to download? (Must be a multiple of 60): "))
        if self.download_count % 60 == 0: break
        else:
          print "Please a multiple of 60."
          continue
      except:
        print "Please pick a valid number."
 
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
  #  if len(data) >= 150: 
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
          print "Wallpaper downaloaded to %s!" % (os.path.abspath(filename.group()))
          self.queue.task_done()
          DownloadCounter.download_success += 1
        except IOError as e:
          print "{} failed to download: {}".format(filename.group(), e.strerror)
      except urllib2.HTTPError, e:
        self.queue.task_done()
#        print('HTTPError = ' + str(e.code))
      except urllib2.URLError, e:
        self.queue.task_done()
 #       print('URLError = ' + str(e.reason))
             
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
  start_time = time.time()
  download_counter = DownloadCounter()
  footar = (len([file for file in os.listdir('.') if os.path.isfile(file)]))
  download_counter.track_downloads(footar)
  download_counter.total_downloads()
  while True:
    url = "http://wallbase.cc/toplist/" + str(download_counter.current_download_count) + "/23/gteq/1920x1080/0/110/60/0"
    parser = MyHTMLParser()
    html = open_url(url)
    parser.feed(html)
    #thread pool to decode and retrieve img_src
    for i in range(60):
      t = MyThreadedHTMLParser(decode_queue)
      t.setDaemon(True)
      t.start()
      decode_queue.join()
      for img in img_src:
        queue.put(img)
      #thread pool to download 
      for i in range(60):
        td = ThreadDownload(queue)
        td.setDaemon(True)
        td.start()
      queue.join()
      download_counter.current_download_count += 60
      break
    if download_counter.current_download_count >= (int(download_counter.download_count) + download_counter.file_count): break
  print "%.2f" % (time.time() - start_time)
main()