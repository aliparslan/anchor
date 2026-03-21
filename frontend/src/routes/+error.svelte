<script>
	import { page } from '$app/state';
</script>

<div class="error-page">
	<p>Something went wrong.</p>
	<a href="/">Go home</a>
</div>

<style>
	.error-page {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 80vh;
		gap: 16px;
		font-family: 'DM Sans', sans-serif;
		color: #6b6a66;
	}
	.error-page a {
		color: #1a1917;
		text-decoration: underline;
	}
</style>
