import {useMemo} from 'react';
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type Word = {word: string; start: number; end: number};
type Caption = {segment_id: number; text: string; start: number; end: number; words: Word[]};
export type AlignedCaptions = {total_duration: number; captions: Caption[]};

type Shot = {
  segment_id: number;
  match_text: string;
  shot_type: string;
  camera_scale: number[];
  b_roll_asset: string | null;
  start_s?: number;
  end_s?: number;
  info_card: {title: string; subtitle: string} | null;
  highlight_keywords: string[];
};

export type MainVideoProps = {
  src: string;
  aligned: AlignedCaptions;
  storyboard: {video_title: string; fps: number; width: number; height: number; segments: Shot[]};
};

const normalize = (text: string) => text.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const cover = {width: '100%', height: '100%', objectFit: 'cover'} as const;

function matchShots(shots: Shot[], captions: Caption[]) {
  const planned: {shot: Shot; start: number; end: number}[] = [];
  let nextCaption = 0;
  for (const [index, shot] of shots.entries()) {
    const {start_s: start, end_s: end} = shot;
    if (start !== undefined && end !== undefined && Number.isFinite(start) && Number.isFinite(end) && start >= 0 && end > start) {
      planned.push({shot, start, end});
      continue;
    }
    if (index === 0 && shot.shot_type === 'A-roll_zoom_hook') {
      planned.push({shot, start: 0, end: 3});
      continue;
    }
    const match = normalize(shot.match_text);
    const captionIndex = captions.findIndex((caption, i) =>
      i >= nextCaption && caption.start >= 3 && match.length > 0 &&
      normalize(caption.text).includes(match),
    );
    if (captionIndex >= 0) {
      const start = captions[captionIndex].start;
      planned.push({shot, start, end: start + 6});
      nextCaption = captionIndex + 1;
    }
  }
  return planned.map((entry, index) => ({
    ...entry,
    end: Math.min(entry.end, planned[index + 1]?.start ?? Infinity),
  }));
}

function keywordWords(words: Word[], keywords: string[]) {
  const tokens = words.map(({word}) => normalize(word));
  const text = tokens.join('');
  const matches: [number, number][] = [];
  for (const keyword of keywords.map(normalize).filter(Boolean)) {
    for (let start = text.indexOf(keyword); start >= 0; start = text.indexOf(keyword, start + 1)) {
      matches.push([start, start + keyword.length]);
    }
  }
  let cursor = 0;
  return tokens.map((token) => {
    const start = cursor;
    cursor += token.length;
    return token.length > 0 && matches.some(([from, to]) => start < to && cursor > from);
  });
}

