/**
 * SongTable — lists all songs with per-stem audio preview and delete button.
 */
import React, { useState, useRef } from 'react';

const STEMS = ['drums', 'bass', 'other', 'vocals'];

export default function SongTable({ songs, onDelete }) {
  const [playingKey, setPlayingKey] = useState(null);
  const audioRef = useRef(new Audio());

  const handlePreview = (url, key) => {
    if (playingKey === key) {
      audioRef.current.pause();
      setPlayingKey(null);
      return;
    }
    audioRef.current.pause();
    audioRef.current.src = url;
    audioRef.current.play().catch(() => {});
    setPlayingKey(key);
    audioRef.current.onended = () => setPlayingKey(null);
  };

  if (!songs?.length) {
    return (
      <div className="empty-state">
        <div className="empty-icon" style={{ animation: 'float 3s ease-in-out infinite' }}>🎵</div>
        <p style={{ fontWeight: 600, marginBottom: '0.375rem' }}>ยังไม่มีเพลง</p>
        <p style={{ fontSize: '0.85rem' }}>เพิ่มเพลงแรกด้วยฟอร์มด้านบน!</p>
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table className="tbl">
        <thead>
          <tr>
            <th style={{ width: 36 }}>#</th>
            <th style={{ width: 50 }}>ปก</th>
            <th>ชื่อเพลง</th>
            <th>ศิลปิน</th>
            <th>พรีวิว Stem</th>
            <th style={{ width: 80 }}>ลบ</th>
          </tr>
        </thead>
        <tbody>
          {songs.map((song, idx) => (
            <tr key={song.id}>
              <td style={{ color: 'var(--text-muted)' }}>{idx + 1}</td>
              <td>
                <div style={{
                  width: 40, height: 40, borderRadius: 8, overflow: 'hidden',
                  background: 'rgba(255, 255, 255, 0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  {song.cover_url ? (
                    <img
                      src={song.cover_url}
                      alt={song.title}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  ) : (
                    <span style={{ fontSize: '1.1rem' }}>🎵</span>
                  )}
                </div>
              </td>
              <td style={{ fontWeight: 600 }}>{song.title}</td>
              <td style={{ color: 'var(--text-secondary)' }}>{song.artist}</td>
              <td>
                <div className="stem-pills">
                  {STEMS.map(stem => {
                    const key = `${song.id}-${stem}`;
                    const playing = playingKey === key;
                    return (
                      <button
                        key={stem}
                        className={`stem-pill ${stem}`}
                        onClick={() => handlePreview(song.stems[stem], key)}
                        title={`${playing ? 'หยุด' : 'ฟัง'} ${stem}`}
                        aria-label={`${playing ? 'หยุดฟัง' : 'ฟัง'} ${stem} ของ ${song.title}`}
                      >
                        {playing ? '⏸' : '▶'} {stem}
                      </button>
                    );
                  })}
                </div>
              </td>
              <td>
                <button
                  id={`delete-${song.id}`}
                  className="btn btn-danger btn-sm"
                  onClick={() => onDelete(song.id)}
                  aria-label={`ลบ ${song.title}`}
                >
                  🗑️
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
