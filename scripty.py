from HTMLParser import HTMLParser 
from sys import exit
from base64 import standard_b64decode
import urllib2, re, os, time, threading, Queue

queue = Queue.Queue()
decode_queue = Queue.Queue()

class DownloadTracker():
  """Responsible for managing download calculations"""
  download_success = 0
  def track_downloads(self, file_count):
    self.file_count = file_count
    self.current_download_count = file_count
  def total_downloads(self):
    while True:
      try:
        self.download_count = int(input("How many wallpapers would you like to download? (Must be a multiple of 60): "))
        if self.download_count % 60 == 0:
          break
        else:
          print "Please a multiple of 60."
      except:
        print "Please pick a valid number."
 
class MyHTMLParser(HTMLParser):
  """Checks each href from global page and adds it to decode_queue if it is a wallpaper"""
  def handle_starttag(self, tag, attrs):
    for attr_name, attr_value in attrs:
      if not attr_name == "href": continue
      wallpaper_url = re.search(r"(?<=http://wallbase.cc/)wallpaper/[\d]+", attr_value)
      if wallpaper_url:
        decode_queue.put(attr_value)
        
class TestyClass(HTMLParser):
  """Selects for base64 encoded image from HTML, decodes it, adds it to queue"""
  def handle_data(self, data):
    base64_imgsrc = re.search(r"(?<=(%s))[\S]*(?=%s)" % (re.escape("'+B(\\'"), re.escape("\\')")), (repr(data)))
    if base64_imgsrc:
      queue.put(standard_b64decode(base64_imgsrc.group()))
              
class MyThreadedHTMLParser(threading.Thread, HTMLParser):
  """Passes HTML from URLs in decode_queue to TestyClass"""
  def __init__(self, decode_queue):
    threading.Thread.__init__(self)
    self.decode_queue = decode_queue
  def run(self):
    try: 
      url = self.decode_queue.get(True)
      html = open_url(url)
      if html is not None: 
        parser2 = TestyClass()
        parser2.feed(html)
    except Queue.Empty:
      print "decode_queue.get failed"
    finally:
      self.decode_queue.task_done() 
      
class ThreadDownload(threading.Thread):
  """Download data from the URL in queue"""
  def __init__(self, queue):
    threading.Thread.__init__(self)
    self.queue = queue 
  def run(self):
    try:
      img_url = self.queue.get()
      try:
        img_data = urllib2.urlopen(img_url).read()
        try:
          filename = re.search(r"(wallpaper)[\S]+", str(img_url))
          output = open(str(filename.group()), 'wb')
          output.write(img_data)
          output.close()
         # print "Wallpaper downaloaded to %s!" % (os.path.abspath(filename.group()))
          DownloadTracker.download_success += 1
        except IOError as e:
          print "{} failed to download: {}".format(filename.group(), e.strerror)
      except urllib2.URLError, e:
        if hasattr(e, 'reason'):
          print '\nReason: %s \nURL: %s' % (e.reason, img_url)
        elif hasattr(e, 'code'):
          print '\nReason: %s \nURL: %s' % (e.reason, img_url)
        else:
          print '\nReason: %s \nURL: %s' % (e.reason, img_url)
    except Queue.Empty:
      pass
    finally:
      self.queue.task_done()    
           
def open_url(url):
  """Opens URL and returns html"""
  try:
    response = urllib2.urlopen(url)  
    html = response.read()
    response.close()
    return(html)        
  except urllib2.URLError, e:
    if hasattr(e, 'reason'):
      print '\nReason: %s \nURL: %s' % (e.reason, url)
    elif hasattr(e, 'code'):
      print '\nReason: %s \nURL: %s' % (e.reason, url)
    else:
      print '\nReason: %s \nURL: %s' % (e.reason, url)
    
def mkPicDir(file_path):
  if not os.path.isdir(file_path):
    try:
      os.mkdir(file_path)
    except OSError, e:
      print "Directory could not be created."#, e.errno
      exit() 
      
def main():
  file_path = '.\pics'
  mkPicDir(file_path)
  os.chdir(file_path)
  start_time = time.time()
  dt = DownloadTracker()
  #Count files in ./pics which will be added to current_download_count in order to pick up where the user left off downloading
  files_in_file_path = (len([file for file in os.listdir('.') if os.path.isfile(file)])) 
  dt.track_downloads(files_in_file_path)
  dt.total_downloads()
  while True:
    url = "http://wallbase.cc/toplist/" + str(dt.current_download_count) + "/23/gteq/1920x1080/1.77/110/60/3d"
    parser = MyHTMLParser()
    html = open_url(url)
    if html is None: 
      print "Main() 1st While: html is none"
      continue
    #First page displays 60 images, this will parse for the appropriate hrefs and add them to decode_queue
    parser.feed(html)
    #Until decode_queue is empty perform MyThreadedHTMLParser
    for i in range(decode_queue.qsize()):
      t = MyThreadedHTMLParser(decode_queue)      
      t.start()
    decode_queue.join()
    print "decode_queue joined %.2f" % (time.time() - start_time)
    #thread pool to download 
    for i in range(queue.qsize()):
      td = ThreadDownload(queue)
      td.start()
    queue.join()
    print "queue joined %.2f" % (time.time() - start_time)
    dt.current_download_count += 60
    print "Images downloaded:" + str(dt.download_success)
    print "Images left to download: " + str((int(dt.download_count) + dt.file_count - dt.current_download_count))
    if dt.current_download_count >= (int(dt.download_count) + dt.file_count):
      break
  if not dt.download_success == dt.download_count:
    print "Images to retry, once I put in that feature: " + str(dt.download_count - dt.download_success)
  print "%.2f" % (time.time() - start_time)
main()