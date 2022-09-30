#!/usr/bin/env python

import sys
import os
import glob
import requests
from time import sleep


if len(sys.argv) < 2:
    print 'please specify downloadlist'
    sys.exit(1)
listfile = sys.argv[1]

with open(listfile,'r') as f:
    urls = f.readlines()
    
    
# hasn't been run
if len(urls[0].split()) == 1:
    urls = ['N '+u.strip() for u in urls]
    
urlsdone = []
urlstodo = []
for u in urls:
    C = u.split()
    if C[0].upper() == 'N':
        urlstodo.append(C[1].strip())
    elif C[0].upper() == 'U':
        urlsdone.append(C[1].strip())
    else:
        print('something is strange here',u)
        
print(len(urlsdone),' urls done')
print(len(urlstodo),' urls to do')

workdir='.'

filestodo = [u.split('/')[-1] for u in urlstodo]

s = requests.Session()

s.auth = ('user', 'pass')

for f,u in zip(filestodo,urlstodo):
    if os.path.isfile(workdir+'/'+f):
        print 'File',f,'already exists, skipping'
    else:
        print 'Downloading',f
        url=u
        print url
        filename=workdir+'/'+f
        downloaded=False
        while not downloaded:
            connected=False
            while not connected:
                try:
                    print 'Opening connection'
                    response = s.get(url, stream=True,verify=False,timeout=60)
                    if response.status_code!=200:
                        print response.headers
                        raise RuntimeError('Code was %i' % response.status_code)
                    esize=long(response.headers['Content-Length'])
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
                    print 'Connection error! sleeping 30 seconds before retry...'
                    sleep(30)
                else:
                    connected=True
            try:
                print 'Downloading'
                with open(filename, 'wb') as fd:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            fd.write(chunk)
                fsize=os.path.getsize(filename)
                if esize!=fsize:
                    print 'Download incomplete (expected %i, got %i)! Retrying' % (esize, fsize)
                else:
                    print 'Download successful'
                    downloaded=True
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
                print 'Connection error! sleeping 30 seconds before retry...'
                sleep(30) # back to the connection
                



with open(listfile,'w') as f:
    for u in urlsdone:
        f.write('Y '+u+'\n')
    for u in urlstodo:
        f.write('N '+u+'\n')
        
        
