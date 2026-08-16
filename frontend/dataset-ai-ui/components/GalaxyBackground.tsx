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
    <div className="fixed inset-0 -z-10 pointer-events-none">
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
