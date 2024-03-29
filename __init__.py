from os.path import join, dirname

from json_database import JsonStorage
from ovos_utils.ocp import MediaType, PlaybackType
from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class WayneJuneLovecraftReadingsSkill(OVOSCommonPlaybackSkill):
    def __init__(self, *args, **kwargs):
        self.supported_media = [MediaType.AUDIOBOOK,
                                MediaType.VISUAL_STORY,
                                MediaType.VIDEO]
        self.default_image = join(dirname(__file__), "ui", "wayne_june.png")
        self.skill_icon = join(dirname(__file__), "ui", "icon.png")
        self.default_bg = join(dirname(__file__), "ui", "bg.jpeg")
        self.db = JsonStorage(join(dirname(__file__), "res", "waynejune.json"))
        super().__init__(*args, **kwargs)

        self.register_ocp_keyword(MediaType.AUDIOBOOK,
                                  "book_name", list(self.db.keys()))
        self.register_ocp_keyword(MediaType.AUDIOBOOK,
                                  "book_author", ["Lovecraft", "H. P. Lovecraft"])
        self.register_ocp_keyword(MediaType.AUDIOBOOK,
                                  "audiobook_narrator", ["Wayne June"])
        self.register_ocp_keyword(MediaType.AUDIOBOOK,
                                  "audiobook_streaming_provider",
                                  ["HorrorBabble", "Horror Babble"])

    def get_base_score(self, phrase):
        score = 0
        if self.voc_match(phrase, "reading"):
            score += 10

        if self.voc_match(phrase, "audio_theatre"):
            score += 10

        if self.voc_match(phrase, "lovecraft"):
            score += 50

        if self.voc_match(phrase, "wayne_june"):
            score += 35
            if self.voc_match(phrase, "lovecraft"):
                score += 10

        if self.voc_match(phrase, "horror"):
            score += 10
        if self.voc_match(phrase, "cthulhu"):
            score += 10
        return score

    @ocp_search()
    def ocp_waynejune_lovecraft_playlist(self, phrase):
        score = self.get_base_score(phrase)
        if self.voc_match(phrase, "wayne_june"):
            score += 50
        yield {
            "match_confidence": score,
            "media_type": MediaType.AUDIOBOOK,
            "playlist": self.featured_media(),
            "playback": PlaybackType.AUDIO,
            "skill_icon": self.skill_icon,
            "image": self.default_bg,
            "bg_image": self.default_bg,
            "title": "Lovecraft - read by Wayne June (Compilation Playlist)",
            "author": "H. P. Lovecraft",
            "album": "read by Wayne June"
        }

    def clean_vocs(self, phrase):
        phrase = self.remove_voc(phrase, "reading")
        phrase = self.remove_voc(phrase, "audio_theatre")
        phrase = self.remove_voc(phrase, "play")
        phrase = phrase.strip()
        return phrase

    @ocp_search()
    def search(self, phrase, media_type):
        """Analyze phrase to see if it is a play-able phrase with this skill.

        Arguments:
            phrase (str): User phrase uttered after "Play", e.g. "some music"
            media_type (MediaType): requested CPSMatchType to media for

        Returns:
            search_results (list): list of dictionaries with result entries
            {
                "match_confidence": MatchConfidence.HIGH,
                "media_type":  CPSMatchType.MUSIC,
                "uri": "https://audioservice.or.gui.will.play.this",
                "playback": PlaybackType.VIDEO,
                "image": "http://optional.audioservice.jpg",
                "bg_image": "http://optional.audioservice.background.jpg"
            }
        """
        score = self.get_base_score(phrase)
        if media_type != MediaType.AUDIOBOOK:
            score -= 20

        phrase = self.clean_vocs(phrase)

        # calculate scores for individual stories
        # NOTE: each match is designed to be 70 for exact match,
        # the other 30 are reserved for author/media type
        # NOTE2: all my lovecraft skills are designed to return confidence
        # of 40 if the query only contains the author, this is important to
        # ensure all stories are equal without extra information
        scores = {}
        for k in self.db:
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

        if self.voc_match(phrase, "mountains"):
            scores["At The Mountains Of Madness"] += 70

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

        for k, v in scores.items():
            if v >= 50:
                yield {
                    "match_confidence": min(100, v),
                    "media_type": MediaType.AUDIOBOOK,
                    "uri": self.db[k]["uri"],
                    "playback": PlaybackType.AUDIO,
                    "image": join(dirname(__file__), self.db[k]["image"]),
                    "bg_image": self.default_bg,
                    "skill_icon": self.skill_icon,
                    "length": self.db[k]["length"],
                    "title": k,
                    "author": "H. P. Lovecraft",
                    "album": "read by Wayne June"
                }

    @ocp_featured_media()
    def featured_media(self):
        return [
            {"media_type": MediaType.AUDIOBOOK,
             "uri": entry["uri"],
             "playback": PlaybackType.AUDIO,
             "image": join(dirname(__file__), entry["image"]),
             "bg_image": self.default_bg,
             "skill_icon": self.skill_icon,
             "length": entry["length"],
             "title": title,
             "author": "H. P. Lovecraft",
             "album": "read by Wayne June"
             } for title, entry in self.db.items()
        ]


