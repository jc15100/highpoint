## Requirements

Run `pip3 install -r requirements.txt`

## Running the code

Place the input video (`.mp4` format) in `pipeline/input/` folder.
Then, from the top of the repo run:

```
python pipeline/run.py --input-video "pipeline/input/intermediate.mp4" --output-path "pipeline/output" --output-name "video_summary.mp4"
```

## Papers Tried So Far
List of approaches/repos investigated for project idea.

### LTC-GIF: git@github.com:jc15100/LTC-GIF.git
Project uses Attention-based Deep NNs to determine the best sequence & render a GIF. Uses vdc repo for video preprocessing.
Approach is not working well initially.


### PGL-SUM: git@github.com:jc15100/PGL-SUM.git
Top result according to paperswithcode.com on Video Summarization task.
Likely needs fine tuning for sports videos.
