#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import http from "node:http";
import path from "node:path";

const repoRoot = path.resolve(new URL("..", import.meta.url).pathname);
const scriptPath = path.join(
  repoRoot,
  "video-pipeline/scripts/ltx23-masterpiece-creation.json",
);
const source = JSON.parse(readFileSync(scriptPath, "utf8"));
const outRoot = "/tmp/ltx23-masterpiece";
const storyboardDir = path.join(outRoot, "storyboards");
const frameRoot = path.join(outRoot, "frames");
const clipDir = path.join(outRoot, "clips");
const audioDir = path.join(outRoot, "audio");
const outputDir = path.join(outRoot, "output");
for (const dir of [storyboardDir, frameRoot, clipDir, audioDir, outputDir]) {
  mkdirSync(dir, { recursive: true });
}

const host = "127.0.0.1";
const port = 7859;
const width = 1024;
const height = 576;
const fps = 24;
const frames = 97;

function postJson(endpoint, payload) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(payload);
    const req = http.request(
      {
        hostname: host,
        port,
        path: endpoint,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
        },
        timeout: 0,
      },
      (res) => {
        let data = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => {
          data += chunk;
        });
        res.on("end", () => resolve({ status: res.statusCode, text: data }));
      },
    );
    req.on("error", reject);
    req.setTimeout(0);
    req.end(body);
  });
}

function run(cmd, args) {
  execFileSync(cmd, args, { stdio: "inherit" });
}

function scenePath(dir, index, ext) {
  return path.join(dir, `scene_${String(index + 1).padStart(3, "0")}.${ext}`);
}

async function generateStoryboard(scene, index) {
  const outPath = scenePath(storyboardDir, index, "png");
  if (existsSync(outPath)) {
    console.log(`storyboard ${index + 1}: reuse ${outPath}`);
    return outPath;
  }

  const prompt = [
    scene.storyboard_prompt,
    scene.style,
    source.global_style,
    "masterpiece composition, crisp details, sharp focus, high quality",
  ]
    .filter(Boolean)
    .join(", ");
  const payload = {
    prompt,
    negative_prompt:
      "blurry, soft focus, smear, low quality, watermark, text, letters, subtitles, distorted hands, deformed objects, flicker",
    width,
    height,
    steps: 6,
    guidance_scale: 1,
    seed: -1,
    batch_size: 1,
    model: "flux_1_schnell_q8p.ckpt",
    sampler_name: "DPM++ 2M Karras",
  };
  console.log(`storyboard ${index + 1}: request`);
  const res = await postJson("/sdapi/v1/txt2img", payload);
  if (res.status < 200 || res.status >= 300) {
    throw new Error(`storyboard ${index + 1} failed: ${res.text}`);
  }
  const data = JSON.parse(res.text);
  if (!data.images?.length) {
    throw new Error(`storyboard ${index + 1} returned no image`);
  }
  writeFileSync(outPath, Buffer.from(data.images[0], "base64"));
  console.log(`storyboard ${index + 1}: wrote ${outPath}`);
  return outPath;
}

async function generateClip(scene, index, storyboardPath) {
  const outPath = scenePath(clipDir, index, "mp4");
  if (existsSync(outPath)) {
    console.log(`clip ${index + 1}: reuse ${outPath}`);
    return outPath;
  }

  const sceneFrames = path.join(frameRoot, `scene_${String(index + 1).padStart(3, "0")}`);
  mkdirSync(sceneFrames, { recursive: true });
  const prompt = [
    scene.camera,
    scene.video_prompt,
    scene.motion,
    scene.style,
    "high quality LTX 2.3 video, crisp detail, stable geometry, no blur, no jitter",
  ]
    .filter(Boolean)
    .join(", ");
  const payload = {
    prompt,
    negative_prompt:
      "text, watermark, blurry, soft focus, motion smear, jitter, flicker, warped objects, distorted hands, duplicate fingers, deformed brush, bad motion",
    init_images: [readFileSync(storyboardPath, "base64")],
    width,
    height,
    steps: 8,
    guidance_scale: 1.0,
    seed: -1,
    denoising_strength: 0.78,
    num_frames: frames,
    fps,
    model: "ltx_2.3_22b_distilled_q6p.ckpt",
    sampler_name: "TCD Trailing",
    shift: 5,
    resolution_dependent_shift: true,
    tea_cache: true,
  };
  console.log(`clip ${index + 1}: request LTX 2.3`);
  const res = await postJson("/sdapi/v1/img2img", payload);
  if (res.status < 200 || res.status >= 300) {
    throw new Error(`clip ${index + 1} failed: ${res.text}`);
  }
  const data = JSON.parse(res.text);
  if (!data.images?.length) {
    throw new Error(`clip ${index + 1} returned no frames`);
  }
  data.images.forEach((b64, frameIndex) => {
    writeFileSync(
      path.join(sceneFrames, `frame_${String(frameIndex).padStart(6, "0")}.png`),
      Buffer.from(b64, "base64"),
    );
  });
  run("ffmpeg", [
    "-y",
    "-framerate",
    String(fps),
    "-i",
    path.join(sceneFrames, "frame_%06d.png"),
    "-c:v",
    "libx264",
    "-crf",
    "14",
    "-preset",
    "slow",
    "-pix_fmt",
    "yuv420p",
    outPath,
  ]);
  console.log(`clip ${index + 1}: wrote ${outPath}`);
  return outPath;
}

