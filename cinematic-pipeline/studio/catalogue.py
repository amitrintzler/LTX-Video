"""A catalogue of what this studio can make, each entry with a real sample.

The dashboard previously listed files. This answers the more useful question -
what kinds of thing can be produced, what is each for, and how do I make one -
and proves each answer with a small, deliberately low-quality proxy clipped from
real output so the page stays light.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from jobs import PROJECT, RENDER_ROOT

PROXY_DIR = Path.home() / "LTX-Studio" / "proxies"
PROXY_DIR.mkdir(parents=True, exist_ok=True)

FINAL = RENDER_ROOT / "ltx25-optionseducator-trailer60"
PREVIEW = RENDER_ROOT / "ltx25-optionseducator-trailer60-preview"
VIDEO_PIPELINE_OUT = Path(__file__).resolve().parents[2] / "video-pipeline" / "output"
FRAMEWORK = RENDER_ROOT / "framework-design"

# "category" groups the dashboard the way someone arrives at it - "I need a
# sound", "I need an image" - rather than by which engine happens to make it.
# It is deliberately not "kind": kind is the sample's file type and decides
# which player renders it, and an animation is a video file but a different
# thing to ask for.
#
# id, title, what it is for, the job that makes one, how to find a sample
KINDS: list[dict[str, Any]] = [
    {
        "id": "trailer",
        "category": "film",
        "engine": "LTX + post",
        "usage": "Landing page hero, YouTube, investor or press send-out",
        "title": "Cinematic trailer",
        "purpose": "Landing-page hero and YouTube. 60s, story arc, titles, score.",
        "job": "render-final",
        "length": "30-90s",
        "kind": "video",
        "find": lambda: _first(
            [
                FINAL / "optionseducator_ltx25_trailer60.mp4",
                PREVIEW / "optionseducator_ltx25_trailer60_preview.mp4",
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "world",
        "category": "shot",
        "engine": "LTX",
        "usage": "Atmosphere, establishing shots, mood between product beats",
        "title": "Generated world clip",
        "purpose": "Atmosphere a screenshot cannot show: streets, weather, scale. Generated in the game's style.",
        "job": "regenerate-clip",
        "length": "10s per clip",
        "kind": "video",
        "find": lambda: _glob(FINAL / "shots", "*_ltx.mp4"),
        "sample_at": 0.5,
        "sample_len": 4.0,
    },
    {
        "id": "product",
        "category": "shot",
        "engine": "Post only",
        "usage": "Feature explainers, onboarding, app-store and site loops",
        "title": "Product demo shot",
        "purpose": "Your real UI, pixel-perfect, with a camera move. No GPU, any length.",
        "job": "offline-cut",
        "length": "2-8s per shot",
        "kind": "video",
        "find": lambda: _glob(FINAL / "shots", "*_ui.mp4"),
        "sample_at": 0.2,
        "sample_len": 4.0,
    },
    {
        "id": "story",
        "category": "film",
        "engine": "Post only",
        "usage": "Lesson promos, social posts about a concept, in-app teasers",
        "title": "Story lesson reel",
        "purpose": "Your own storybook art, each page captioned with its title and the concept it teaches.",
        "job": "reassemble",
        "length": "any",
        "kind": "video",
        "find": lambda: _first([FINAL / "shots" / "story_panel.mp4"]),
        "sample_at": 0.0,
        "sample_len": 6.0,
    },
    {
        "id": "chart",
        "category": "shot",
        "engine": "Post only",
        "usage": "Anywhere a real price chart must be readable on screen",
        "title": "Stock chart on a building",
        "purpose": "A real price chart with signals and volume, warped onto a facade so it belongs to the city.",
        "job": "reassemble",
        "length": "any",
        "kind": "video",
        "find": lambda: _glob(FINAL / "shots", "*_chart.mp4"),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "chain",
        "category": "shot",
        "engine": "Post only",
        "usage": "Explaining strikes, bid/ask and implied vol",
        "title": "Options chain display",
        "purpose": "Calls, strikes, puts and implied vol as a readable table, placed in the world.",
        "job": "reassemble",
        "length": "any",
        "kind": "video",
        "find": lambda: _glob(FINAL / "shots", "*_chain.mp4"),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "podcast",
        "category": "shot",
        "engine": "Post only",
        "usage": "Promoting the daily habit: podcast, video, news",
        "title": "Podcast and daily-video panels",
        "purpose": "Drawn players for the daily habit: microphone, waveform, transport, thumbnails.",
        "job": "reassemble",
        "length": "any",
        "kind": "video",
        "find": lambda: (
            _glob(FINAL / "shots", "*_podcast.mp4")
            or _glob(FINAL / "shots", "*_video.mp4")
        ),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "inworld_ui",
        "category": "shot",
        "engine": "LTX + post",
        "usage": "Showing the product without cutting away from the world",
        "title": "Product panel inside the world",
        "purpose": "Real app screens composited into a generated shot, so app and world share a frame.",
        "job": "reassemble",
        "length": "any",
        "kind": "video",
        "find": lambda: _glob(FINAL / "shots", "*_composited.mp4"),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "titles",
        "category": "image",
        "engine": "Post only",
        "usage": "Any caption, district plate, disclaimer or lower third",
        "title": "Title cards and street plates",
        "purpose": "Anything that must be read is drawn, never generated: headings, district plates, small print.",
        "job": "offline-cut",
        "length": "still",
        "kind": "image",
        "find": lambda: _glob(FINAL / "overlays", "0*.png"),
    },
    {
        "id": "payoffs",
        "category": "image",
        "engine": "Post only",
        "usage": "Teaching strategy shapes: calls, spreads, condors",
        "title": "Payoff diagrams",
        "purpose": "Covered call, vertical spread, volatility hedge, iron condor - correct silhouettes.",
        "job": "offline-cut",
        "length": "still",
        "kind": "image",
        "find": lambda: _glob(FINAL / "overlays", "payoffs_*.png"),
    },
    {
        "id": "thumbnail",
        "category": "image",
        "engine": "Post only",
        "usage": "YouTube thumbnails, site posters, social cards",
        "title": "Thumbnail and stills",
        "purpose": "A designed poster frame - headline type over clean key art, not a "
        "screenshot of a frame. The site-video job renders one beside its film; the older "
        "trailer thumbnails were made by hand.",
        "job": "site-video",
        "length": "still",
        "kind": "image",
        "find": lambda: _first([FRAMEWORK / "framework-demo.jpg"])
        or _glob(PROJECT / "youtube", "*.jpg"),
    },
    {
        "id": "score",
        "category": "sound",
        "engine": "Audio",
        "usage": "Any cut needing an original, rights-clear cue",
        "title": "Original score",
        "purpose": "Composed in code: key, tempo, hook and length are parameters, so any cut gets a fitting cue.",
        "job": "compose-score",
        "length": "any",
        "kind": "audio",
        "find": lambda: _first([PROJECT / "music" / "composed_score.wav"]),
    },
    {
        "id": "vertical",
        "category": "film",
        "engine": "Post only",
        "usage": "Reels, TikTok, Shorts",
        "title": "Vertical 9:16 cut",
        "purpose": "Reels, TikTok and Shorts, with brand header and CTA footer rather than a letterbox.",
        "job": "vertical-cut",
        "length": "15-60s",
        "kind": "video",
        "find": lambda: _glob(RENDER_ROOT, "studio-vertical-*/*.mp4"),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "openworld-montage",
        "category": "shot",
        "engine": "LTX + post",
        "usage": "A wider look at the open world: reveal, old town, storm, first trade, one open city",
        "title": "Open-world city montage",
        "purpose": "Five-beat cut of the open world itself, ahead of the product trailer: "
        "city reveal, old town, reading the storm, the first trade, one open city.",
        "job": "openworld-montage",
        "length": "60s",
        "kind": "video",
        # A separate script (ltx25_optionscity_firsttrade60.py), not the trailer this
        # studio drives. All five acts are cached, so "Make one" reassembles from
        # them (ffmpeg + narration) rather than spending a GPU render.
        "find": lambda: _first(
            [
                RENDER_ROOT
                / "ltx25-optionscity-firsttrade60-preview"
                / "optionscity_ltx25_firsttrade60_preview.mp4"
            ]
        ),
        "sample_at": 4.0,
        "sample_len": 5.0,
    },
    {
        "id": "image",
        "category": "image",
        "engine": "Flow (Nano Banana)",
        "usage": "Story art, mood boards, keyframes, thumbnails - free on this plan",
        "title": "Generated still",
        "purpose": "One illustration or photo-style still from a prompt via Flow's "
        "image model. Costs zero credits, so it is the studio's default image source.",
        "job": "image",
        "length": "still",
        "kind": "image",
        "find": lambda: _glob(RENDER_ROOT / "images", "*.png"),
    },
    {
        "id": "openworld-trailer",
        "category": "film",
        "engine": "Real product (no LTX, no Flow)",
        "usage": "The Open-World Options City feature, pitched: what it is, why it's "
        "different, what you can do in it",
        "title": "Open-World Options City trailer",
        "purpose": "A feature trailer built entirely from the real product - live "
        "captures of the actual 3D city (scripts/capture_open_world.py) and the "
        "real landing/simulator screenshots - not AI-generated footage.",
        "job": "openworld-trailer",
        "length": "~35s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "trailers"
                / "open-world"
                / "open_world_trailer.mp4"
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "options-chain-trailer",
        "category": "film",
        "engine": "Real product (no LTX, no Flow) + Flow cinematics",
        "usage": "The Options Chain tool, pitched: live Black-Scholes pricing "
        "across the full strike ladder",
        "title": "Options Chain trailer",
        "purpose": "2 real Flow cinematic shots plus a real Options Chain screenshot "
        "with drawn highlights on the actual Greeks grid.",
        "job": "options-chain-trailer",
        "length": "~35s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "trailers"
                / "options-chain"
                / "options_chain_trailer.mp4"
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "lesson-hub-trailer",
        "category": "film",
        "engine": "Real product (no LTX, no Flow) + Flow cinematics",
        "usage": "The learner dashboard/roadmap, pitched: one clear path through "
        "options & markets",
        "title": "Lesson Hub trailer",
        "purpose": "1 real Flow cinematic shot plus real dashboard screenshots with "
        "drawn highlights on the actual roadmap and module cards.",
        "job": "lesson-hub-trailer",
        "length": "~34s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "trailers"
                / "lesson-hub"
                / "lesson_hub_trailer.mp4"
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "insight-engine-trailer",
        "category": "film",
        "engine": "Real product (no LTX, no Flow)",
        "usage": "The strategy-selection simulator, pitched: see the trade-off "
        "before you make the trade",
        "title": "Insight Engine trailer",
        "purpose": "Built entirely from real captures of the Iron Condor "
        "strategy-selection flow, with drawn highlights - no cinematic shots "
        "were generated for this one (Flow was out of video credits).",
        "job": "insight-engine-trailer",
        "length": "~26s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "trailers"
                / "insight-engine"
                / "insight_engine_trailer.mp4"
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "simulator-trailer",
        "category": "film",
        "engine": "Real product (no LTX, no Flow)",
        "usage": "The Guided Simulator workspace, pitched: practice the trade "
        "before it's real",
        "title": "Guided Simulator trailer",
        "purpose": "Built entirely from real captures of the guided practice "
        "workspace and the 5-step interactive simulation, with drawn highlights.",
        "job": "simulator-trailer",
        "length": "~26s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "trailers"
                / "simulator"
                / "simulator_trailer.mp4"
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "lesson-library-trailer",
        "category": "film",
        "engine": "Real product (no LTX, no Flow)",
        "usage": "The lesson catalog and achievements, pitched: curated paths, "
        "real achievements",
        "title": "Lesson Library trailer",
        "purpose": "Built entirely from real captures of the library hero, mini "
        "modules, achievement badges, and curriculum cards, with drawn highlights.",
        "job": "lesson-library-trailer",
        "length": "~26s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "trailers"
                / "lesson-library"
                / "lesson_library_trailer.mp4"
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "assistant-trailer",
        "category": "film",
        "engine": "Real product (no LTX, no Flow)",
        "usage": "The AI Assistant, pitched: ask questions, get grounded answers",
        "title": "AI Assistant trailer",
        "purpose": "Built entirely from a real capture of the assistant's chat "
        "interface (lesson-aware mode, citation chips, concept highlights), with "
        "drawn highlights.",
        "job": "assistant-trailer",
        "length": "~26s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "trailers"
                / "assistant"
                / "assistant_trailer.mp4"
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "trade-demos-trailer",
        "category": "film",
        "engine": "Real product (no LTX, no Flow)",
        "usage": "The 30-day trade timeline lab, pitched: watch a real trade play "
        "out, day by day",
        "title": "Trade Demo Timeline Lab trailer",
        "purpose": "Built entirely from a real capture of the NVDA breakout call "
        "spread timeline (daily narrative, Greeks snapshot), with drawn highlights.",
        "job": "trade-demos-trailer",
        "length": "~26s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "trailers"
                / "trade-demos"
                / "trade_demos_trailer.mp4"
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "mini-games-trailer",
        "category": "film",
        "engine": "Real product (no LTX, no Flow)",
        "usage": "The mini-games arcade, pitched: five fast drills for real "
        "options skills",
        "title": "Mini-Games trailer",
        "purpose": "Built entirely from a real capture of the arcade catalog "
        "(Sim Challenge, Strategy Builder, Risk Ladder, Scenario Sprint, Market "
        "Maker Defense), with drawn highlights.",
        "job": "mini-games-trailer",
        "length": "~26s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "trailers"
                / "mini-games"
                / "mini_games_trailer.mp4"
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "market-maker-defense-trailer",
        "category": "film",
        "engine": "Real product (no LTX, no Flow)",
        "usage": "The Market Maker Defense mini-game, pitched: survive the "
        "opening bell",
        "title": "Market Maker Defense trailer",
        "purpose": "Built entirely from real captures of the mission briefing "
        "(delta & gamma concept) and the live trading HUD, with drawn highlights.",
        "job": "market-maker-defense-trailer",
        "length": "~26s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "trailers"
                / "market-maker-defense"
                / "market_maker_defense_trailer.mp4"
            ]
        ),
        "sample_at": 6.0,
        "sample_len": 5.0,
    },
    {
        "id": "animate-image",
        "category": "shot",
        "engine": "Veo i2v (Flow)",
        "usage": "Turn any still into real animation: story art, keyframes, posters",
        "title": "Animated illustration",
        "purpose": "An image becomes the start frame and Veo animates it with real "
        "motion - characters walk, cameras track, weather moves. The lane that "
        "replaced LTX i2v's statues.",
        "job": "animate-image",
        "length": "8s",
        "kind": "video",
        "find": lambda: (
            _first(
                [
                    Path.home()
                    / "LTX-Renders"
                    / "stories"
                    / "first_trade_fable"
                    / "pages"
                    / "01_anim.mp4"
                ]
            )
            or _glob(RENDER_ROOT / "animations", "*.mp4")
        ),
        "sample_at": 1.0,
        "sample_len": 5.0,
    },
    {
        "id": "story-reel",
        "category": "film",
        "engine": "Flow images + post",
        "usage": "Illustrated lesson stories, social storytelling, in-app tales",
        "title": "Illustrated story reel",
        "purpose": "A story spec (pages: prompt + caption) becomes generated storybook "
        "art with drawn captions, Ken Burns motion and a composed score - free art, "
        "no GPU.",
        "job": "story-reel",
        "length": "30-90s",
        "kind": "video",
        "find": lambda: _glob(Path.home() / "LTX-Renders" / "stories", "*/*.mp4"),
        "sample_at": 4.0,
        "sample_len": 5.0,
    },
    {
        "id": "showreel",
        "category": "film",
        "engine": "All six engines",
        "usage": "The studio's own demo reel - one chapter per engine, freshly generated",
        "title": "Studio showreel",
        "purpose": "ONE STUDIO / SIX ENGINES: LTX world shot, Veo via Flow, Manim math, "
        "a Remotion template, motion-gfx promo graphics, and the composed score - "
        "assembled with drawn cards and engine labels.",
        "job": "showreel",
        "length": "~60s",
        "kind": "video",
        "find": lambda: _first(
            [Path.home() / "LTX-Renders" / "studio-showreel" / "studio_showreel90.mp4"]
        ),
        "sample_at": 4.0,
        "sample_len": 5.0,
    },
    {
        "id": "site-video",
        "category": "film",
        "engine": "Real page capture + motion design + original score",
        "usage": "The video embedded on a real site page - shipped to "
        "gameofoptions.netlify.app/framework-design",
        "title": "Site page video",
        "purpose": "One retina capture of the live page under a virtual camera, "
        "the method as motion design, then a portal act proving every format "
        "(lesson, podcast, video, game, open world) with real captures. Original "
        "score and narration, no third-party audio.",
        "job": "site-video",
        "length": "~74s",
        "kind": "video",
        "find": lambda: _first([FRAMEWORK / "framework-demo.mp4"]),
        "sample_at": 60.0,
        "sample_len": 5.0,
    },
    {
        "id": "deliver",
        "category": "ship",
        "engine": "QA gates + the site's own R2 upload workflow",
        "usage": "Putting a finished render on the live site, with proof it is the one "
        "that passed QA",
        "title": "Ship it to the site",
        "purpose": "Checks the render (duration, loudness, true peak, the music drop's "
        "position, dropouts, repeated frames), then ships it: uploads to the media host "
        "and re-reads the live bytes to confirm. Never merges - that is a paid deploy.",
        "job": "deliver-site-video",
        "length": "~1 min",
        "kind": "video",
        "find": lambda: _first([FRAMEWORK / "framework-demo.mp4"]),
        "sample_at": 66.0,
        "sample_len": 5.0,
    },
    {
        "id": "narration",
        "category": "sound",
        "engine": "Kokoro-82M (offline, Apache-2.0)",
        "usage": "Voice-over for any cut - trailers, lessons, explainers",
        "title": "Narration",
        "purpose": "A spoken line, treated for trailer use: pitched down, EQ'd, "
        "doubled and put in a hall. Runs locally, so no API, no per-word cost "
        "and no licence to clear.",
        "job": "narration",
        "length": "per line",
        "kind": "audio",
        "find": lambda: _glob(FRAMEWORK / "work" / "vo", "*.wav"),
    },
    {
        "id": "capabilities-reel",
        "category": "film",
        "engine": "All 10 feature trailers + all six engines",
        "usage": 'The single answer to "show me everything this studio can do" - '
        "highlights from every feature trailer plus the six-engines showreel, cut "
        "as one piece",
        "title": "Studio capabilities reel",
        "purpose": "A three-act cut (WHY the product, WORLD the game, HOW the six "
        "engines build it) built from a Hollywood trailer-music-supervisor consult: "
        "one licensed bed carries the whole reel with per-act volume automation, "
        "the code-composed synth supplies only three one-shot transition stingers.",
        "job": "capabilities-reel",
        "length": "~118s",
        "kind": "video",
        "find": lambda: _first(
            [
                Path.home()
                / "LTX-Renders"
                / "studio-capabilities-reel"
                / "studio_capabilities_reel.mp4"
            ]
        ),
        "sample_at": 5.0,
        "sample_len": 5.0,
    },
    {
        "id": "cinematic-project",
        "category": "film",
        "engine": "Motion gfx / parallax / LTX-2",
        "usage": "Openmontage promo projects: Game of Options promo, trader films, "
        "depth-parallax shots, motion-graphics explainers",
        "title": "Cinematic promo project",
        "purpose": "The openmontage promo engine: a project.json describes shots "
        "(motion graphics, SDXL-still parallax camera moves, LTX-2 generations), "
        "and the pipeline renders keyframes, footage, audio bed and the graded final.",
        "job": "cinematic-project",
        "length": "any",
        "kind": "video",
        "find": lambda: _glob(
            Path(__file__).resolve().parents[1] / "projects", "*/output/*_final.mp4"
        ),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "remotion",
        "category": "animation",
        "engine": "Remotion (React)",
        "usage": "Lesson videos, Greeks curves, payoff walkthroughs, kinetic promos - "
        "20 ready templates",
        "title": "Remotion lesson template",
        "purpose": "The React-based template library moved in from the optionseducator "
        "repo: pick a composition (payoff diagrams, Greek curves, market mechanics, "
        "open-world promos...) and render it to MP4.",
        "job": "remotion",
        "length": "8s-3 min per template",
        "kind": "video",
        "find": lambda: _remotion_sample(),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "animation",
        "category": "animation",
        "engine": "Manim / HTML / D3 / slides",
        "usage": "Explainer and math animations: payoff curves, Greeks, charts, "
        "narrated concept walkthroughs - no GPU model involved",
        "title": "Programmatic animation",
        "purpose": "The video-pipeline's non-LTX renderers, from the openmontage work: "
        "give it a topic or scene script and it plans scenes, picks a renderer per "
        "scene (Manim, HTML/hyperframes, D3, slides), renders, narrates and stitches.",
        "job": "animation",
        "length": "any",
        "kind": "video",
        "find": lambda: _first(
            [
                VIDEO_PIPELINE_OUT / "options-trailer-final.mp4",
                VIDEO_PIPELINE_OUT / "trading-trailer-final.mp4",
            ]
        ),
        "sample_at": 2.0,
        "sample_len": 5.0,
    },
    {
        "id": "openworld-clip",
        "category": "shot",
        "engine": "LTX",
        "usage": "One act of the open-world montage: reveal, old town, storm, trade, open city",
        "title": "Open-world montage act",
        "purpose": "A single act of the First Trade montage, regenerated on its own so one "
        "weak beat does not cost a full re-render.",
        "job": "regenerate-montage-clip",
        "length": "5-10s per act",
        "kind": "video",
        "find": lambda: _montage_clip(),
        "sample_at": 0.5,
        "sample_len": 4.0,
    },
    {
        "id": "flow-hero",
        "category": "shot",
        "engine": "Flow (Veo) + LTX + post",
        "usage": "Higher-realism opening and closing shots for the product trailer",
        "title": "Flow hero bookends",
        "purpose": "The trailer's first and last shots (city_reveal, pantheon_night) "
        "regenerated on Veo via Flow, dropped into the clip cache so a reassemble "
        "picks them up - the middle stays LTX.",
        "job": "flow-hero-shots",
        "length": "8s per clip",
        "kind": "video",
        "find": lambda: _first(
            [FINAL / "city_reveal_flow.mp4", FINAL / "pantheon_night_flow.mp4"]
        ),
        "sample_at": 1.0,
        "sample_len": 4.0,
    },
    {
        "id": "flow",
        "category": "shot",
        "engine": "Google Flow (browser)",
        "usage": "Anything neither LTX nor a drawn browser page covers, when the local "
        "GPU is busy or the shot needs a different model entirely",
        "title": "Google Flow generation",
        "purpose": "Flow has no public API, so this drives the real web app in a signed-in "
        "browser: prompt in, generated clip or image out.",
        "job": "flow",
        "length": "any",
        "kind": "video",
        # There is never a fixed sample to point at - each Flow job's own output is
        # its sample, found by whichever ran most recently.
        "find": lambda: _glob(RENDER_ROOT, "flow/*.mp4"),
        "sample_at": 0.5,
        "sample_len": 4.0,
    },
]


def _remotion_sample() -> Path | None:
    """Most recent studio-rendered template, else the local validation render
    (remotion-videos/out is gitignored, so a fresh clone has no sample until
    the first render)."""
    rendered = (
        sorted((RENDER_ROOT / "remotion").glob("*.mp4"))
        if (RENDER_ROOT / "remotion").exists()
        else []
    )
    fallback = (
        Path(__file__).resolve().parents[2]
        / "remotion-videos"
        / "out"
        / "payoff-validate.mp4"
    )
    return _first([*rendered, fallback])


def _montage_clip() -> Path | None:
    """First montage act whose cached result still points at a real file."""
    import json

    for d in (
        RENDER_ROOT / "ltx25-optionscity-firsttrade60-preview",
        RENDER_ROOT / "ltx25-optionscity-firsttrade60",
    ):
        if not d.exists():
            continue
        for result in sorted(d.glob("0*_result.json")):
            try:
                p = Path(json.loads(result.read_text()).get("video_path", ""))
            except Exception:  # noqa: BLE001
                continue
            if p.is_file():
                return p
    return None


def _first(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.is_file():
            return p
    return None


def _glob(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    hits = sorted(root.glob(pattern))
    return hits[0] if hits else None


def _proxy(src: Path, at: float, length: float) -> Path | None:
    """A small, low-bitrate, muted preview. Deliberately cheap to load."""
    key = f"{abs(hash((str(src), at, length, int(src.stat().st_mtime))))}.mp4"
    out = PROXY_DIR / key
    if out.is_file():
        return out
    r = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            str(at),
            "-t",
            str(length),
            "-i",
            str(src),
            "-an",
            "-vf",
            "scale=384:-2,fps=15",
            "-c:v",
            "libx264",
            "-crf",
            "34",
            "-preset",
            "veryfast",
            "-movflags",
            "+faststart",
            "-y",
            str(out),
        ],
        capture_output=True,
    )
    return out if out.is_file() and r.returncode == 0 else None


def build() -> list[dict[str, Any]]:
    entries = []
    for kind in KINDS:
        src = kind["find"]()
        entry = {k: v for k, v in kind.items() if k != "find"}
        entry["available"] = src is not None
        entry["source"] = str(src) if src else None
        entry["proxy"] = None
        if src and kind["kind"] == "video":
            proxy = _proxy(src, kind.get("sample_at", 1.0), kind.get("sample_len", 4.0))
            entry["proxy"] = str(proxy) if proxy else None
        elif src:
            entry["proxy"] = str(src)
        if not src:
            entry["why"] = "no sample yet — run the job to make one"
        entries.append(entry)
    return entries
