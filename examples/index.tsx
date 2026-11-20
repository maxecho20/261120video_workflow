import {AbsoluteFill, Audio, Composition, OffthreadVideo, Sequence, interpolate, registerRoot, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Event = {id: string; type: 'lyric' | 'cue' | 'scene'; start_frame: number; end_frame?: number; text?: string};
type MusicProps = {events: Event[]};

const textStyle = {fontFamily: 'PingFang SC, Arial, sans-serif'};
const cover = {width: '100%', height: '100%', objectFit: 'cover'} as const;
const audio = () => staticFile('repro-demo/score.wav');
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

const TalkDemo = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{...textStyle, backgroundColor: '#14232d', color: 'white'}}>
      <AbsoluteFill style={{left: 230, width: 730}}>
        <OffthreadVideo src={staticFile('repro-demo/speaker.mp4')} muted style={cover} />
      </AbsoluteFill>
      <Sequence from={24} durationInFrames={108}>
        <div style={{position: 'absolute', left: 35, top: 36, width: 302, height: 174, border: '4px solid #fff', borderRadius: 14, overflow: 'hidden'}}>
          <OffthreadVideo src={staticFile('repro-demo/example.mp4')} muted style={cover} />
        </div>
      </Sequence>
      <div style={{position: 'absolute', left: 36, top: 230, fontSize: 24}}>B-roll 角窗示例</div>
      <div style={{position: 'absolute', bottom: 40, left: 200, right: 40, textAlign: 'center', fontSize: 38, background: '#132027e8', padding: 14}}>
        {frame < 90 ? '以主轨保留讲述顺序' : '让示例对上讲到的内容'}
      </div>
      <Audio src={audio()} volume={0.25} />
    </AbsoluteFill>
  );
};

const products = [
  {year: '节点 A', title: '把用途集中到一台设备', color: '#006d77', tiles: ['通讯', '媒体', '网络']},
  {year: '节点 B', title: '让第三方扩展用途', color: '#b0532c', tiles: ['导航', '游戏', '创作', '工具']},
];

const ProductDemo = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const index = Math.min(1, Math.floor(frame / 90));
  const page = products[index];
  const lift = spring({frame: frame - index * 90, fps, config: {damping: 18}});
  return (
    <AbsoluteFill style={{...textStyle, background: '#f4f0e5', color: '#213036', justifyContent: 'center', padding: '0 72px'}}>
      <div style={{fontSize: 22, color: page.color}}>{page.year}</div>
      <div style={{width: 405, marginTop: 16, fontSize: 51, fontWeight: 700}}>{page.title}</div>
      <div style={{position: 'absolute', right: 120, top: 95, width: 240, height: 350, borderRadius: 30, padding: 25, background: page.color, color: 'white', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, transform: `translateY(${interpolate(lift, [0, 1], [55, 0], clamp)}px)`}}>
        {page.tiles.map(tile => <div key={tile} style={{display: 'grid', placeItems: 'center', background: '#ffffff32', borderRadius: 12, fontSize: 20}}>{tile}</div>)}
      </div>
      <Audio src={audio()} volume={0.55} />
    </AbsoluteFill>
  );
};

const MusicDemo = ({events}: MusicProps) => {
  const frame = useCurrentFrame();
  const cue = events.find(event => event.type === 'cue')?.start_frame ?? 90;
  const lyric = events.find(event => event.type === 'lyric' && event.start_frame <= frame && frame < (event.end_frame ?? 0));
  const room = frame >= cue;
  return (
    <AbsoluteFill style={{...textStyle, background: room ? '#f7ca83' : '#94b6bf', color: '#283844', overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: '18%', top: 100, width: 280, height: 300, border: '16px solid #405764', background: room ? '#fff2c6' : '#9ab1dc', boxShadow: room ? '12px 15px #ca8b55' : '12px 15px #738b96'}} />
      <div style={{position: 'absolute', left: interpolate(frame, [0, cue], [568, 420], clamp), top: 290, width: 70, height: 100, background: '#b74e39', borderTop: '20px solid #29303b', boxShadow: '10px 8px #453c4b'}} />
      <div style={{position: 'absolute', bottom: 38, left: 0, width: '100%', textAlign: 'center', fontSize: 35}}>{lyric?.text}</div>
      <Audio src={audio()} volume={0.6} />
    </AbsoluteFill>
  );
};

const Root = () => (
  <>
    <Composition id="TalkDemo" component={TalkDemo} width={960} height={540} fps={30} durationInFrames={180} />
    <Composition id="ProductDemo" component={ProductDemo} width={960} height={540} fps={30} durationInFrames={180} />
    <Composition
      id="MusicDemo" component={MusicDemo} width={960} height={540} fps={30} durationInFrames={180}
      defaultProps={{events: []}}
      calculateMetadata={async () => {
        const response = await fetch(staticFile('repro-demo/mv-timeline.json'));
        if (!response.ok) throw new Error('请先生成音乐样例时间表');
        const {events, fps, duration_in_frames} = await response.json();
        return {props: {events}, fps, durationInFrames: duration_in_frames};
      }}
    />
  </>
);

registerRoot(Root);
