#!/usr/bin/env python3

import re
from typing import List, Tuple
import os
import time
import argparse

from m4b_util.helpers import Audiobook
from pathlib import Path

from gradio_client import Client

import ebooklib
from ebooklib import epub

from bs4 import BeautifulSoup
from natsort import natsorted

########################################################################
# Configure these before running
#######################################################################

spaces_api_url = 'https://xxxxxxxxxxxxxxxxxxxxxx'

hf_token = 'hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx'

style_voice = 'f-us-2' # [f-us-1, f-us-2, f-us-3, f-us-4, m-us-1, m-us-2, m-us-3, m-us-4]

########################################################################
# StyleTTS2 Code, running on HF Spaces
########################################################################

def convert_chapter(client,chapter_path, chapter_paragraphs):

    start_time = time.time()

    joined_chapter = '\n'.join(chapter_paragraphs)

    result = client.predict(
            joined_chapter,    
            style_voice,
            3,    # float (numeric value between 3 and 15) in 'Diffusion Steps' Slider component
            api_name="/synthesize"
    )

    os.rename(result, chapter_path)

    time_to_finish = time.time() - start_time

    print('Chapter Finished in '+str(time_to_finish)+' seconds. ( '+chapter_path+')')

######################################################################
# Ebook Parsing / Handling Code
#  - Modified from : https://github.com/p0n1/epub_to_audiobook
#####################################################################

def get_book(input_file):
    return epub.read_epub(input_file)

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
# Code to combine wav files to M4b, using https://github.com/Tsubashi/m4b-util
########################################################################

def convert_wav_to_m4b(folder, book_title, author):

    safe_author = sanitize_title(author)
    safe_title = sanitize_title(book_title)+' - '+safe_author+'.m4b'
  

    book = Audiobook(
        author=author,
        cover="",
        output_name=safe_title,
        title=book_title,
        date="01-04-24",
        keep_temp_files=False,
    )

    sorted_files = natsorted(Path(folder).glob("*.wav"))

    book.add_chapters_from_filelist(sorted_files, True, False)
    book.bind(os.path.join(folder,safe_title))

    if not os.path.exists(os.path.join(folder,'temp_backup')):
        os.makedirs(os.path.join(folder,'temp_backup'))

    # Remove each .wav file found to a temp_backup folder
    for wav_file in sorted_files:
        try:

            os.rename(wav_file,os.path.join(folder,'temp_backup',wav_file.name))
            print(f'Moved file: {wav_file}')
        except OSError as e:
            print(f'Error: {wav_file} : {e.strerror}')


    print(f"Book '{book_title}' by {author} has been created.")

#########################################################
# Controls the generation process, pass in epub filename
########################################################

def generate_audiobook(epub_filename):

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

    print('Converting Chapters using StyleTTS 2, via HF Spaces')

    client = Client(spaces_api_url,hf_token=hf_token)

    for chapter in chapters:

        chapter_title = chapter[0]

        if chapter_title != 'temp' and chapter_title != '':

            chapter_num += 1

            safe_chapter_title = sanitize_title(chapter_title)
            chapter_path = safe_title+'/'+str(chapter_num)+' - '+safe_chapter_title+'.wav'

            if not os.path.exists(chapter_path):
            
                chapter_paragraphs = chapter[1]

                convert_chapter(client,chapter_path,chapter_paragraphs)

    print('Chapters done generating, now converting to m4b.')
    
    convert_wav_to_m4b(safe_title, title, author)
    
    time_to_finish = time.time() -start_time

    print('Book Generated in: '+str(time_to_finish)+' seconds')


def main():

    parser = argparse.ArgumentParser(description='Process arguments.')

    # Add the mandatory arguments
    parser.add_argument('filename', help='Epub filename', type=str)

    # Parse the arguments
    args = parser.parse_args()

    epub_filename = args.filename

    generate_audiobook(epub_filename)

if __name__ == "__main__":
    main()
