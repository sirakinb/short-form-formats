import React from 'react';
import {Composition, Still} from 'remotion';
import {COUNTER_END, Counter} from './compositions/Counter';
import {COVERS, Cover} from './compositions/Cover';
import {GAME_PARODY_END, GameParody} from './compositions/GameParody';
import {LISTICLE_END, Listicle} from './compositions/Listicle';
import {TALKING_HEAD_END, TalkingHead} from './compositions/TalkingHead';
import {loadBrandFonts} from './fonts';
import {FPS, H, W, s} from './theme';

loadBrandFonts();

// Set showSafeZone to true in the studio's props panel to see what platform UI will cover.
const video = {fps: FPS, width: W, height: H, defaultProps: {showSafeZone: false}};

export const Root: React.FC = () => (
  <>
    <Composition id="TalkingHead" component={TalkingHead} durationInFrames={s(TALKING_HEAD_END)} {...video} />
    <Composition id="Listicle" component={Listicle} durationInFrames={s(LISTICLE_END)} {...video} />
    <Composition id="Counter" component={Counter} durationInFrames={s(COUNTER_END)} {...video} />
    <Composition id="GameParody" component={GameParody} durationInFrames={s(GAME_PARODY_END)} {...video} />
    {COVERS.map((c) => <Still key={c.id} id={c.id} component={Cover} width={W} height={H} defaultProps={c.props} />)}
  </>
);
