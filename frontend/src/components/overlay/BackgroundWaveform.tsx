import React, { useEffect, useRef } from "react";

interface BackgroundWaveformProps {
  /** Color of the wave lines */
  color?: string;
  /** 0–1 intensity, controls amplitude */
  intensity?: number;
  /** Number of wave layers */
  layers?: number;
}

/**
 * Canvas-based animated sine wave background.
 * Renders multiple translucent sine layers that flow across the pill width.
 */
export const BackgroundWaveform: React.FC<BackgroundWaveformProps> = ({
  color = "rgba(251, 146, 60, 1)",
  intensity = 0.85,
  layers = 3,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const tRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Parse the color into r,g,b so we can control alpha per layer
    // color is expected as "rgba(r,g,b,1)" or "rgb(r,g,b)"
    const parseColor = (c: string) => {
      const m = c.match(/[\d.]+/g);
      if (!m || m.length < 3) return { r: 251, g: 146, b: 60 };
      return { r: Number(m[0]), g: Number(m[1]), b: Number(m[2]) };
    };
    const { r, g, b } = parseColor(color);

    const layerConfigs = [
      { amp: 9 * intensity,  speed: 0.022, freq: 1.6,  alpha: 0.22, yOffset: 0.6 },
      { amp: 6 * intensity,  speed: 0.034, freq: 2.3,  alpha: 0.14, yOffset: 0.5 },
      { amp: 11 * intensity, speed: 0.016, freq: 1.1,  alpha: 0.10, yOffset: 0.55 },
    ].slice(0, layers);

    const draw = () => {
      const W = canvas.width;
      const H = canvas.height;
      ctx.clearRect(0, 0, W, H);

      tRef.current += 1;

      layerConfigs.forEach((cfg, li) => {
        ctx.beginPath();
        const phaseShift = li * (Math.PI * 0.6);
        const baseline = H * cfg.yOffset;

        for (let x = 0; x <= W; x += 2) {
          const y =
            baseline +
            Math.sin((x / W) * Math.PI * 2 * cfg.freq + tRef.current * cfg.speed + phaseShift) *
              cfg.amp +
            Math.sin((x / W) * Math.PI * 3.7 * cfg.freq + tRef.current * cfg.speed * 1.3 + phaseShift * 1.5) *
              (cfg.amp * 0.4);
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }

        ctx.strokeStyle = `rgba(${r},${g},${b},${cfg.alpha})`;
        ctx.lineWidth = li === 0 ? 1.5 : 1;
        ctx.stroke();
      });

      animRef.current = requestAnimationFrame(draw);
    };

    const resize = () => {
      if (!canvas.parentElement) return;
      canvas.width = canvas.parentElement.offsetWidth;
      canvas.height = canvas.parentElement.offsetHeight;
    };

    resize();
    draw();
    window.addEventListener("resize", resize);

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [color, intensity, layers]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 0,
        borderRadius: "9999px",
      }}
    />
  );
};
