from ovos_utils.skills.templates.common_play import BetterCommonPlaySkill
from ovos_utils.playback import CPSMatchType, CPSPlayback, CPSMatchConfidence
import pafy
from tempfile import gettempdir
import re
import subprocess
from os.path import join, dirname, exists
import random


class WayneJuneLovecraftReadingsSkill(BetterCommonPlaySkill):

    def __init__(self):
        super().__init__("Wayne June Lovecraft Readings")
        self.supported_media = [CPSMatchType.GENERIC,
                                CPSMatchType.AUDIOBOOK,
                                CPSMatchType.VISUAL_STORY,
                                CPSMatchType.VIDEO]
        self.urls = {
            # these 3 are in official account
            "tomb": "https://www.youtube.com/watch?v=6yIqQ2O-zws",
            "virgin_finlay": "https://www.youtube.com/watch?v=zf_Il12Tgn8",
            # NOTE provided below, the other link does not need to extract
            # the real stream and is prefered
            #"thing_doorstep": "https://www.youtube.com/watch?v=PicZATCo3h4",

            # these are likely to be taken down soon
            "shunned_house": "https://www.youtube.com/watch?v=77xxGopjMbY",

            # these were removed from youtube but backed up, might also disappear
            "horror_red_hook": "https://archive.org/download/youtube-rMhYkkaR8HU/H.P._Lovecraft_-_The_Horror_At_Red_Hook_-_Wayne_June-rMhYkkaR8HU.mp4",
            "innsmouth": "https://archive.org/download/youtube-aFZrqYn5f_0/H.P._Lovecraft_-_The_Shadow_Over_Innsmouth_-_Wayne_June-aFZrqYn5f_0.mp4",
            "reanimator": "https://archive.org/download/youtube-GfHClVEPcjU/H.P._Lovecraft_-_Herbert_West_Reanimator_-_Wayne_June-GfHClVEPcjU.mp4",
            "lurking_fear": "https://archive.org/download/youtube--CZZo_y3TB8/H.P._LOVECRAFT_-_The_Lurking_Fear_-_Wayne_June--CZZo_y3TB8.mp4",
            "cthulhu": "https://archive.org/download/youtube-EHGj5M8WIAQ/THE_CALL_OF_CTHULHU_-_H.P._LOVECRAFT_-_Wayne_June-EHGj5M8WIAQ.mp4",
            "dunwich": "https://archive.org/download/youtube-OL8iuoZqX_U/H.P._Lovecraft_-_The_Dunwich_Horror_-_Wayne_June-OL8iuoZqX_U.mp4",
            "thing_doorstep": "https://archive.org/download/youtube-gHLEGzu8Dw8/H.P._Lovecraft_-_The_Thing_On_The_Doorstep_-_Wayne_June-gHLEGzu8Dw8.mp4",

            # TODO more streams, this guy is the best and has read
            # nearly everything from lovecraft, can only find paid
            # audiobooks for the remaining stories
        }
        self.default_image = join(dirname(__file__), "ui", "logo.png")

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
            media_type (CPSMatchType): requested CPSMatchType to search for

        Returns:
            search_results (list): list of dictionaries with result entries
            {
                "match_confidence": CPSMatchConfidence.HIGH,
                "media_type":  CPSMatchType.MUSIC,
                "uri": "https://audioservice.or.gui.will.play.this",
                "playback": CPSPlayback.GUI,
                "image": "http://optional.audioservice.jpg",
                "bg_image": "http://optional.audioservice.background.jpg"
            }
        """
        original = phrase
        score = 0

        # calculate a base score for media type + author
        if media_type == CPSMatchType.AUDIOBOOK:
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
            scores["horror_red_hook"] += 10
            scores["dunwich"] += 10

        if self.voc_match(phrase, "red_hook"):
            scores["horror_red_hook"] += 40
            if self.voc_match(phrase, "horror"):
                scores["horror_red_hook"] += 20

        if self.voc_match(phrase, "dunwich"):
            scores["dunwich"] += 40
            if self.voc_match(phrase, "horror"):
                scores["dunwich"] += 20

        if self.voc_match(phrase, "lurking_fear"):
            scores["lurking_fear"] += 70

        if self.voc_match(phrase, "tomb"):
            scores["tomb"] += 70
        if self.voc_match(phrase, "virgin_finlay"):
            scores["virgin_finlay"] += 70

        if self.voc_match(phrase, "reanimator"):
            scores["reanimator"] += 40
            if self.voc_match(phrase, "herbert_west"):
                scores["reanimator"] += 30

        if self.voc_match(phrase, "innsmouth"):
            scores["innsmouth"] += 40
            if self.voc_match(phrase, "shadow"):
                scores["innsmouth"] += 30

        if self.voc_match(phrase, "cthulhu"):
            scores["cthulhu"] += 40
            if self.voc_match(phrase, "call"):
                scores["cthulhu"] += 20

        if self.voc_match(phrase, "doorstep"):
            scores["thing_doorstep"] += 10
        if self.voc_match(phrase, "thing"):
            scores["thing_doorstep"] += 10
        if self.voc_match(phrase, "thing") and \
                self.voc_match(phrase, "doorstep"):
            scores["thing_doorstep"] += 50

        if self.voc_match(phrase, "house"):
            scores["shunned_house"] += 10
        if self.voc_match(phrase, "shunned"):
            scores["shunned_house"] += 10
        if self.voc_match(phrase, "shunned") and \
                self.voc_match(phrase, "house"):
            scores["shunned_house"] += 50

        matches = []
        for k, v in scores.items():
            if v >= CPSMatchConfidence.AVERAGE_LOW:
                matches.append({
                            "match_confidence": min(100, v),
                            "media_type": CPSMatchType.AUDIOBOOK,
                            "uri": self.urls[k],
                            "playback": CPSPlayback.AUDIO,
                            "image": self.default_image
                        })
        if matches:
            return matches
        return None


def create_skill():
    return WayneJuneLovecraftReadingsSkill()
