#!/usr/bin/env python3

import re
import sys
from pathlib import Path
from typing import List, Tuple
import os
import time
import argparse

from m4b_util.helpers import Audiobook

import ebooklib
from ebooklib import epub

from bs4 import BeautifulSoup
from natsort import natsorted

import requests
import json
import base64

from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket
import threading
import signal

########################################################################
# StyleTTS2 Book Generation
########################################################################


def convert_chapter(chapter_path, chapter_paragraphs, voice_url):
    start_time = time.time()
    joined_chapter = '\n'.join(chapter_paragraphs)

    if voice_url:
        result = styletts2(joined_chapter, 17, voice_url)
    else:
        result = styletts2(joined_chapter, 8)

    os.rename(result, chapter_path)
    time_to_finish = round(time.time() - start_time)
    print('Generated chapter in '+str(time_to_finish)+' seconds, using voice: '+voice_url+' ( '+chapter_path+')')

######################################################################
# Ebook Parsing / Handling Code
#  - Modified from : https://github.com/p0n1/epub_to_audiobook
#####################################################################

########################################################################
# Interface for StyleTTS2 server running on local Docker
########################################################################


def styletts2(text, diffusion_steps=8, voice_url=False, embedding_scale=1.2, alpha=0.25, beta=0.6, seed=69):
    url = "http://localhost:5000/predictions"
    data = {
        "input": {
            "text": text,
            "alpha": alpha,
            "beta": beta,
            "diffusion_steps": diffusion_steps,
            "embedding_scale": embedding_scale,
            "seed": seed
        }
    }

    if voice_url:
        data['input']['reference'] = voice_url

    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    output = response.json().get('output', '')

    if output:
        output_data = output.split(',', 1)[-1]
    else:
        print("Something went wrong with gen")
        exit(1)

    with open('temp.mp3', 'wb') as file:
        file.write(base64.b64decode(output_data))

    return 'temp.mp3'

########################################################################
# Serve voice reference file for Docker image to use
########################################################################


def serve_file(filename):
    class FileHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.path = filename
            return super().do_GET()

    httpd = HTTPServer((socket.gethostbyname(socket.gethostname()), 5001), FileHandler)
    ip_address = httpd.server_address[0]
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True

    def shutdown_server(a, b):
        print("Shutting down")
        httpd.shutdown()
        thread.join()
        print("Shutdown.")
        sys.exit(1)
    signal.signal(signal.SIGINT, shutdown_server)

    thread.start()
    return f'http://{ip_address}:{port}/{filename}', shutdown_server


def get_book(input_file):
    return epub.read_epub(input_file, {"ignore_ncx": True})


def get_book_title(book) -> str:
    if book.get_metadata('DC', 'title'):
        return book.get_metadata("DC", "title")[0][0]
    return "Untitled"


def get_book_author(book) -> str:
    if book.get_metadata('DC', 'creator'):
        return book.get_metadata("DC", "creator")[0][0]
    return "Unknown"


def get_chapters(book) -> List[Tuple[str, str]]:
    chapters = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = item.get_content()
        soup = BeautifulSoup(content, features="xml")
        title = soup.title.string if soup.title else ""

        if title == '':
            title = soup.find('h1').text if soup.find('h1') else ''

        #print(title)

        paragraphs = [p.text+' , ' for p in soup.find_all('p')]
        #print(paragraphs)

        if not title:

            title = 'temp'

        title = sanitize_title(title)
        
        chapters.append((title, paragraphs))
        soup.decompose()

    return chapters

def sanitize_title( title ) -> str:
    sanitized_title = re.sub(r"[^\w\s]", "", title, flags=re.UNICODE)
    sanitized_title = re.sub(r"\s+", "_", sanitized_title.strip())
    return sanitized_title

########################################################################
# Code to combine mp3 files to M4b, using https://github.com/Tsubashi/m4b-util
########################################################################

def convert_mp3_to_m4b(folder, book_title, author):

    safe_author = sanitize_title(author)
    safe_title = sanitize_title(book_title)+' - '+safe_author+'.m4b'
  

    book = Audiobook(
        author=author,
        cover="",
        output_name=safe_title,
        title=book_title,
        date="01-12-24",
        keep_temp_files=False,
    )

    sorted_files = natsorted(Path(folder).glob("*.mp3"))

    print(sorted_files)
    book.add_chapters_from_filelist(sorted_files, True, False)
    print("Added chapters")
    book.bind(os.path.join(folder, safe_title))
    print("Bound book")
    if not os.path.exists(os.path.join(folder,'temp_backup')):
        os.makedirs(os.path.join(folder,'temp_backup'))

    # Remove each .mp3 file found to a temp_backup folder
    for mp3_file in sorted_files:
        try:

            os.rename(mp3_file,os.path.join(folder,'temp_backup',mp3_file.name))
            print(f'Moved file: {mp3_file}')
        except OSError as e:
            print(f'Error: {mp3_file} : {e.strerror}')


    print(f"Book '{book_title}' by {author} has been created.")

#########################################################
# Controls the generation process, pass in epub filename
########################################################

def generate_audiobook(epub_filename, voice_type):

    start_time = time.time()
 
    book = get_book(epub_filename)

    title = get_book_title(book)

    safe_title = sanitize_title(title)

    if not os.path.exists(safe_title):
        os.makedirs(safe_title)

    print('Epub Title: '+safe_title)
    
    author = get_book_author(book)
    print('Epub Author: '+author)

    chapters = get_chapters(book)

    chapter_num = 0

    chapter_folders = []

    print('Converting Chapters using StyleTTS 2, via local StyleTTS2 server')

    for chapter in chapters:

        chapter_title = chapter[0]

        if chapter_title != 'temp' and chapter_title != '':

            chapter_num += 1

            #if chapter_num == 3:
            #    break

            safe_chapter_title = sanitize_title(chapter_title)
            chapter_path = safe_title+'/'+str(chapter_num)+' - '+safe_chapter_title+'.mp3'

            if not os.path.exists(chapter_path):
            
                chapter_paragraphs = chapter[1]

                convert_chapter(chapter_path,chapter_paragraphs, voice_type)
   
    print('Chapters done generating, now converting to m4b.')
    
    convert_mp3_to_m4b(safe_title, title, author)
    
    time_to_finish = time.time() - start_time

    print('Book Generated in: '+str(time_to_finish)+' seconds')


def main():

    parser = argparse.ArgumentParser(description='Process arguments.')
    parser.add_argument('filename', help='Epub filename', type=str)
    parser.add_argument('--voice', help='Specify voice type. Leave blank to use LJSpeech (best long-form), or set from the following to use multi-voice: f-us-1, f-us-2, f-us-3, f-us-4, m-us-1, m-us-2, m-us-3, m-us-4', type=str, default='LJSpeech - Longform')
    args = parser.parse_args()
    epub_filename = args.filename
    voice_file = args.voice

    try:
        voice_url, shutdown_server = serve_file(voice_file)
        generate_audiobook(epub_filename, voice_url)
        shutdown_server(True, True)

    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