function makeAudio() {
  const audioPath = path.join(audioDir, "synced-score.m4a");
  if (existsSync(audioPath)) {
    return audioPath;
  }
  run("ffmpeg", [
    "-y",
    "-f",
    "lavfi",
    "-i",
    "anoisesrc=color=pink:duration=60:amplitude=0.025",
    "-f",
    "lavfi",
    "-i",
    "sine=frequency=82.41:duration=60:sample_rate=48000",
    "-f",
    "lavfi",
    "-i",
    "sine=frequency=164.81:duration=60:sample_rate=48000",
    "-f",
    "lavfi",
    "-i",
    "sine=frequency=246.94:duration=60:sample_rate=48000",
    "-filter_complex",
    "[0:a]lowpass=f=1800,highpass=f=70,volume=0.055,afade=t=in:st=0:d=2,afade=t=out:st=58:d=2[n];" +
      "[1:a]volume=0.03,afade=t=in:st=0:d=4,afade=t=out:st=56:d=4[bass];" +
      "[2:a]volume=0.022,afade=t=in:st=12:d=5,afade=t=out:st=56:d=4[mid];" +
      "[3:a]volume=0.014,afade=t=in:st=36:d=5,afade=t=out:st=57:d=3[high];" +
      "[n][bass][mid][high]amix=inputs=4:duration=longest:normalize=0,alimiter=limit=0.8[a]",
    "-map",
    "[a]",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    audioPath,
  ]);
  return audioPath;
}

function assemble(clips) {
  const listPath = path.join(outRoot, "clip-list.txt");
  const repeated = [];
  while (repeated.length < 15) {
    repeated.push(...clips);
  }
  writeFileSync(
    listPath,
    repeated
      .slice(0, 15)
      .map((clip) => `file '${clip.replaceAll("'", "'\\''")}'`)
      .join("\n") + "\n",
  );
  const silentPath = path.join(outputDir, "ltx23-masterpiece-silent.mp4");
  run("ffmpeg", [
    "-y",
    "-f",
    "concat",
    "-safe",
    "0",
    "-i",
    listPath,
    "-t",
    "60",
    "-c:v",
    "libx264",
    "-crf",
    "14",
    "-preset",
    "slow",
    "-pix_fmt",
    "yuv420p",
    "-movflags",
    "+faststart",
    silentPath,
  ]);
  const finalPath = path.join(outputDir, "ltx23-masterpiece-60s.mp4");
  run("ffmpeg", [
    "-y",
    "-i",
    silentPath,
    "-i",
    makeAudio(),
    "-map",
    "0:v",
    "-map",
    "1:a",
    "-c:v",
    "copy",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-shortest",
    "-movflags",
    "+faststart",
    finalPath,
  ]);
  return finalPath;
}

const storyboards = [];
for (let i = 0; i < source.scenes.length; i += 1) {
  storyboards.push(await generateStoryboard(source.scenes[i], i));
}

const clips = [];
for (let i = 0; i < source.scenes.length; i += 1) {
  clips.push(await generateClip(source.scenes[i], i, storyboards[i]));
}

const finalPath = assemble(clips);
console.log(`final ${finalPath}`);
