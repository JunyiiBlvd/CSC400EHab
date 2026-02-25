"use client";

export type SparkPoint = {
  t: number;     // time in ms since epoch (Date.now())
  v: number;     // value
};

export default function Sparkline({
  points,
  width = 220,
  height = 40,
}: {
  points: SparkPoint[];
  width?: number;
  height?: number;
}) {
  if (points.length < 2) return null;

  const minV = Math.min(...points.map(p => p.v));
  const maxV = Math.max(...points.map(p => p.v));
  const rangeV = maxV - minV || 1;

  const minT = Math.min(...points.map(p => p.t));
  const maxT = Math.max(...points.map(p => p.t));
  const rangeT = maxT - minT || 1;

  const coords = points.map((p) => {
    const x = ((p.t - minT) / rangeT) * width;
    const y = height - ((p.v - minV) / rangeV) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  return (
    <svg width={width} height={height} style={{ display: "block", marginTop: 6 }}>
      <polyline
        fill="none"
        stroke="white"
        strokeOpacity={0.6}
        strokeWidth={2}
        points={coords.join(" ")}
      />
    </svg>
  );
}
