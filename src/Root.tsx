import {ALL_FORMATS, Input, UrlSource} from 'mediabunny';
import {Composition, staticFile} from 'remotion';
import type {CalculateMetadataFunction} from 'remotion';
import storyboard from '../public/storyboard.json';
import {MainVideo} from './MainVideo';
import type {AlignedCaptions, MainVideoProps} from './MainVideo';

const calculateMetadata: CalculateMetadataFunction<MainVideoProps> = async ({abortSignal}) => {
  const src = staticFile('rough_cut.mp4');
  const response = await fetch(staticFile('aligned_captions.json'), {signal: abortSignal});
  if (!response.ok) {
    throw new Error('无法读取 public/aligned_captions.json，请先运行 Stage 3。');
  }
  const aligned: AlignedCaptions = await response.json();
  const input = new Input({formats: ALL_FORMATS, source: new UrlSource(src)});
  try {
    const video = await input.getPrimaryVideoTrack();
    if (!video) {
      throw new Error('public/rough_cut.mp4 缺少视频轨，请重新运行 Stage 3。');
    }
    const duration = await video.computeDuration();
    return {
      durationInFrames: Math.max(1, Math.ceil(duration * storyboard.fps)),
      props: {src, aligned, storyboard},
    };
  } finally {
    input.dispose();
  }
};

export const Root = () => (
  <Composition
    id="MainVideo"
    component={MainVideo}
    fps={storyboard.fps}
    width={storyboard.width}
    height={storyboard.height}
    durationInFrames={1}
    defaultProps={{src: '', aligned: {total_duration: 0, captions: []}, storyboard}}
    calculateMetadata={calculateMetadata}
  />
);