export const MainVideo = ({src, aligned, storyboard}: MainVideoProps) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const currentTime = frame / fps;
  const activeCaption = aligned.captions.find(({start, end}) => currentTime >= start && currentTime < end);
  const shots = useMemo(
    () => matchShots(storyboard.segments, aligned.captions),
    [storyboard.segments, aligned.captions],
  );
  const activeShot = shots.find(({start, end}) => currentTime >= start && currentTime < end);
  const shot = activeShot?.shot;
  const words = activeCaption?.words ?? [];
  const highlights = keywordWords(words, shot?.highlight_keywords ?? []);
  const isEmphasis = shot?.shot_type === 'A-roll_zoom_hook' || shot?.shot_type === 'keyword_card';

  const shotFrame = frame - Math.floor((activeShot?.start ?? 0) * fps);
  const captionFrame = frame - Math.floor((activeCaption?.start ?? 0) * fps);
  const shotSpring = spring({frame: shotFrame, fps, config: {damping: 14, stiffness: 120}});
  const zoomSpring = isEmphasis
    ? shotSpring
    : spring({frame: captionFrame, fps, config: {damping: 14, stiffness: 120}});
  const breathe = interpolate(frame % (12 * fps), [0, 6 * fps, 12 * fps], [1, 1.04, 1], clamp);
  const scale = isEmphasis || highlights.includes(true)
    ? interpolate(zoomSpring, [0, 1], [shot?.camera_scale[0] ?? 1, 1.14], clamp)
    : activeShot && shot?.camera_scale.length === 2
      ? interpolate(shotFrame, [0, Math.max(1, (activeShot.end - activeShot.start) * fps)], shot.camera_scale, clamp)
      : breathe;

  const card = shot?.info_card;
  const cardDuration = Math.min(2.8, (activeShot?.end ?? 0) - (activeShot?.start ?? 0));
  const cardOpacity = card && cardDuration > 0
    ? Math.min(
        interpolate(shotSpring, [0, 1], [0, 1], clamp),
        interpolate(shotFrame / fps, [cardDuration - 0.25, cardDuration], [1, 0], clamp),
      )
    : 0;

  const bRoll = activeShot?.shot.shot_type === 'B-roll_overlay' && activeShot.shot.b_roll_asset;
  const bRollStart = Math.ceil((activeShot?.start ?? 0) * fps);
  const bRollEnd = Math.min(durationInFrames, Math.ceil((activeShot?.end ?? 0) * fps));
  const bRollSrc = bRoll && staticFile('assets/' + bRoll.replace(/^assets\//, ''));

  return (
    <AbsoluteFill style={{backgroundColor: '#0a0a0c', overflow: 'hidden', fontFamily: 'PingFang SC, sans-serif'}}>
      <AbsoluteFill style={{
        transform: `scale(${scale})`,
        filter: `brightness(${1 - 0.28 * cardOpacity}) blur(${3 * cardOpacity}px)`,
      }}>
        <OffthreadVideo src={src} style={cover} />
        {bRollSrc && bRollEnd > bRollStart && (
          <Sequence from={bRollStart} durationInFrames={bRollEnd - bRollStart}>
            {/\.(avif|gif|jpe?g|png|webp)$/i.test(bRollSrc)
              ? <Img src={bRollSrc} style={cover} />
              : <OffthreadVideo src={bRollSrc} style={cover} muted />}
          </Sequence>
        )}
      </AbsoluteFill>

      <AbsoluteFill style={{
        background: 'linear-gradient(to top, rgba(0,0,0,0.82) 0%, rgba(0,0,0,0) 35%)',
        pointerEvents: 'none',
      }} />

      {card && cardOpacity > 0 && (
        <div style={{
          position: 'absolute',
          top: '14%',
          left: '8%',
          right: shot.shot_type === 'A-roll_zoom_hook' ? '8%' : undefined,
          maxWidth: '84%',
          padding: '28px 36px',
          boxSizing: 'border-box',
          borderRadius: 24,
          background: 'rgba(20, 24, 36, 0.78)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.18)',
          boxShadow: '0 24px 48px rgba(0, 0, 0, 0.45)',
          transform: `translateY(${interpolate(shotSpring, [0, 1], [40, 0], clamp)}px)`,
          opacity: cardOpacity,
        }}>
          <div style={{color: '#00F5D4', fontSize: 30, fontWeight: 700, marginBottom: 8}}>
            {card.subtitle}
          </div>
          <div style={{color: '#FFFFFF', fontSize: 52, fontWeight: 900, letterSpacing: 1}}>
            {card.title}
          </div>
        </div>
      )}

      {activeCaption && (
        <div style={{
          position: 'absolute',
          bottom: '12%',
          left: '6%',
          right: '6%',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignItems: 'baseline',
          gap: 6,
          textAlign: 'center',
          color: '#FFFFFF',
          fontSize: 52,
          fontWeight: 900,
          textShadow: '0 4px 16px rgba(0,0,0,0.85)',
        }}>
          {words.length === 0 && activeCaption.text}
          {words.map((word, index) => {
            const speaking = currentTime >= word.start && currentTime <= word.end + 0.12;
            const keyword = highlights[index];
            const pop = speaking ? spring({
              frame: Math.max(0, frame - Math.floor(word.start * fps)),
              fps,
              config: {damping: 10, stiffness: 220},
            }) : 0;
            return (
              <span key={index} style={{
                display: 'inline-block',
                fontSize: keyword ? 60 : 52,
                color: keyword ? '#FFD700' : speaking ? '#00F5D4' : '#FFFFFF',
                transform: `scale(${interpolate(pop, [0, 1], [1, keyword ? 1.28 : 1.14])})`,
                padding: '0 2px',
              }}>
                {word.word}
              </span>
            );
          })}
        </div>
      )}
    </AbsoluteFill>
  );
};
