declare module 'animejs' {
  import type { AnimeInstance, AnimeParams } from 'animejs';
  export default function anime(params: AnimeParams | AnimeParams[]): AnimeInstance;
}
