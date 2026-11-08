import {Config} from '@remotion/cli/config';

// JPEG frames render faster; the final encode is H.264 either way.
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
