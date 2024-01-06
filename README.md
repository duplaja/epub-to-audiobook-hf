# Epub to Audiobook (M4B)
Epub to MB4 Audiobook, with StyleTTS2 via HuggingFace Spaces API

## Notes

* **Breaking Changes Jan 5: You must re-clone the Space and update your script here, both, for new features.**

* This uses [StyleTTS 2](https://github.com/yl4579/StyleTTS2). Running on the Smallest Tesla T4 space, it generates audio at around 10x realtime (10 min audio for one minute of running), or 13-15x realtime using LJSpeech (new default). [See a demo here](https://huggingface.co/spaces/styletts2/styletts2), to hear the quality.

* This requires a HuggingFace account, with billing attached. To give an idea of efficiency, I generated a 5 hour audiobook in around 30 min, $0.35 in costs or so (counting start up time, etc). **Note: Retested on newly implimented LJSpeech, and time was closer to 20 min for the same book. 30% time / cost savings!**

* Newly added; Ability to awaken / pause your HF Space automatically, for biggest savings. (see `HF_REPO_ID` below)

* This is very much a version 1.0. I haven't extensively tested the epub parsing, outside of a few that I had. I can't guarantee it'll work with all of them.

* This is designed to handle failure gracefully, in that if you start generating, and it crashes / errors during the generating process (happens occasionally with the HF API), then it'll skip over already generated chapters, and generate starting with the first one that is missing. This is also nice for breaking up the generation of large books. The m4b file is only generated once all chapters are generated.

## Directions

* Clone this repository locally.

* Install all dependencies, as needed: `pip install -r requirements.txt`

* Sign up on [HuggingFace.co](https://hugginface.co), if you have not already. (note: may have to disable adblocker to sign up, otherwise redirect breaks). Add a payment method. Generate a token with write access, using this link: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

* Make a copy on HuggingFace of this space: [https://huggingface.co/spaces/Dupaja/styletts2-public/](https://huggingface.co/spaces/Dupaja/styletts2-public/) (3 dots, Duplicate this Space, private copy). Pick the lowest GPU instance, Small Tesla T4. (Note: This demo instance is running on the Free CPU plan, so it is not really usable. If you want to test out the voices / sound first, check out the official demo here: [https://huggingface.co/spaces/styletts2/styletts2](https://huggingface.co/spaces/styletts2/styletts2) .

* Go to your new space's settings, and set your "Sleep After" time to 15 min, to prevent it from running when not in use. This runs at a cost of $0.60 / hour, billed by the minute, and you can pause at any time from the settings page, using the Pause toggle.

Once the Space builds, do the following:

- Go to your Space's App page, and find the API link in the footer. This will give you the API URL (**Only copy the url through .space , you don't need or want the rest of it, since it changes each time**). 

- Add the API url to epub-to-audiobook-hf.py and your HuggingFace Token to this file, lines 26 and 28, or set the `SPACES_API_URL` and `HF_TOKEN` env variables. Optionally add your Space's Repo ID to line 30, or set the `HF_REPO_ID` env var (Example: `Dupaja/styletts2-public`), if you want to be able to automatically unpause / awaken, and auto-pause your space.

- Put the epub you want to generate from in the same folder as epub-to-audiobook-hf.py

* Run using `python3 epub-to-audiobook-hf.py <filename-of-epub>. 

* You can optionally use the command line flag `--voice f-us-2`, or other voice from the list to select a voice (see code or demo space for possible choices). Leaving this out defaults to LJSpeech, the (faster, better sounding imo) option, although it has only one voice.

* You can optionally use the command line flag `--awake` with no arguments, to keep your space from autopausing right away after generation (only if you have your repo ID set).

## A Big Thanks To:

* [mrfakename](https://huggingface.co/mrfakename) : Original developer of the StyleTTS 2 Hugging Face Space, and a huge help for bouncing ideas / troubleshooting!
* [audiobookshelf](https://github.com/advplyr/audiobookshelf), for inspiring this project
* [StyleTTS 2 Project](https://github.com/yl4579/StyleTTS2) (extremely fast, natural sounding text to speech)
* [m4b-util](https://github.com/Tsubashi/m4b-util) (m4b building utilities)
* [ebooklib](https://github.com/aerkalov/ebooklib) (ebook parsing)
* [epub-to-audiobook](https://github.com/p0n1/epub_to_audiobook) (ebook parsing)
* [HuggingFace](https://huggingface.co) (Spaces infrastructure)
