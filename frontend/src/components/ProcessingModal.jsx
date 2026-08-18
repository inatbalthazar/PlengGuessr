/**
 * ProcessingModal — shown while the backend pipeline is running.
 * Displays animated spinner + progress bar, then success/error state.
 */
import React from 'react';

export default function ProcessingModal({ task, onClose }) {
  const isDone  = task?.status === 'done';
  const isError = task?.status === 'error';

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Processing status">
      <div className="modal-box">
        {isError ? (
          <>
            <div style={{ fontSize: '3rem' }}>❌</div>
            <h3 style={{ color: '#f87171' }}>เกิดข้อผิดพลาด</h3>
            <p style={{ wordBreak: 'break-word' }}>{task.error || 'ไม่ทราบสาเหตุ'}</p>
            <button className="btn btn-secondary" onClick={onClose}>ปิด</button>
          </>
        ) : isDone ? (
          <>
            <div style={{ fontSize: '3rem', animation: 'float 2.5s ease-in-out infinite' }}>🎉</div>
            <h3 style={{ color: '#34d399' }}>ประมวลผลสำเร็จ!</h3>
            <p style={{ fontSize: '1rem', margin: '0.5rem 0 1rem' }}>
              {task.song ? (
                <>
                  <strong style={{ color: 'var(--text-primary)' }}>{task.song.title}</strong>
                  {' — '}{task.song.artist}
                </>
              ) : (
                task.message || 'ดำเนินการเสร็จเรียบร้อยแล้ว'
              )}
            </p>
            <button className="btn btn-success" onClick={onClose}>ตกลง / ปิด</button>
          </>
        ) : (
          <>
            <div className="spinner" style={{ margin: '0 auto' }} />
            <h3 style={{ color: 'var(--text-primary)' }}>กำลังประมวลผล...</h3>
            <p>{task?.message || 'กรุณารอสักครู่'}</p>

            <div className="progress-wrap" style={{ margin: '0 0 0.5rem' }}>
              <div className="progress-fill" style={{ width: `${task?.progress ?? 0}%` }} />
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {task?.progress ?? 0}%
            </span>

            {task?.status === 'separating' && (
              <p style={{ marginTop: '0.875rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                💡 Demucs อาจใช้เวลา 2–10 นาที ขึ้นอยู่กับฮาร์ดแวร์
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
