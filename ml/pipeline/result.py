
class HighpointResult:
    smashes: [str]
    smashes_urls: [str]
    group_highlight: str
    group_highlight_url: str
    player_speeds: {str: [int]}
    player_frames: [str]
    player_frames_urls: [str]
    supported: bool

    def __init__(self, 
                 smashes, 
                 smashes_urls, 
                 group_highlight, 
                 group_highlight_url, 
                 player_speeds, 
                 player_frames, 
                 player_frames_urls, 
                 supported):
        self.smashes = smashes
        self.smashes_urls = smashes_urls
        self.group_highlight = group_highlight
        self.group_highlight_url = group_highlight_url
        self.player_speeds = player_speeds
        self.player_frames = player_frames
        self.player_frames_urls = player_frames_urls
        self.supported = supported
        
