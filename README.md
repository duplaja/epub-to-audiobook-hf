# Epub to Audiobook (M4B)
Epub to MB4 Audiobook, with StyleTTS2 via local TTS api

## Notes
* This fork is designed to run the TTS through a local server / predictor. I got it working using this one: `https://replicate.com/adirik/styletts2` but others should work as well.
* You need approx 5GB of VRAM, and 5 GB of RAM to run the model locally (a bit less without custom voice)
* This is designed to handle failure gracefully, in that if you start generating, and it crashes / errors during the generating process (happens occasionally with the HF API), then it'll skip over already generated chapters, and generate starting with the first one that is missing. This is also nice for breaking up the generation of large books. The m4b file is only generated once all chapters are generated.

## Directions

* Clone this repository locally.

* Install all dependencies, as needed: `pip install -r requirements.txt`. Also make sure you have ffmpeg installed!

* Run a local StyleTTS2 server using ` docker run -d -p 5000:5000 --gpus=all r8.im/adirik/styletts2@sha256:dd4d03b097968361dda9b0563716eb0758d1d5b8aeb890d22bd08634e2bd069c`

* Run using `python3 epub-to-audiobook-hf.py <filename-of-epub> --voice reference_voice.wav`

* You should use the command line flag `--voice reference_voice.wav`. Leaving this out defaults to LJSpeech, the (faster, worse sounding imo) option, although it has only one voice.

## A Big Thanks To:

* [mrfakename](https://huggingface.co/mrfakename) : Original developer of the StyleTTS 2 Hugging Face Space, and a huge help for bouncing ideas / troubleshooting!
* [audiobookshelf](https://github.com/advplyr/audiobookshelf), for inspiring this project
* [StyleTTS 2 Project](https://github.com/yl4579/StyleTTS2) (extremely fast, natural sounding text to speech)
* [m4b-util](https://github.com/Tsubashi/m4b-util) (m4b building utilities)
* [ebooklib](https://github.com/aerkalov/ebooklib) (ebook parsing)
* [epub-to-audiobook](https://github.com/p0n1/epub_to_audiobook) (ebook parsing)
* [HuggingFace](https://huggingface.co) (Spaces infrastructure)
