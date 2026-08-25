"use client";

import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Stars } from "@react-three/drei";
import type { Group } from "three";

function RotatingLayer({
  rotationSpeed,
  parallax,
  children,
}: {
  rotationSpeed: number;
  parallax: number;
  children: React.ReactNode;
}) {
  const group = useRef<Group>(null);

  useFrame((state, delta) => {
    if (!group.current) return;
    group.current.rotation.y += delta * rotationSpeed;
    group.current.rotation.x += delta * rotationSpeed * 0.4;

    // Gentle parallax toward the pointer for an interactive, premium feel.
    const targetX = state.pointer.y * parallax;
    const targetY = state.pointer.x * parallax;
    group.current.rotation.x += (targetX - group.current.rotation.x) * 0.02;
    group.current.rotation.y += (targetY - group.current.rotation.y) * 0.02;
  });

  return <group ref={group}>{children}</group>;
}

export default function GalaxyBackground() {
  return (
    // z-index stays negative and page wrappers stay z-index-free (auto): that
    // keeps every wrapper out of the positioned/z-index paint bucket, so
    // normal in-flow page content — painted before positioned descendants at
    // any given stacking level — naturally lands above this fixed layer with
    // no explicit z-index tug-of-war. (An earlier attempt gave the content
    // wrapper `z-10`, which made it establish its own stacking context and
    // put this positioned z-0 canvas ABOVE the plain in-flow text inside it —
    // don't add z-index back to those wrappers without re-checking this.)
    <div
      className="pointer-events-none fixed inset-0 -z-10"
      style={{
        background: "radial-gradient(circle at 20% 10%, #1b1645 0%, #050510 45%, #030308 100%)",
      }}
    >
      <Canvas camera={{ position: [0, 0, 1] }}>
        <RotatingLayer rotationSpeed={0.015} parallax={0.15}>
          <Stars radius={60} depth={60} count={5000} factor={4} saturation={0} fade speed={1.2} />
        </RotatingLayer>
        <RotatingLayer rotationSpeed={0.035} parallax={0.3}>
          <Stars radius={30} depth={40} count={1500} factor={5} saturation={0} fade speed={2} />
        </RotatingLayer>
      </Canvas>
    </div>
  );
}
