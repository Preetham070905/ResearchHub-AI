/**
 * ConfidenceGauge — Circular SVG meter (0–100)
 * Red < 40, Yellow 40-70, Green > 70
 * Appears at the bottom of each analysis report.
 */
import { useState } from 'react';

interface Props {
    score: number;
    size?: number;
    label?: string;
}

export default function ConfidenceGauge({ score, size = 120, label = 'Confidence' }: Props) {
    const [showTooltip, setShowTooltip] = useState(false);

    const radius = (size - 16) / 2;
    const circumference = 2 * Math.PI * radius;
    const clamped = Math.max(0, Math.min(100, score));
    const offset = circumference - (clamped / 100) * circumference;

    const color = clamped < 40 ? '#ef4444' : clamped < 70 ? '#f59e0b' : '#22c55e';
    const bg = clamped < 40 ? '#fef2f2' : clamped < 70 ? '#fffbeb' : '#f0fdf4';
    const levelLabel = clamped < 40 ? 'Low' : clamped < 70 ? 'Moderate' : 'High';

    return (
        <div
            style={{ position: 'relative', display: 'inline-flex', flexDirection: 'column', alignItems: 'center' }}
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
        >
            <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
                {/* Background circle */}
                <circle
                    cx={size / 2} cy={size / 2} r={radius}
                    fill="none" stroke="#e5e7eb" strokeWidth={8}
                />
                {/* Progress arc */}
                <circle
                    cx={size / 2} cy={size / 2} r={radius}
                    fill="none" stroke={color} strokeWidth={8}
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    strokeLinecap="round"
                    style={{ transition: 'stroke-dashoffset 1s ease' }}
                />
            </svg>

            {/* Centre label */}
            <div style={{
                position: 'absolute', top: 0, left: 0, width: size, height: size,
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            }}>
                <span style={{ fontSize: size * 0.28, fontWeight: 800, color }}>{Math.round(clamped)}</span>
                <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{levelLabel}</span>
            </div>

            <span style={{ fontSize: 11, fontWeight: 600, marginTop: 4, color: 'var(--text-body)' }}>{label}</span>

            {/* Tooltip */}
            {showTooltip && (
                <div style={{
                    position: 'absolute', bottom: -50, left: '50%', transform: 'translateX(-50%)',
                    background: '#1f2937', color: '#fff', padding: '6px 12px', borderRadius: 6,
                    fontSize: 11, whiteSpace: 'nowrap', zIndex: 100, lineHeight: 1.4,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                }}>
                    <strong>Confidence: {Math.round(clamped)}%</strong><br />
                    Based on paper count, source diversity,<br />
                    and agent agreement level.
                    <div style={{
                        position: 'absolute', top: -4, left: '50%', transform: 'translateX(-50%) rotate(45deg)',
                        width: 8, height: 8, background: '#1f2937',
                    }} />
                </div>
            )}
        </div>
    );
}
