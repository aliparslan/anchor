<script lang="ts">
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import MitInput from '$lib/components/MitInput.svelte';
	import TodoList from '$lib/components/TodoList.svelte';
</script>

<PageHeader title="Todos" />

<div class="home-section">
	<SectionHeader title="Priority" />
	<MitInput />
</div>

<div class="home-section">
	<SectionHeader title="Tasks" />
	<TodoList />
</div>
