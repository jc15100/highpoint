
class HighpointResult:
    smashes: [str]
    group_highlight: str
    player_speeds: {str: [int]}
    player_frames: [str]
    supported: bool

    def __init__(self, smashes, group_highlight, player_speeds, player_frames, supported):
        self.smashes = smashes
        self.group_highlight = group_highlight
        self.player_speeds = player_speeds
        self.player_frames = player_frames
        self.supported = supported
        
