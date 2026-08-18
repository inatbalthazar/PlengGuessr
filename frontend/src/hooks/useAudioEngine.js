/**
 * useAudioEngine — Web Audio API engine for SongGuessr.
 *
 * Design:
 *  - Loads all 4 stems into AudioBuffers (in parallel).
 *  - Syncs playback by starting all BufferSources at the same time.
 *  - Mute/unmute via GainNode with 50 ms smooth ramp.
 *  - Pause stores offset; resume creates new nodes from that offset.
 */
import { useState, useRef, useCallback, useEffect } from 'react';

const STEMS = ['drums', 'bass', 'other', 'vocals'];
const INITIAL_MUTED = { drums: false, bass: true, other: true, vocals: true };

export function useAudioEngine() {
  const [isLoading,  setIsLoading]  = useState(false);
  const [loadError,  setLoadError]  = useState(null);
  const [isPlaying,  setIsPlaying]  = useState(false);
  const [songLoaded, setSongLoaded] = useState(false);
  const [mutedStems, setMutedStems] = useState(INITIAL_MUTED);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(30);

  // Refs — stable across renders, no stale closure risk
  const ctxRef      = useRef(null);
  const buffers     = useRef({});   // stem → AudioBuffer
  const sources     = useRef({});   // stem → AudioBufferSourceNode
  const gains       = useRef({});   // stem → GainNode
  const startedAt   = useRef(0);    // ctx.currentTime when last play() called
  const pausedAt    = useRef(0);    // audio offset (s) when paused
  const rafRef      = useRef(null);
  const mutedRef    = useRef(INITIAL_MUTED);
  const durationRef = useRef(30);

  // Keep refs in sync with state
  useEffect(() => { mutedRef.current = mutedStems; }, [mutedStems]);
  useEffect(() => { durationRef.current = duration; }, [duration]);

  // ------------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------------
  const getCtx = useCallback(() => {
    if (!ctxRef.current) {
      ctxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    return ctxRef.current;
  }, []);

  const stopSources = useCallback(() => {
    STEMS.forEach(stem => { try { sources.current[stem]?.stop(); } catch {} });
    sources.current = {};
    gains.current   = {};
  }, []);

  const stopRAF = useCallback(() => {
    if (rafRef.current) { cancelAnimationFrame(rafRef.current); rafRef.current = null; }
  }, []);

  // ------------------------------------------------------------------
  // Load song (fetch + decode all stems in parallel)
  // ------------------------------------------------------------------
  const loadSong = useCallback(async (song) => {
    stopSources();
    stopRAF();
    setIsPlaying(false);
    setCurrentTime(0);
    setSongLoaded(false);
    setIsLoading(true);
    setLoadError(null);
    setMutedStems(INITIAL_MUTED);
    pausedAt.current = 0;
    buffers.current  = {};

    const ctx = getCtx();

    try {
      await Promise.all(STEMS.map(async (stem) => {
        const url = song.stems[stem];
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Cannot fetch stem: ${stem} (${res.status})`);
        const ab  = await res.arrayBuffer();
        const buf = await ctx.decodeAudioData(ab);
        buffers.current[stem] = buf;
      }));

      // Use the longest buffer as duration
      const dur = Math.max(...Object.values(buffers.current).map(b => b.duration));
      setDuration(dur);
      setIsLoading(false);
      setSongLoaded(true);
    } catch (err) {
      setLoadError(`โหลดเสียงไม่สำเร็จ: ${err.message}`);
      setIsLoading(false);
    }
  }, [getCtx, stopSources, stopRAF]);

  // ------------------------------------------------------------------
  // Internal playback starter
  // ------------------------------------------------------------------
  const startPlayback = useCallback((offset) => {
    const ctx = getCtx();
    if (ctx.state === 'suspended') ctx.resume();

    stopSources();

    STEMS.forEach(stem => {
      const buf = buffers.current[stem];
      if (!buf) return;

      const src  = ctx.createBufferSource();
      src.buffer = buf;

      const gain = ctx.createGain();
      gain.gain.value = mutedRef.current[stem] ? 0 : 1;

      src.connect(gain);
      gain.connect(ctx.destination);
      src.start(0, Math.min(offset, buf.duration - 0.01));

      sources.current[stem] = src;
      gains.current[stem]   = gain;

      src.onended = () => {
        if (sources.current[stem] === src) {
          // Track ended naturally
          stopRAF();
          setIsPlaying(false);
          setCurrentTime(durationRef.current);
          pausedAt.current = 0;
        }
      };
    });

    startedAt.current = ctx.currentTime;
    setIsPlaying(true);

    const tick = () => {
      const ctx2 = ctxRef.current;
      if (!ctx2) return;
      const elapsed = ctx2.currentTime - startedAt.current + offset;
      setCurrentTime(Math.min(elapsed, durationRef.current));
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, [getCtx, stopSources, stopRAF]);

  // ------------------------------------------------------------------
  // Public controls
  // ------------------------------------------------------------------
  const play = useCallback(() => {
    if (!songLoaded) return;
    startPlayback(pausedAt.current);
  }, [songLoaded, startPlayback]);

  const pause = useCallback(() => {
    if (!isPlaying) return;
    const ctx = ctxRef.current;
    const elapsed = ctx
      ? ctx.currentTime - startedAt.current + pausedAt.current
      : pausedAt.current;
    pausedAt.current = Math.max(0, elapsed);
    stopSources();
    stopRAF();
    setIsPlaying(false);
  }, [isPlaying, stopSources, stopRAF]);

  const reset = useCallback(() => {
    stopSources();
    stopRAF();
    setIsPlaying(false);
    setCurrentTime(0);
    pausedAt.current = 0;
    setMutedStems(INITIAL_MUTED);
  }, [stopSources, stopRAF]);

  const toggleMute = useCallback((stem) => {
    setMutedStems(prev => {
      const muted   = !prev[stem];
      const newState = { ...prev, [stem]: muted };

      // Smooth gain transition (50 ms)
      const gain = gains.current[stem];
      if (gain && ctxRef.current) {
        gain.gain.setTargetAtTime(muted ? 0 : 1, ctxRef.current.currentTime, 0.05);
      }

      return newState;
    });
  }, []);

  const unmuteAll = useCallback(() => {
    const allOpen = { drums: false, bass: false, other: false, vocals: false };
    setMutedStems(allOpen);
    STEMS.forEach(stem => {
      const gain = gains.current[stem];
      if (gain && ctxRef.current) {
        gain.gain.setTargetAtTime(1, ctxRef.current.currentTime, 0.05);
      }
    });
  }, []);

  return {
    isLoading, loadError,
    isPlaying, songLoaded,
    mutedStems, currentTime, duration,
    loadSong, play, pause, reset,
    toggleMute, unmuteAll,
  };
}
