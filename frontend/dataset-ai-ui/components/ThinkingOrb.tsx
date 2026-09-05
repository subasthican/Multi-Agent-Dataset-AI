"use client";

import { useEffect, useRef } from "react";

interface ThinkingOrbProps {
  /** Dot color, any valid CSS color string. */
  color: string;
  /** Canvas size in CSS px (square). */
  size?: number;
  /** Faster spin + full brightness while the stage is actively running. */
  active?: boolean;
  /** Faded, near-static — the stage hasn't started yet. */
  dimmed?: boolean;
}

const DOT_COUNT = 70;
// A fixed camera tilt so the sphere reads as 3D even before it starts
// spinning, rather than looking like a flat disc of dots face-on.
const PITCH = 0.4;

/** Points evenly distributed over a unit sphere via the Fibonacci-sphere
 * method — cheap, and avoids the pole-clustering a naive lat/long grid gets. */
function fibonacciSphere(count: number): [number, number, number][] {
  const points: [number, number, number][] = [];
  const offset = 2 / count;
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < count; i++) {
    const y = i * offset - 1 + offset / 2;
    const r = Math.sqrt(Math.max(0, 1 - y * y));
    const phi = i * goldenAngle;
    points.push([Math.cos(phi) * r, y, Math.sin(phi) * r]);
  }
  return points;
}

/** A small rotating point-cloud sphere — the "thinking orb" look (à la
 * MetalForge's thinking-orbs/crystal effect), reimplemented from scratch on
 * canvas since the original is an interactive, sign-in-gated editor rather
 * than something embeddable. Depth (z) drives both size and opacity so the
 * far side of the sphere visibly recedes instead of every dot looking flat. */
export default function ThinkingOrb({ color, size = 32, active = false, dimmed = false }: ThinkingOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pointsRef = useRef(fibonacciSphere(DOT_COUNT));
  const angleRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const radius = size * 0.4;
    const center = size / 2;
    const cosP = Math.cos(PITCH);
    const sinP = Math.sin(PITCH);
    const spinSpeed = active ? 0.025 : 0.008;

    let rafId: number;

    function render() {
      ctx!.clearRect(0, 0, size, size);
      const cosA = Math.cos(angleRef.current);
      const sinA = Math.sin(angleRef.current);

      const projected = pointsRef.current.map(([x, y, z]) => {
        const x1 = x * cosA + z * sinA;
        const z1 = z * cosA - x * sinA;
        const y1 = y * cosP - z1 * sinP;
        const z2 = y * sinP + z1 * cosP;
        return { x: x1, y: y1, z: z2 };
      });

      // Painter's algorithm: draw back-to-front so near dots sit on top.
      projected.sort((a, b) => a.z - b.z);

      for (const p of projected) {
        const depth = (p.z + 1) / 2; // 0 (far) .. 1 (near)
        const dotRadius = Math.max(0.5, 1.5 * (0.45 + depth * 0.85));
        const alpha = (dimmed ? 0.3 : 0.85) * (0.2 + depth * 0.8);
        ctx!.globalAlpha = alpha;
        ctx!.fillStyle = color;
        ctx!.beginPath();
        ctx!.arc(center + p.x * radius, center + p.y * radius, dotRadius, 0, Math.PI * 2);
        ctx!.fill();
      }
      ctx!.globalAlpha = 1;

      if (!reduceMotion) {
        angleRef.current += spinSpeed;
        rafId = requestAnimationFrame(render);
      }
    }

    render();
    return () => cancelAnimationFrame(rafId);
  }, [size, color, active, dimmed]);

  return <canvas ref={canvasRef} style={{ width: size, height: size }} aria-hidden />;
}
