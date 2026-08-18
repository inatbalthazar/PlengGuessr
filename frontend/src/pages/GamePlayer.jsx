/**
 * GamePlayer.jsx — Host & Player Interactive Game Screen.
 *
 * Features:
 *  - Playlist / Quiz Category Selector
 *  - Song selection & random next song
 *  - 4 StemCards (Bass 1st, Drums 2nd, Other 3rd, Vocals 4th)
 *  - Interactive Guess Input with Fuzzy / Partial Keyword Matcher
 *  - Dynamic Score & Cheer System based on unmuted stems count:
 *      * 1 Stem (Bass only): 3 Stars (+300 pts) + Max Confetti & Loud Celebration!
 *      * 2 Stems: 2 Stars (+200 pts) + Medium Celebration
 *      * 3 Stems: 1 Star (+100 pts) + Normal Cheer
 *      * 4 Stems (Vocals on): +50 pts + Mild/Subtle Cheer ("ยินดีด้วยเบาๆ")
 *  - Scoreboard / Streak counter
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import StemCard from '../components/StemCard';
import FireworksCanvas from '../components/FireworksCanvas';
import { useAudioEngine } from '../hooks/useAudioEngine';
import { ChevronDown, Trophy, Sparkles, CheckCircle2, XCircle, Flame, HelpCircle } from 'lucide-react';

const STEM_ORDER = ['bass', 'drums', 'other', 'vocals'];

function fmt(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

function normalizeStr(str) {
  if (!str) return '';
  return str
    .toLowerCase()
    .replace(/\(.*?\)|\[.*?\]/g, '') // remove (feat...), [MV]
    .replace(/[^a-z0-9ก-๙]/gi, '')   // keep English, Numbers, Thai, Korean
    .trim();
}

function isFuzzyMatch(userInput, targetTitle, targetArtist) {
  if (!userInput || !userInput.trim()) return false;
  const userNorm = normalizeStr(userInput);
  const titleNorm = normalizeStr(targetTitle);
  const artistNorm = normalizeStr(targetArtist);
  const fullNorm = normalizeStr(`${targetArtist} ${targetTitle}`);

  if (!userNorm || userNorm.length < 2) return false;

  // 1. Exact or Substring match
  if (titleNorm === userNorm || fullNorm === userNorm) return true;
  if (titleNorm.includes(userNorm) || userNorm.includes(titleNorm)) return true;

  // 2. Keyword overlap match
  const userWords = userInput.toLowerCase().split(/\s+/).map(w => normalizeStr(w)).filter(w => w.length >= 2);
  const titleWords = targetTitle.toLowerCase().split(/\s+/).map(w => normalizeStr(w)).filter(w => w.length >= 2);

  if (userWords.length > 0 && titleWords.length > 0) {
    const matchedCount = userWords.filter(uw => titleWords.some(tw => tw.includes(uw) || uw.includes(tw))).length;
    if (matchedCount / titleWords.length >= 0.4 || (titleWords.length === 1 && matchedCount >= 1)) {
      return true;
    }
  }

  return false;
}

export default function GamePlayer() {
  // ---- Songs & Playlists data -------------------------------------------
  const [allSongs, setAllSongs] = useState([]);
  const [playlists, setPlaylists] = useState([]);
  const [selectedPlaylistId, setSelectedPlaylistId] = useState('all-songs');
  const [loadingData, setLoadingData] = useState(true);

  // ---- Game session state -----------------------------------------------
  const [selectedId, setSelectedId] = useState('');
  const [revealed, setRevealed] = useState(false);
  const [guessInput, setGuessInput] = useState('');
  const [guessResult, setGuessResult] = useState(null); // { success: boolean, points: number, cheerText: string, cheerSubtext: string, level: string }
  const [totalScore, setTotalScore] = useState(0);
  const [streak, setStreak] = useState(0);

  const {
    isLoading, loadError,
    isPlaying, songLoaded,
    mutedStems, currentTime, duration,
    loadSong, play, pause, reset,
    toggleMute, unmuteAll,
  } = useAudioEngine();

  // ---- Load songs & playlists -------------------------------------------
  useEffect(() => {
    Promise.all([
      fetch('/api/songs').then(r => r.json()),
      fetch('/api/custom-playlists').then(r => r.json()),
    ])
      .then(([songsData, playlistsData]) => {
        setAllSongs(songsData || []);
        setPlaylists(playlistsData || []);
        setLoadingData(false);
      })
      .catch(() => setLoadingData(false));
  }, []);

  // Filter songs based on selected playlist
  const availableSongs = useMemo(() => {
    if (selectedPlaylistId === 'all-songs') return allSongs;
    const currentP = playlists.find(p => p.id === selectedPlaylistId);
    if (!currentP || !currentP.song_ids || currentP.song_ids.length === 0) return allSongs;
    return allSongs.filter(s => currentP.song_ids.includes(s.id));
  }, [allSongs, playlists, selectedPlaylistId]);

  const selectedSong = availableSongs.find(s => s.id === selectedId) || allSongs.find(s => s.id === selectedId);

  // ---- Song selection ---------------------------------------------------
  const handleSelectSong = useCallback(async (id) => {
    setSelectedId(id);
    setRevealed(false);
    setGuessInput('');
    setGuessResult(null);
    if (!id) return;
    const song = allSongs.find(s => s.id === id);
    if (song) await loadSong(song);
  }, [allSongs, loadSong]);

  const handleNextRandomSong = useCallback(() => {
    if (availableSongs.length === 0) return;
    const unplayed = availableSongs.filter(s => s.id !== selectedId);
    const pool = unplayed.length > 0 ? unplayed : availableSongs;
    const rand = pool[Math.floor(Math.random() * pool.length)];
    if (rand) handleSelectSong(rand.id);
  }, [availableSongs, selectedId, handleSelectSong]);

  // ---- Game actions -----------------------------------------------------
  const handleReveal = useCallback(() => {
    setRevealed(true);
    unmuteAll();
  }, [unmuteAll]);

  const handleReset = useCallback(() => {
    reset();
    setRevealed(false);
    setGuessInput('');
    setGuessResult(null);
  }, [reset]);

  const handlePlayPause = useCallback(() => {
    if (isPlaying) pause(); else play();
  }, [isPlaying, play, pause]);

  // ---- Guess Submission & Dynamic Cheer Calculation ---------------------
  const handleGuessSubmit = (e) => {
    e.preventDefault();
    if (!selectedSong || revealed || !guessInput.trim()) return;

    const matched = isFuzzyMatch(guessInput, selectedSong.title, selectedSong.artist);

    if (matched) {
      // Calculate cheer level based on unmuted stems
      const unmutedCount = STEM_ORDER.filter(stem => !mutedStems[stem]).length;
      let pts = 0;
      let stars = 0;
      let cheerText = '';
      let cheerSubtext = '';
      let level = 'subtle';

      if (unmutedCount <= 1) { // Bass only!
        pts = 300;
        stars = 3;
        cheerText = '🌟🌟🌟 PERFECT! ทายถูกด้วยเสียงเบสอย่างเดียว!';
        cheerSubtext = 'สุดยอดเทพสมองเพชร! ฟังแค่เสียงเบสชิ้นเดียวก็ทายถูกเลย! 🎉🔥💥';
        level = 'max';
      } else if (unmutedCount === 2) {
        pts = 200;
        stars = 2;
        cheerText = '⭐️⭐️ GREAT! ทายถูกด้วยดนตรี 2 ชิ้น!';
        cheerSubtext = 'เก่งมากๆ! เปิดฟังแค่ 2 ชิ้นเครื่องดนตรีก็เอาอยู่แล้ว 👏✨';
        level = 'medium';
      } else if (unmutedCount === 3) {
        pts = 100;
        stars = 1;
        cheerText = '⭐️ GOOD! ทายถูกต้อง!';
        cheerSubtext = 'เยี่ยมเลย! ทายชื่อเพลงถูกต้องเรียบร้อย 👍';
        level = 'normal';
      } else { // 4 stems (Vocals included)
        pts = 50;
        stars = 0;
        cheerText = '🙂 NICE! ทายถูกต้องแล้วนะ';
        cheerSubtext = 'ยินดีด้วยเบาๆ ~ เปิดเสียงร้องช่วยแล้วทายถูกจนได้!';
        level = 'subtle';
      }

      setTotalScore(prev => prev + pts);
      setStreak(prev => prev + 1);
      setGuessResult({
        success: true,
        points: pts,
        stars,
        cheerText,
        cheerSubtext,
        level,
      });
      setRevealed(true);
      unmuteAll();
    } else {
      setGuessResult({
        success: false,
        cheerText: '❌ ยังไม่ถูกต้อง ลองใหม่อีกครั้ง!',
        cheerSubtext: 'ลองเปิดเสียงเพิ่ม หรือทายด้วยคำอื่นดูสิ!',
        level: 'none',
      });
    }
  };

  // ---- Keyboard shortcuts -----------------------------------------------
  useEffect(() => {
    const onKey = (e) => {
      const tag = e.target.tagName;
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;

      switch (e.key) {
        case ' ':
          e.preventDefault();
          if (songLoaded) handlePlayPause();
          break;
        case '1': toggleMute('bass');   break;
        case '2': toggleMute('drums');  break;
        case '3': toggleMute('other');  break;
        case '4': toggleMute('vocals'); break;
        case 'r': case 'R': handleReset();  break;
        case 'Enter':
          e.preventDefault();
          if (songLoaded && !revealed) handleReveal();
          break;
      }
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [songLoaded, handlePlayPause, toggleMute, handleReset, handleReveal, revealed]);

  const progress = duration > 0 ? Math.min((currentTime / duration) * 100, 100) : 0;

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', paddingBottom: '3rem' }}>
      {/* Explosive Fireworks Effect when Correct */}
      <FireworksCanvas
        active={revealed && !!guessResult?.success}
        level={guessResult?.level}
        points={guessResult?.points || 0}
      />

      {/* Top Header & Scoreboard */}
      <div className="page-header" style={{ position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 className="page-title" style={{ margin: 0 }}>🎵 PlengGuessr</h1>
            <p className="page-subtitle" style={{ margin: 0 }}>ทายเพลงจากเครื่องดนตรี — ทายยิ่งไว ยิ่งได้ดาวเยอะ!</p>
          </div>

          {/* Score Badge */}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <div className="badge-score" style={{ background: 'rgba(99, 102, 241, 0.2)', border: '1px solid var(--primary-light)', padding: '0.5rem 1rem', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Trophy size={18} color="gold" />
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>คะแนนรวม</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--primary-light)' }}>{totalScore}</div>
              </div>
            </div>

            <div className="badge-streak" style={{ background: 'rgba(245, 158, 11, 0.2)', border: '1px solid #f59e0b', padding: '0.5rem 1rem', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Flame size={18} color="#f59e0b" />
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>ต่อเนื่อง</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f59e0b' }}>{streak} 🔥</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Category & Song Selector Card ──────────────────────────────── */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="form-row" style={{ alignItems: 'flex-end' }}>
          {/* Category / Playlist Dropdown */}
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">📋 เลือกหมวดหมู่ Quiz / Playlist</label>
            <div style={{ position: 'relative' }}>
              <select
                className="form-select"
                value={selectedPlaylistId}
                onChange={e => {
                  setSelectedPlaylistId(e.target.value);
                  setSelectedId('');
                  setRevealed(false);
                }}
                style={{ paddingRight: '2.25rem' }}
              >
                <option value="all-songs">🎵 รวมเพลงทั้งหมด ({allSongs.length} เพลง)</option>
                {playlists.filter(p => p.id !== 'all-songs').map(p => (
                  <option key={p.id} value={p.id}>
                    📋 {p.name} ({p.song_ids ? p.song_ids.length : allSongs.length} เพลง)
                  </option>
                ))}
              </select>
              <ChevronDown size={16} style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
            </div>
          </div>

          {/* Song Select Dropdown */}
          <div className="form-group" style={{ flex: 1.2 }}>
            <label className="form-label">🎼 เลือกเพลงข้อถัดไป</label>
            <div style={{ position: 'relative' }}>
              <select
                id="song-select"
                className="form-select"
                value={selectedId}
                onChange={e => handleSelectSong(e.target.value)}
                style={{ paddingRight: '2.25rem' }}
              >
                <option value="">— เลือกเพลงในหมวดนี้ —</option>
                {availableSongs.map(s => (
                  <option key={s.id} value={s.id}>
                    เพลงที่ #{availableSongs.indexOf(s) + 1} ({revealed && selectedId === s.id ? `${s.title} — ${s.artist}` : '❓ ซ่อนคำตอบ'})
                  </option>
                ))}
              </select>
              <ChevronDown size={16} style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
            </div>
          </div>

          {/* Random Next Song Button */}
          <div className="form-group" style={{ flex: 'none' }}>
            <button
              className="btn btn-primary"
              onClick={handleNextRandomSong}
              title="สุ่มเพลงถัดไป"
              style={{ height: '42px' }}
            >
              🎲 สุ่มเพลงถัดไป
            </button>
          </div>
        </div>
      </div>

      {/* ── Loading / Error State ───────────────────────────────── */}
      {isLoading && (
        <div style={{ textAlign: 'center', margin: '2.5rem 0' }}>
          <div className="spinner" style={{ margin: '0 auto 0.875rem' }} />
          <p style={{ color: 'var(--text-secondary)' }}>กำลังเตรียมเครื่องดนตรี แยก Stem เสียง...</p>
        </div>
      )}

      {loadError && (
        <div className="alert alert-error" style={{ maxWidth: 480, margin: '0 auto 1rem' }}>
          {loadError}
        </div>
      )}

      {/* ── Active Game View ────────────────────────────────────── */}
      {songLoaded && !isLoading && (
        <>
          {/* Vinyl Disc Animation */}
          <div className="vinyl-container">
            <div className={`vinyl-disc ${isPlaying ? 'playing' : ''}`}>
              <div className="vinyl-center-hole" />
              {selectedSong?.cover_url ? (
                <img
                  src={selectedSong.cover_url}
                  alt="Album Cover"
                  className="vinyl-cover-blur"
                  style={{ filter: revealed ? 'none' : 'blur(14px) brightness(0.5)' }}
                />
              ) : (
                <span style={{ fontSize: '2rem' }}>🎵</span>
              )}
            </div>
          </div>

          {/* Stem Cards — Bass is 1st Card! */}
          <div className="stems-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            {STEM_ORDER.map(stem => (
              <StemCard
                key={stem}
                stem={stem}
                muted={mutedStems[stem]}
                onToggle={toggleMute}
              />
            ))}
          </div>

          {/* Progress Bar & Audio Time */}
          <div style={{ maxWidth: 580, margin: '0 auto 1.5rem' }}>
            <div className="progress-wrap">
              <div className="progress-fill" style={{ transform: `scaleX(${progress / 100})` }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
              <span>{fmt(currentTime)}</span>
              <span>{fmt(duration)}</span>
            </div>
          </div>

          {/* Playback Controls */}
          <div className="controls" style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '2rem' }}>
            <button id="btn-reset" className="btn btn-secondary" onClick={handleReset} title="R — รีเซ็ต">
              ↺ รีเซ็ต
            </button>

            <button
              id="btn-play-pause"
              className="btn btn-primary btn-lg"
              onClick={handlePlayPause}
              style={{ minWidth: 150 }}
              title="Space — เล่น/หยุด"
            >
              {isPlaying ? '⏸ หยุด' : '▶ เล่นเพลง'}
            </button>

            <button id="btn-unmute-all" className="btn btn-secondary" onClick={unmuteAll} title="เปิดเสียงทุก Stem">
              🔊 เปิดทั้งหมด
            </button>
          </div>

          {/* ── Interactive Guessing & Reveal Section ──────────────────────── */}
          <div className="card" style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '1.5rem', marginBottom: '2rem' }}>
            {!revealed ? (
              <form onSubmit={handleGuessSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <HelpCircle size={20} color="var(--primary-light)" />
                  <label className="form-label" style={{ margin: 0, fontSize: '1rem' }}>
                    พิมพ์คำตอบทายชื่อเพลง (หรือศิลปิน)
                  </label>
                </div>

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="พิมพ์ชื่อเพลงที่นี่ (พิมพ์แค่อ่างคำสำคัญก็ถูกได้)..."
                    value={guessInput}
                    onChange={e => setGuessInput(e.target.value)}
                    style={{ flex: 1, fontSize: '1.05rem', padding: '0.75rem 1rem' }}
                    autoFocus
                  />
                  <button type="submit" className="btn btn-primary btn-lg" style={{ padding: '0 1.75rem' }}>
                    🎯 ส่งคำตอบ
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={handleReveal}
                    title="ยอมแพ้ / เฉลยคำตอบ"
                  >
                    👁️ เฉลย
                  </button>
                </div>

                {guessResult && !guessResult.success && (
                  <div className="alert alert-error" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <XCircle size={18} />
                    <div>
                      <strong>{guessResult.cheerText}</strong>
                      <div style={{ fontSize: '0.85rem' }}>{guessResult.cheerSubtext}</div>
                    </div>
                  </div>
                )}
              </form>
            ) : (
              /* Answer Revealed View */
              <div style={{ textAlign: 'center', padding: '1rem 0' }}>
                {/* Dynamic Cheer Box */}
                {guessResult && guessResult.success && (
                  <div
                    style={{
                      background: guessResult.level === 'max'
                        ? 'linear-gradient(135deg, rgba(234,179,8,0.25), rgba(99,102,241,0.25))'
                        : guessResult.level === 'medium'
                        ? 'linear-gradient(135deg, rgba(34,197,94,0.2), rgba(99,102,241,0.2))'
                        : 'rgba(99,102,241,0.15)',
                      border: `2px solid ${
                        guessResult.level === 'max' ? '#eab308' : guessResult.level === 'medium' ? '#22c55e' : 'var(--primary-light)'
                      }`,
                      borderRadius: '16px',
                      padding: '1.25rem',
                      marginBottom: '1.25rem',
                      animation: 'pulseGlow 2s ease-in-out infinite',
                    }}
                  >
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.25rem' }}>
                      {guessResult.cheerText}
                    </div>
                    <div style={{ fontSize: '1rem', opacity: 0.9 }}>
                      {guessResult.cheerSubtext}
                    </div>
                    <div style={{ marginTop: '0.5rem', fontSize: '1.2rem', fontWeight: 700, color: 'gold' }}>
                      +{guessResult.points} คะแนน 🏆
                    </div>
                  </div>
                )}

                {selectedSong?.cover_url && (
                  <div className="album-cover-revealed">
                    <img
                      src={selectedSong.cover_url}
                      alt={selectedSong.title}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  </div>
                )}

                <p className="reveal-label" style={{ color: 'var(--text-muted)', margin: '0 0 0.25rem' }}>🏆 คำตอบที่ถูกต้องคือ...</p>
                <h2 className="reveal-title" style={{ fontSize: '2rem', margin: '0 0 0.25rem', color: 'var(--primary-light)' }}>
                  {selectedSong?.title}
                </h2>
                <p className="reveal-artist" style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', margin: '0 0 1.25rem' }}>
                  🎤 {selectedSong?.artist}
                </p>

                <button className="btn btn-success btn-lg" onClick={handleNextRandomSong}>
                  🎲 ลุยข้อถัดไป! ➔
                </button>
              </div>
            )}
          </div>

          {/* Keyboard Shortcuts Hint */}
          <div className="shortcuts" style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap', opacity: 0.8, fontSize: '0.8rem' }}>
            <div className="shortcut"><kbd className="kbd">Space</kbd> เล่น/หยุด</div>
            <div className="shortcut"><kbd className="kbd">1</kbd> เบส 🎸</div>
            <div className="shortcut"><kbd className="kbd">2</kbd> กลอง 🥁</div>
            <div className="shortcut"><kbd className="kbd">3</kbd> ดนตรี 🎹</div>
            <div className="shortcut"><kbd className="kbd">4</kbd> เสียงร้อง 🎤</div>
            <div className="shortcut"><kbd className="kbd">Enter</kbd> เฉลย</div>
            <div className="shortcut"><kbd className="kbd">R</kbd> รีเซ็ต</div>
          </div>
        </>
      )}

      {/* ── Empty State ─────────────────────────────────────────── */}
      {!selectedId && !isLoading && availableSongs.length > 0 && (
        <div className="empty-state" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
          <div className="empty-icon" style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>🎮</div>
          <p style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem' }}>พร้อมเริ่มทายเพลงแล้ว!</p>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            เลือกเพลงหรือกดสุ่มเพลงด้านบน แล้วลองกดเปิดฟังจาก **การ์ดเสียงเบส 🎸** เป็นอันดับแรก!
          </p>
          <button className="btn btn-primary btn-lg" onClick={handleNextRandomSong}>
            🎲 เริ่มสุ่มเพลงแรกเลย!
          </button>
        </div>
      )}
    </div>
  );
}
