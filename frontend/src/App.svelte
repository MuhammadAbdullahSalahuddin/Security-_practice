<script>
  import { fade } from 'svelte/transition';
  import { page } from './store.js';
  import Home from './pages/Home.svelte';
  import ModeSelect from './pages/ModeSelect.svelte';
  import Exam from './pages/Exam.svelte';
  import Results from './pages/Results.svelte';
</script>

<main class="min-h-screen">
  {#if $page === 'home'}
    <div transition:fade={{ duration: 180 }}>
      <Home />
    </div>
  {:else if $page === 'mode_select'}
    <div transition:fade={{ duration: 180 }}>
      <ModeSelect />
    </div>
  {:else if $page === 'exam'}
    <div transition:fade={{ duration: 180 }}>
      <Exam />
    </div>
  {:else if $page === 'results'}
    <div transition:fade={{ duration: 180 }}>
      <Results />
    </div>
  {/if}
</main>
