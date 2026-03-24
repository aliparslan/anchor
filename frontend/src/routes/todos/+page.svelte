<script lang="ts">
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import MitInput from '$lib/components/MitInput.svelte';
	import TodoList from '$lib/components/TodoList.svelte';
</script>

<PageHeader title="Todos" />

<SectionHeader title="Priority" />
<MitInput />

<SectionHeader title="Tasks" style="margin-top: var(--space-section)" />
<TodoList />
