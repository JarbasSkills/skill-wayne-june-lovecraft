from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel,\
    CPSTrackStatus, CPSMatchType
import pafy
from tempfile import gettempdir
import re
import subprocess
from os.path import join, dirname, exists
import random


class WayneJuneLovecraftReadingsSkill(CommonPlaySkill):

    def __init__(self):
        super().__init__("Wayne June Lovecraft Readings")
        if "download_audio" not in self.settings:
            self.settings["download_audio"] = True
        if "audio_only" not in self.settings:
            self.settings["audio_only"] = False

        self.lovecraft_stories = ["shunned_house", "tomb", "thing_doorstep"]
        self.lovecraft_comics = ["rats_walls", "cthulhu"]
        # TODO other authors read by wayne june
        self.stories = [] + self.lovecraft_stories

        self.urls = {
            # these 3 are in official account
            "tomb": "https://www.youtube.com/watch?v=6yIqQ2O-zws",
            "thing_doorstep": "https://www.youtube.com/watch?v=PicZATCo3h4",
            "virgin_finlay": "https://www.youtube.com/watch?v=zf_Il12Tgn8",

            # these are likely to be taken down soon
            "shunned_house": "https://www.youtube.com/watch?v=77xxGopjMbY",

            "rats_walls": "https://www.youtube.com/watch?v=o0eDis-w-90",
            "cthulhu": "https://www.youtube.com/watch?v=7RV6htNDTwI&t=1261s",


            # TODO more streams, this guy is the best and has read
            # nearly everything from lovecraft, can only find paid
            # audiobooks for the remaining stories however
            # Yet another lovecraft skill? this is why
        }
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.VIDEO,
                                CPSMatchType.MOVIE,
                                CPSMatchType.AUDIOBOOK]

    def initialize(self):
        self.add_event('skill-wayne-june-lovecraft.jarbasskills.home',
                       self.handle_homescreen)

        # speed up playback, download + convert in advance
        if self.settings["download_audio"]:
            for story in self.urls:
                try:
                    self.get_audio_stream(self.urls[story], True)
                except:
                    pass

    def get_intro_message(self):
        self.speak_dialog("intro")
        self.gui.show_image(join(dirname(__file__), "ui", "logo.png"))

    # homescreen
    def handle_homescreen(self, message):
        # TODO selection menu
        story = random.choice(["shunned_house", "tomb", "thing_doorstep"])
        self.CPS_start("wayne june lovecraft", {"url": self.urls[story]})

    # common play
    def remove_voc(self, utt, voc_filename, lang=None):
        lang = lang or self.lang
        cache_key = lang + voc_filename

        if cache_key not in self.voc_match_cache:
            self.voc_match(utt, voc_filename, lang)

        if utt:
            # Check for matches against complete words
            for i in self.voc_match_cache[cache_key]:
                # Substitute only whole words matching the token
                utt = re.sub(r'\b' + i + r"\b", "", utt)

        return utt

    def clean_vocs(self, phrase, authors=False):
        phrase = self.remove_voc(phrase, "reading")
        phrase = self.remove_voc(phrase, "audio_theatre")
        phrase = self.remove_voc(phrase, "play")
        if authors:
            phrase = self.remove_voc(phrase, "lovecraft")
            phrase = self.remove_voc(phrase, "wayne_june")
        phrase = phrase.strip()
        return phrase

    def CPS_match_query_phrase(self, phrase, media_type):

        original = phrase
        match = None
        score = 0
        story = random.choice(self.stories)

        if media_type == CPSMatchType.AUDIOBOOK or \
                self.voc_match(original, "reading"):
            score += 0.1
            match = CPSMatchLevel.GENERIC

        if media_type == CPSMatchType.VIDEO or \
                media_type == CPSMatchType.MOVIE or \
                self.voc_match(original, "comic"):
            if media_type != CPSMatchType.MOVIE:
                score += 0.1
            match = CPSMatchLevel.GENERIC
            story = random.choice(self.lovecraft_comics)

        if self.voc_match(original, "audio_theatre"):
            score += 0.1
            match = CPSMatchLevel.GENERIC

        phrase = self.clean_vocs(phrase)

        if self.voc_match(phrase, "lovecraft"):
            score += 0.3
            match = CPSMatchLevel.ARTIST
            story = random.choice(self.lovecraft_stories)

        # TODO readings of other authors by wayne june

        if self.voc_match(phrase, "wayne_june"):
            score += 0.3
            match = CPSMatchLevel.ARTIST
            if self.voc_match(phrase, "lovecraft"):
                score += 0.1
                match = CPSMatchLevel.MULTI_KEY

        title = self.clean_vocs(phrase, authors=True)

        # TODO self.fuzzy_voc_match(title, "XXX", thresh=0.65)

        if self.voc_match(title, "shunned_house"):
            score += 0.7
            story = "shunned_house"
            if match is not None:
                match = CPSMatchLevel.MULTI_KEY
            else:
                match = CPSMatchLevel.TITLE
        elif self.voc_match(title, "cthulhu"):
            score += 0.7
            story = "cthulhu"
            if match is not None:
                match = CPSMatchLevel.MULTI_KEY
            else:
                match = CPSMatchLevel.TITLE
        elif self.voc_match(title, "thing") and \
                self.voc_match(phrase, "doorstep"):
            score += 0.7
            story = "thing_doorstep"
            if match is not None:
                match = CPSMatchLevel.MULTI_KEY
            else:
                match = CPSMatchLevel.TITLE
        elif self.voc_match(title, "tomb"):
            score += 0.7
            story = "tomb"
            if match is not None:
                match = CPSMatchLevel.MULTI_KEY
            else:
                match = CPSMatchLevel.TITLE
        elif self.voc_match(title, "rats") and self.voc_match(title, "walls"):
            score += 0.7
            story = "rats_walls"
            if match is not None:
                match = CPSMatchLevel.MULTI_KEY
            else:
                match = CPSMatchLevel.TITLE
        elif self.voc_match(title, "virgin_finlay"):
            score += 0.7
            story = "virgin_finlay"
            if match is not None:
                match = CPSMatchLevel.MULTI_KEY
            else:
                match = CPSMatchLevel.TITLE

        if score >= 0.9:
            match = CPSMatchLevel.EXACT

        url = self.urls[story]

        if match is not None:
            return (phrase, match,
                    {"query": original, "story": story, "url": url})
        return None

    def CPS_start(self, phrase, data):

        if self.gui.connected and not self.settings["audio_only"]:
            url = self.get_video_stream(data["url"])
            self.CPS_send_status(uri=url,
                                 playlist_position=0,
                                 title=data["story"],
                                 status=CPSTrackStatus.PLAYING_GUI)
            self.gui.play_video(url, data["story"])
        else:
            url = self.get_audio_stream(data["url"], self.settings["download_audio"])
            self.audioservice.play(url, utterance=self.play_service_string)
            self.CPS_send_status(uri=url,
                                 playlist_position=0,
                                 title=data["story"],
                                 status=CPSTrackStatus.PLAYING_AUDIOSERVICE)

    # youtube handling
    @staticmethod
    def get_audio_stream(url, download=False):
        stream = pafy.new(url).getbestaudio()

        # TODO check if https supported by audioservice
        # if not set download=True without needing user changing settings.json
        if download:
            path = join(gettempdir(),
                        url.split("watch?v=")[-1] + "." + stream.extension)
            mp3 = join(gettempdir(), url.split("watch?v=")[-1] + ".mp3")

            if not exists(mp3) and not exists(path):
                stream.download(path)

            if not exists(mp3):
                # convert file to allow playback with simple audio backend
                command = ["ffmpeg", "-n", "-i", path, "-acodec",
                           "libmp3lame",
                           "-ab", "128k", mp3]
                subprocess.call(command)

            return mp3
        return stream.url

    @staticmethod
    def get_video_stream(url):
        stream = pafy.new(url).getbest()
        return stream.url


def create_skill():
    return WayneJuneLovecraftReadingsSkill()
