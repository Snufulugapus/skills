---
name: youtube-transcript
description: Fetch the transcript of a YouTube video or Short and load it into the current conversation so Claude can read, summarize, quote, or reason over the spoken content. Use this skill whenever the user shares a YouTube URL (youtube.com/watch, youtu.be/*, youtube.com/shorts/*) and wants to discuss, summarize, analyze, extract quotes from, or ask questions about the video. Also trigger for phrases like "get the transcript", "pull the transcript", "what does this video say", "summarize this YouTube video", "pull captions", or any time a YouTube link appears alongside intent to engage with its content rather than just share the link.
---

# YouTube Transcript

Fetch the transcript of a YouTube video or Short using `yt-dlp` and bring it into the current conversation.

## When to use

Run this whenever the user pastes a YouTube URL and clearly wants Claude to engage with the video's content — summarize, quote, analyze, cross-reference, etc. Don't run it if the user is just sharing the link for later or asking about something unrelated to the video.

Accept any YouTube URL form:
- `https://www.youtube.com/watch?v=...`
- `https://youtu.be/...`
- `https://www.youtube.com/shorts/...`
- Bare video IDs if obvious from context

## How to run it

Invoke the bundled script with the URL:

```bash
python ~/.claude/skills/youtube-transcript/scripts/fetch_transcript.py "<URL>"
```

Flags:
- `--timestamps` — prepend `[HH:MM:SS]` to each line. Useful when the user wants to cite moments or navigate back to specific parts. Off by default for cleaner summarization input.
- `--lang <code>` — caption language (default `en`). Use when the video is non-English or the user asks for a specific language.

The script prints the transcript to stdout, preceded by a small metadata header (title, uploader, duration). Read the output and proceed with whatever the user asked for.

## What the script does

1. Confirms `yt-dlp` is installed; if missing, installs it via `pip install --user -U yt-dlp` and retries.
2. Downloads auto-generated captions (and manual captions if present) to a temp directory — no video file is downloaded.
3. Parses the VTT, strips inline timing tags, deduplicates YouTube's rolling auto-caption lines (each cue normally repeats prior words), and emits clean text.
4. Cleans up the temp dir.

## Common failure modes

- **"No captions found"** — the video has captions disabled, or the requested language isn't available. Tell the user; offer to retry with `--lang <other>` if plausible. Some very new uploads also don't have auto-captions generated yet.
- **Age-restricted / private / members-only video** — `yt-dlp` can't fetch these without cookies. Tell the user this is the limitation; don't try to work around it.
- **Livestream still in progress** — captions may be incomplete or absent. Wait for the stream to end, or proceed with whatever is available.

## Output handling

For most videos the transcript fits comfortably in the conversation (a 10-minute video is ~1500 words). For very long content (multi-hour podcasts) the stdout can get large — if you hit token limits, redirect the output to a file and use `Read` with pagination instead:

```bash
python ~/.claude/skills/youtube-transcript/scripts/fetch_transcript.py "<URL>" > /tmp/yt-transcript.txt
```

Then `Read` the file in chunks.

## After fetching

Don't dump the whole transcript back at the user — they already know what's in the video. Do whatever they actually asked for (summarize, answer a question, extract quotes, translate, etc.). If they didn't ask for anything specific, offer 2-3 concrete things you can do with it.
