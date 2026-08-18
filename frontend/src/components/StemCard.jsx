/**
 * StemCard — individual instrument stem with mute/unmute toggle.
 * Uses CSS custom properties --stem-color and --stem-glow
 * so the parent's .unmuted class automatically applies the right glow.
 */
import React from 'react';

const CONFIG = {
  drums:  { icon: '🥁', label: 'Drums',  thai: 'กลอง',    color: 'var(--drums-color)',  glow: 'var(--drums-glow)'  },
  bass:   { icon: '🎸', label: 'Bass',   thai: 'เบส',      color: 'var(--bass-color)',   glow: 'var(--bass-glow)'   },
  other:  { icon: '🎹', label: 'Other',  thai: 'ดนตรี',    color: 'var(--other-color)',  glow: 'var(--other-glow)'  },
  vocals: { icon: '🎤', label: 'Vocals', thai: 'ร้อง',     color: 'var(--vocals-color)', glow: 'var(--vocals-glow)' },
};

export default function StemCard({ stem, muted, onToggle, disabled = false }) {
  const cfg = CONFIG[stem];
  if (!cfg) return null;

  return (
    <div
      id={`stem-card-${stem}`}
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label={`${muted ? 'เปิด' : 'ปิด'} ${cfg.thai}`}
      aria-pressed={!muted}
      className={`stem-card${muted ? '' : ' unmuted'}${disabled ? ' disabled' : ''}`}
      style={{ '--stem-color': cfg.color, '--stem-glow': cfg.glow }}
      onClick={disabled ? undefined : () => onToggle(stem)}
      onKeyDown={e => { if (!disabled && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onToggle(stem); } }}
    >
      <span className="stem-icon">{cfg.icon}</span>
      <span className="stem-label">{cfg.label}</span>
      <span className={`stem-badge ${muted ? 'off' : 'on'}`}>
        {muted ? '🔇 ปิด' : '🔊 เปิด'}
      </span>
    </div>
  );
}
