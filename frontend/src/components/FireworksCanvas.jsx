/**
 * FireworksCanvas.jsx — High-energy arcade fireworks particle explosion canvas.
 * Triggers particle bursts when active, scaling density with score!
 */
import React, { useEffect, useRef } from 'react';

export default function FireworksCanvas({ active, level, points }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!active) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let animationFrameId;
    let particles = [];

    // Resize canvas to cover window
    const width = (canvas.width = window.innerWidth);
    const height = (canvas.height = window.innerHeight);

    // Number of fireworks bursts & particle density scaling with points / level
    const burstCount = points >= 300 ? 12 : points >= 200 ? 7 : points >= 100 ? 4 : 2;
    const particlesPerBurst = points >= 300 ? 40 : points >= 200 ? 28 : 18;

    const colors = [
      '#ff007f', '#00f2ff', '#ffcc00', '#00ff88',
      '#b026ff', '#ff5e00', '#ffffff', '#ff0055', '#33ffff'
    ];

    // Create fireworks bursts across upper screen
    for (let b = 0; b < burstCount; b++) {
      const burstDelay = b * 120; // Staggered explosion timing
      setTimeout(() => {
        const startX = (width * 0.1) + Math.random() * (width * 0.8);
        const startY = (height * 0.15) + Math.random() * (height * 0.45);

        for (let i = 0; i < particlesPerBurst; i++) {
          const angle = Math.random() * Math.PI * 2;
          const speed = 2 + Math.random() * (points >= 300 ? 11 : 7);
          particles.push({
            x: startX,
            y: startY,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            color: colors[Math.floor(Math.random() * colors.length)],
            size: 3 + Math.random() * (points >= 300 ? 6 : 4),
            alpha: 1,
            decay: 0.008 + Math.random() * 0.012,
            gravity: 0.12,
          });
        }
      }, burstDelay);
    }

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.vy += p.gravity;
        p.alpha -= p.decay;

        if (p.alpha <= 0) {
          particles.splice(i, 1);
          continue;
        }

        ctx.save();
        ctx.globalAlpha = p.alpha;
        ctx.fillStyle = p.color;
        ctx.shadowBlur = 14;
        ctx.shadowColor = p.color;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      if (particles.length > 0 || active) {
        animationFrameId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [active, level, points]);

  if (!active) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        pointerEvents: 'none',
        zIndex: 9999,
      }}
    />
  );
}
