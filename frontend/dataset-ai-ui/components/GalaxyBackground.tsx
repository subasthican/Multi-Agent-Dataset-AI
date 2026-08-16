"use client";

import { Canvas } from "@react-three/fiber";
import { Stars } from "@react-three/drei";

export default function GalaxyBackground() {
  return (
    <div className="fixed inset-0 -z-10 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 1] }}>
        <Stars radius={50} depth={50} count={4000} factor={4} saturation={0} fade speed={0.6} />
        <Stars radius={80} depth={80} count={2000} factor={2} saturation={0} fade speed={0.3} />
      </Canvas>
    </div>
  );
}
