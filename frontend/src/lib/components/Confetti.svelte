<script lang="ts">
  let { trigger = false }: { trigger: boolean } = $props();

  let canvas: HTMLCanvasElement;
  let particles: Array<{
    x: number;
    y: number;
    vx: number;
    vy: number;
    color: string;
    size: number;
    rotation: number;
    rotSpeed: number;
    life: number;
  }> = [];
  let animId: number | null = null;
  let hasTriggered = false;

  const colors = ['#2eaadc', '#3dba80', '#e8c84a', '#e07070', '#b07cc6', '#ff8533'];

  function spawnConfetti() {
    const w = window.innerWidth;
    for (let i = 0; i < 80; i++) {
      particles.push({
        x: w / 2 + (Math.random() - 0.5) * w * 0.6,
        y: window.innerHeight * 0.4 + Math.random() * 100,
        vx: (Math.random() - 0.5) * 8,
        vy: -Math.random() * 12 - 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        size: Math.random() * 6 + 3,
        rotation: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 0.2,
        life: 1
      });
    }
    animate();
  }

  function animate() {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let alive = false;
    for (const p of particles) {
      p.vy += 0.25;
      p.x += p.vx;
      p.y += p.vy;
      p.rotation += p.rotSpeed;
      p.life -= 0.008;
      if (p.life <= 0) continue;
      alive = true;

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rotation);
      ctx.globalAlpha = Math.min(1, p.life * 2);
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
      ctx.restore();
    }

    if (alive) {
      animId = requestAnimationFrame(animate);
    } else {
      particles = [];
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  $effect(() => {
    if (trigger && !hasTriggered) {
      hasTriggered = true;
      spawnConfetti();
    }
    return () => {
      if (animId) cancelAnimationFrame(animId);
    };
  });
</script>

<canvas bind:this={canvas} class="confetti-canvas"></canvas>

<style>
  .confetti-canvas {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 999;
  }
</style>
