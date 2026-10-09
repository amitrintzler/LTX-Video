# hyperframes toolchain

Pinned HyperFrames CLI and GSAP used by `stages/renderers/hyperframes.py`.

    cd video-pipeline/hyperframes && npm ci

Needs Node 22+ and ffmpeg. `node_modules/` is git-ignored; the renderer looks for
`node_modules/.bin/hyperframes` and copies `node_modules/gsap/dist/gsap.min.js`
into every temporary project it builds.
