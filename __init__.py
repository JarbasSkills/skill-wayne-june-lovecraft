from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill
from ovos_workshop.frameworks.playback import CommonPlayMediaType, CommonPlayPlaybackType, \
    CommonPlayMatchConfidence
import pafy
from tempfile import gettempdir
import re
import subprocess
from os.path import join, dirname, exists
import random


class WayneJuneLovecraftReadingsSkill(OVOSCommonPlaybackSkill):

    def __init__(self):
        super().__init__("Wayne June Lovecraft Readings")
        self.supported_media = [CommonPlayMediaType.GENERIC,
                                CommonPlayMediaType.AUDIOBOOK,
                                CommonPlayMediaType.VISUAL_STORY,
                                CommonPlayMediaType.VIDEO]
        self.default_image = join(dirname(__file__), "ui", "wayne_june.png")
        self.skill_logo = join(dirname(__file__), "ui", "logo.png")
        self.skill_icon = join(dirname(__file__), "ui", "icon.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.jpeg")
        # TODO use media collection skill template instead
        self.urls = {
            # these 3 are in official account
            "The Tomb": "https://www.youtube.com/watch?v=6yIqQ2O-zws",
        #    "To Virgil Finlay": "https://www.youtube.com/watch?v=zf_Il12Tgn8",
            # NOTE provided below, the other link does not need to extract
            # the real stream and is prefered
            # "The Thing On The Doorstep": "https://www.youtube.com/watch?v=PicZATCo3h4",

            # these are likely to be taken down soon
            "The Shunned House": "https://www.youtube.com/watch?v=77xxGopjMbY",

            # these were removed from youtube but backed up, might also disappear
            "The Horror At Red Hook": "https://archive.org/download/youtube-rMhYkkaR8HU/H.P._Lovecraft_-_The_Horror_At_Red_Hook_-_Wayne_June-rMhYkkaR8HU.mp4",
            "The Shadow Over Innsmouth": "https://archive.org/download/youtube-aFZrqYn5f_0/H.P._Lovecraft_-_The_Shadow_Over_Innsmouth_-_Wayne_June-aFZrqYn5f_0.mp4",
            "Herbert West–Reanimator": "https://archive.org/download/youtube-GfHClVEPcjU/H.P._Lovecraft_-_Herbert_West_Reanimator_-_Wayne_June-GfHClVEPcjU.mp4",
            "The Lurking Fear": "https://archive.org/download/youtube--CZZo_y3TB8/H.P._LOVECRAFT_-_The_Lurking_Fear_-_Wayne_June--CZZo_y3TB8.mp4",
            "The Call Of Cthulhu": "https://archive.org/download/youtube-EHGj5M8WIAQ/THE_CALL_OF_CTHULHU_-_H.P._LOVECRAFT_-_Wayne_June-EHGj5M8WIAQ.mp4",
            "The Dunwich Horror": "https://archive.org/download/youtube-OL8iuoZqX_U/H.P._Lovecraft_-_The_Dunwich_Horror_-_Wayne_June-OL8iuoZqX_U.mp4",
            "The Thing On The Doorstep": "https://archive.org/download/youtube-gHLEGzu8Dw8/H.P._Lovecraft_-_The_Thing_On_The_Doorstep_-_Wayne_June-gHLEGzu8Dw8.mp4",

            # TODO more streams, this guy is the best and has read
            # nearly everything from lovecraft, can only find paid
            # audiobooks for the remaining stories
        }
        self.durations = {
            "The Tomb": 28 * 60 + 58,  # 28:58
          #  "To Virgil Finlay": 1 * 60 + 26,  # 1:26
            "The Shunned House": 1 * 3600 + 18 * 60 + 24,  # 1:18:24
            "The Horror At Red Hook": 1 * 3600 + 4 * 60 + 22,  # 1:04:22
            "The Shadow Over Innsmouth": 2 * 3600 + 53 * 60 + 22,  # 2:53:22
            "Herbert West–Reanimator": 1 * 3600 + 30 * 60 + 47,  # 1:30:47
            "The Lurking Fear": 1 * 3600 + 2 * 60 + 6,  # 1:02:06
            "The Call Of Cthulhu": 1 * 3600 + 19 * 60 + 20,  # 1:19:20
            "The Dunwich Horror": 1 * 3600 + 51 * 60 + 30, # 1:51:30
            "The Thing On The Doorstep": 1 * 3600 + 17 * 60 + 49,  # 1:17:49
        }
        self.pictures = {
            "The Tomb": join(dirname(__file__), "ui", "tomb.jpeg"),
           # "To Virgil Finlay": self.default_image,
            "The Shunned House": join(dirname(__file__), "ui", "shunned_house.jpeg"),
            "The Horror At Red Hook": join(dirname(__file__), "ui", "red_hook.jpeg"),
            "The Shadow Over Innsmouth": join(dirname(__file__), "ui", "innsmouth.jpeg"),
            "Herbert West–Reanimator": join(dirname(__file__), "ui", "herbertwest.png"),
            "The Lurking Fear": join(dirname(__file__), "ui", "lurking.jpeg"),
            "The Call Of Cthulhu": join(dirname(__file__), "ui", "call.jpeg"),
            "The Dunwich Horror":join(dirname(__file__), "ui", "dunwich.jpeg"),
            "The Thing On The Doorstep": join(dirname(__file__), "ui", "thing.png"),
        }



    def get_intro_message(self):
        self.speak_dialog("intro")
        self.gui.show_image(self.default_image)

    def clean_vocs(self, phrase):
        phrase = self.remove_voc(phrase, "reading")
        phrase = self.remove_voc(phrase, "audio_theatre")
        phrase = self.remove_voc(phrase, "play")
        phrase = phrase.strip()
        return phrase

    # better common play
    def CPS_search(self, phrase, media_type):
        """Analyze phrase to see if it is a play-able phrase with this skill.

        Arguments:
            phrase (str): User phrase uttered after "Play", e.g. "some music"
            media_type (CommonPlayMediaType): requested CPSMatchType to search for

        Returns:
            search_results (list): list of dictionaries with result entries
            {
                "match_confidence": CommonPlayMatchConfidence.HIGH,
                "media_type":  CPSMatchType.MUSIC,
                "uri": "https://audioservice.or.gui.will.play.this",
                "playback": CommonPlayPlaybackType.VIDEO,
                "image": "http://optional.audioservice.jpg",
                "bg_image": "http://optional.audioservice.background.jpg"
            }
        """
        original = phrase
        score = 0

        # calculate a base score for media type + author
        if media_type == CommonPlayMediaType.AUDIOBOOK:
            score += 10

        if self.voc_match(original, "reading"):
            score += 10

        if self.voc_match(original, "audio_theatre"):
            score += 10

        phrase = self.clean_vocs(phrase)

        if self.voc_match(phrase, "lovecraft"):
            score += 30

        if self.voc_match(phrase, "wayne_june"):
            score += 35
            if self.voc_match(phrase, "lovecraft"):
                score += 10

        if self.voc_match(phrase, "horror"):
            score += 10
        if self.voc_match(phrase, "cthulhu"):
            score += 10

        # calculate scores for individual stories
        # NOTE: each match is designed to be 70 for exact match,
        # the other 30 are reserved for author/media type
        # NOTE2: all my lovecraft skills are designed to return confidence
        # of 40 if the query only contains the author, this is important to
        # ensure all stories are equal without extra information
        scores = {}
        for k in self.urls:
            scores[k] = score

        if self.voc_match(phrase, "horror"):
            scores["The Horror At Red Hook"] += 10
            scores["The Dunwich Horror"] += 10

        if self.voc_match(phrase, "red_hook"):
            scores["The Horror At Red Hook"] += 40
            if self.voc_match(phrase, "horror"):
                scores["The Horror At Red Hook"] += 20

        if self.voc_match(phrase, "dunwich"):
            scores["The Dunwich Horror"] += 40
            if self.voc_match(phrase, "horror"):
                scores["The Dunwich Horror"] += 20

        if self.voc_match(phrase, "lurking_fear"):
            scores["The Lurking Fear"] += 70

        if self.voc_match(phrase, "tomb"):
            scores["The Tomb"] += 70
      #  if self.voc_match(phrase, "virgin_finlay"):
      #      scores["To Virgil Finlay"] += 70

        if self.voc_match(phrase, "reanimator"):
            scores["Herbert West–Reanimator"] += 40
            if self.voc_match(phrase, "herbert_west"):
                scores["Herbert West–Reanimator"] += 30

        if self.voc_match(phrase, "innsmouth"):
            scores["The Shadow Over Innsmouth"] += 40
            if self.voc_match(phrase, "shadow"):
                scores["The Shadow Over Innsmouth"] += 30

        if self.voc_match(phrase, "cthulhu"):
            scores["The Call Of Cthulhu"] += 40
            if self.voc_match(phrase, "call"):
                scores["The Call Of Cthulhu"] += 20

        if self.voc_match(phrase, "doorstep"):
            scores["The Thing On The Doorstep"] += 10
        if self.voc_match(phrase, "thing"):
            scores["The Thing On The Doorstep"] += 10
        if self.voc_match(phrase, "thing") and \
                self.voc_match(phrase, "doorstep"):
            scores["The Thing On The Doorstep"] += 50

        if self.voc_match(phrase, "house"):
            scores["The Shunned House"] += 10
        if self.voc_match(phrase, "shunned"):
            scores["The Shunned House"] += 10
        if self.voc_match(phrase, "shunned") and \
                self.voc_match(phrase, "house"):
            scores["The Shunned House"] += 50

        matches = []
        for k, v in scores.items():
            if v >= CommonPlayMatchConfidence.AVERAGE_LOW:
                matches.append({
                    "match_confidence": min(100, v),
                    "media_type": CommonPlayMediaType.AUDIOBOOK,
                    "uri": self.urls[k],
                    "playback": CommonPlayPlaybackType.AUDIO,
                    "image": self.pictures[k],
                    "bg_image": self.default_bg,
                    "skill_icon": self.skill_icon,
                    "skill_logo": self.skill_logo,
                    "length": self.durations[k] * 1000,
                    "title": k,
                    "author": "H. P. Lovecraft",
                    "album": "read by Wayne June"
                })
        if matches:
            return matches
        return None


def create_skill():
    return WayneJuneLovecraftReadingsSkill()
