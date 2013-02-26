from HTMLParser import HTMLParser 
from sys import exit
from base64 import standard_b64decode
import urllib2, re, os, time, threading, Queue, logging

LOG_FILENAME = 'scripty.out'
logging.basicConfig(filename=LOG_FILENAME,
                    filemode='w',
                    level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )

queue = Queue.Queue()
decode_queue = Queue.Queue()

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
      except:
        print "Please pick a valid number."
 
class MyHTMLParser(HTMLParser):  
  def handle_starttag(self, tag, attrs):
    for attr_name, attr_value in attrs:
      if not attr_name == "href": continue
      wallpaper_url = re.search(r"(?<=http://wallbase.cc/)wallpaper/[\d]+", attr_value)
      if wallpaper_url:
        decode_queue.put(attr_value)
        
class TestyClass(HTMLParser):
  def handle_data(self, data):
    base64_imgsrc = re.search(r"(?<=(%s))[\S]*(?=%s)" % (re.escape("'+B(\\'"), re.escape("\\')")), (repr(data)))
    if base64_imgsrc:
      queue.put(standard_b64decode(base64_imgsrc.group()))
              
class MyThreadedHTMLParser(threading.Thread, HTMLParser):
  """Decode base64 image and adds the resulting complete URL to queue"""
  def __init__(self, decode_queue):
    threading.Thread.__init__(self)
    self.decode_queue = decode_queue
  def run(self):
    url = self.decode_queue.get()
    html = open_url(url)
    if html is None: 
      self.decode_queue.task_done()
    else:
      parser2 = TestyClass()
      parser2.feed(html)
      self.decode_queue.task_done() 
    
class ThreadDownload(threading.Thread):
  """Threaded Download Attempt"""
  def __init__(self, queue):
    threading.Thread.__init__(self)
    self.queue = queue 
  def run(self):
    img_url = self.queue.get()
    try:
      img_data = urllib2.urlopen(img_url).read()
      try:
        filename = re.search(r"(wallpaper)[\S]+", str(img_url))
        output = open(str(filename.group()), 'wb')
        output.write(img_data)
        output.close()
       # print "Wallpaper downaloaded to %s!" % (os.path.abspath(filename.group()))
        DownloadCounter.download_success += 1
        self.queue.task_done()
      except IOError as e:
        print "{} failed to download: {}".format(filename.group(), e.strerror)
    except urllib2.URLError, e:
      if hasattr(e, 'reason'):
        logging.debug('failed to reach a server.')
        logging.debug('Reason: %s', e.reason)
        self.queue.task_done()
        return None
      elif hasattr(e, 'code'):
        logging.debug('The serverr couldn\'t fulfill the request.')
        logging.debug('Code: %s', e.reason)
        self.queue.task_done()
        return None
      else:
        logging.debug('Shit fucked up1')
        return None
           
def open_url(url):
  """Opens URL and returns html"""
  request = urllib2.Request(url)
  try:
    response = urllib2.urlopen(request)
    link = response.geturl()
    html = response.read()
    response.close()
    return(html)
  except urllib2.URLError, e:
    if hasattr(e, 'reason'):
      logging.debug('failed to reach a serverrr.')
      logging.debug('Reason: %s', e.reason)
      logging.debug(url)
      return None
    elif hasattr(e, 'code'):
      logging.debug('The serverrrr couldn\'t fulfill the request.')
      logging.debug('Code: %s', e.reason)
      return None
    else:
      logging.debug('Shit fucked up2')
      return None    
    
def mkPicDir(file_path):
  if not os.path.isdir(file_path):
    try:
      print "sleeping"
      os.mkdir(file_path)
    except OSError, e:
      print "Directory could not be created."#, e.errno
      exit() 
      
def main():
  file_path = '.\pics'
  mkPicDir(file_path)
  os.chdir(file_path)
  start_time = time.time()
  download_counter = DownloadCounter()
  files_in_file_path = (len([file for file in os.listdir('.') if os.path.isfile(file)]))
  download_counter.track_downloads(files_in_file_path)
  download_counter.total_downloads()
  while True:
    url = "http://wallbase.cc/toplist/" + str(download_counter.current_download_count) + "/23/gteq/1920x1080/0/110/60/0"
    parser = MyHTMLParser()
    html = open_url(url)
    if html is None: 
      print "ABRA KADABRA"
      continue
    parser.feed(html)
    #thread pool to decode and retrieve image source 
    for i in range(60):
      t = MyThreadedHTMLParser(decode_queue)
     # t.setDaemon(True)
      t.start()
    decode_queue.join()
    print "decode_queue joined %.2f" % (time.time() - start_time)
    #thread pool to download 
    for i in range(60):
      td = ThreadDownload(queue)
      #td.setDaemon(True)
      td.start()
    queue.join()
    print "queue joined %.2f" % (time.time() - start_time)
    download_counter.current_download_count += 60
    if threading.active_count() >= 150:
      main_thread = threading.currentThread()
      for thread in threading.enumerate():
        if thread is not main_thread:
          print "Joining :", thread.getName() + " %.2f" % (time.time() - start_time)
          thread.join(2)
    print "download_counter.current_download_count: " + str(download_counter.current_download_count - (int(download_counter.download_count) + download_counter.file_count))
    if download_counter.current_download_count >= (int(download_counter.download_count) + download_counter.file_count):
      print "Breaking out: " + str(threading.active_count())
      main_thread = threading.currentThread()
      for thread in threading.enumerate():
        print thread.getName()
        if thread is main_thread: continue
        print "Joining2 :", thread.getName() + " %.2f" % (time.time() - start_time)
        while thread.isAlive():
          print "still alive"
          thread.join(2)      
        print threading.active_count()
      break
  print threading.active_count()
  print "%.2f" % (time.time() - start_time)
main()