<script lang="ts">
	const haikus = [
		["An old silent pond", "A frog jumps into the pond—", "Splash! Silence again."],
		["Over the wintry", "forest, winds howl in rage", "with no leaves to blow."],
		["In the twilight rain", "these brilliant-hued hibiscus—", "a lovely sunset."],
		["Light of the moon", "moves west, flowers' shadows", "creep eastward."],
		["The lamp once out", "cool stars enter", "the window frame."],
		["No one travels", "along this way but I,", "this autumn evening."],
		["From time to time", "the clouds give rest", "to the moon-beholders."],
		["In the moonlight,", "the color and scent of the", "wisteria seems far away."],
		["A summer river being crossed", "how pleasing", "with sandals in my hands!"],
		["Temple bells die out.", "The fragrant blossoms remain.", "A perfect evening!"],
		["The old pond—", "a frog jumps in,", "sound of water."],
		["Autumn moonlight—", "a worm digs silently", "into the chestnut."],
		["First autumn morning:", "the mirror I stare into", "shows my father's face."],
		["A caterpillar,", "this deep in fall—", "still not a butterfly."],
		["Blowing from the west,", "fallen leaves gather", "in the east."],
		["On a withered branch", "a crow has alighted—", "nightfall in autumn."],
		["You say one word", "and lips are chilled", "by autumn wind."],
		["Everything I touch", "with tenderness, alas,", "pricks like a bramble."],
		["Even in Kyoto—", "hearing the cuckoo's cry—", "I long for Kyoto."],
		["The sea at springtime.", "All day it rises and falls,", "yes, rises and falls."],
		["Toward those short trees", "we saw a hawk descending", "on a day in spring."],
		["As the spring rains fall,", "soaking in them, on the roof,", "is a child's rag ball."],
		["My life—", "how much more of it remains?", "The night is brief."],
		["Come, see", "real flowers", "of this painful world."],
		["Don't weep, insects—", "lovers, stars themselves,", "must part."],
		["The wind from Mt. Fuji", "I put on the fan.", "A gift from Edo."],
		["In this world", "we walk on the roof of hell", "gazing at flowers."],
		["A lovely thing to see:", "through the paper window's hole,", "the Galaxy."],
		["Wrapping the rice cakes,", "with one hand", "she fingers back her hair."],
		["The moon above the pines:", "I keep hanging it there—", "gazing each moment."]
	];

	const dayOfYear = Math.floor(
		(Date.now() - new Date(new Date().getFullYear(), 0, 0).getTime()) / 86400000
	);
	const haiku = haikus[dayOfYear % haikus.length];
</script>

<div class="zen">
	<div class="zen-content">
		{#each haiku as line}
			<p class="zen-line">{line}</p>
		{/each}
	</div>
</div>

<style>
	.zen {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 48px 24px;
		background: var(--bg);
		color: var(--text);
	}

	.zen-content {
		text-align: center;
		max-width: 320px;
	}

	.zen-line {
		font-family: var(--font-display);
		font-size: 18px;
		font-weight: 400;
		line-height: 2;
		color: var(--text-secondary);
		letter-spacing: 0.01em;
	}

	.zen-line:first-child {
		color: var(--text);
	}

	:global(.bottom-nav),
	:global(.capture-fab),
	:global(.app) {
		display: none !important;
	}
</style>
