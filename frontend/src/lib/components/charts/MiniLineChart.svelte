<script lang="ts">
  interface LineDatum {
    label: string;
    value: number;
  }

  let {
    data = [],
    height = 64,
    color = 'var(--accent)',
    showDots = true,
    showArea = true,
    formatValue,
    yMin,
    yMax,
  }: {
    data: LineDatum[];
    height?: number;
    color?: string;
    showDots?: boolean;
    showArea?: boolean;
    formatValue?: (v: number) => string;
    yMin?: number;
    yMax?: number;
  } = $props();

  const PAD = 6;

  const validData = $derived(data.filter((d) => d.value > 0));
  const hasData = $derived(validData.length >= 2);

  const computedMin = $derived(yMin ?? Math.min(...validData.map((d) => d.value)));
  const computedMax = $derived(yMax ?? Math.max(...validData.map((d) => d.value)));
  const range = $derived(computedMax - computedMin || 1);

  const W = 280;

  const points = $derived(
    data.map((d, i) => ({
      x: PAD + (data.length > 1 ? (i / (data.length - 1)) * (W - PAD * 2) : (W - PAD * 2) / 2),
      y: d.value > 0
        ? height - PAD - ((d.value - computedMin) / range) * (height - PAD * 2)
        : height - PAD,
      value: d.value,
      label: d.label,
      hasValue: d.value > 0,
    }))
  );

  const linePath = $derived.by(() => {
    const valid = points.filter((p) => p.hasValue);
    if (valid.length < 2) return '';
    return 'M ' + valid.map((p) => `${p.x},${p.y}`).join(' L ');
  });

  const areaPath = $derived.by(() => {
    const valid = points.filter((p) => p.hasValue);
    if (valid.length < 2) return '';
    const bottom = height - PAD;
    return `M ${valid[0].x},${bottom} L ` +
      valid.map((p) => `${p.x},${p.y}`).join(' L ') +
      ` L ${valid[valid.length - 1].x},${bottom} Z`;
  });

  let hoveredIndex = $state<number | null>(null);
</script>

{#if hasData}
  <div class="mini-line-chart" style="--line-color: {color}">
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <svg
      viewBox="0 0 {W} {height}"
      style="height: {height}px"
      onmouseleave={() => hoveredIndex = null}
    >
      {#if showArea && areaPath}
        <path d={areaPath} fill="url(#area-grad)" />
        <defs>
          <linearGradient id="area-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="var(--line-color)" stop-opacity="0.12" />
            <stop offset="100%" stop-color="var(--line-color)" stop-opacity="0.02" />
          </linearGradient>
        </defs>
      {/if}
      {#if linePath}
        <path d={linePath} fill="none" stroke="var(--line-color)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      {/if}
      {#if showDots}
        {#each points as pt, i}
          {#if pt.hasValue}
            <circle
              cx={pt.x}
              cy={pt.y}
              r={hoveredIndex === i ? 4 : 2.5}
              fill="var(--line-color)"
              class="line-dot"
              onmouseenter={() => hoveredIndex = i}
            />
          {/if}
        {/each}
      {/if}
      {#each points as pt, i}
        {#if pt.hasValue}
          <rect
            x={pt.x - 14}
            y="0"
            width="28"
            height={height}
            fill="transparent"
            onmouseenter={() => hoveredIndex = i}
          />
        {/if}
      {/each}
    </svg>

    <div class="line-labels">
      {#if data.length > 0}
        <span class="line-label">{data[0].label}</span>
        {#if hoveredIndex !== null && formatValue}
          <span class="line-hover-value">{formatValue(points[hoveredIndex].value)}</span>
        {/if}
        <span class="line-label" style="margin-left: auto">{data[data.length - 1].label}</span>
      {/if}
    </div>
  </div>
{:else}
  <div class="line-empty" style="height: {height}px">
    <span class="line-empty-text">Not enough data yet</span>
  </div>
{/if}

<style>
  .mini-line-chart {
    width: 100%;
  }

  svg {
    width: 100%;
    display: block;
  }

  .line-dot {
    transition: r 0.15s ease;
  }

  .line-labels {
    display: flex;
    align-items: center;
    margin-top: 4px;
    position: relative;
  }

  .line-label {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-tertiary);
  }

  .line-hover-value {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-secondary);
    font-weight: 500;
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
  }

  .line-empty {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .line-empty-text {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-tertiary);
  }
</style>
