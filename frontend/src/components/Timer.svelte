<script>
  import { onDestroy } from 'svelte';
  import { examStore } from '../store.js';

  export let endTime;

  let display = '02:00:00';
  let cls = 'text-[var(--green)]';

  const interval = setInterval(() => {
    const rem = Math.max(0, endTime - Date.now());
    const h = Math.floor(rem / 3600000);
    const m = Math.floor((rem % 3600000) / 60000);
    const s = Math.floor((rem % 60000) / 1000);
    display = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;

    if (rem > 1800000)     cls = 'text-[var(--green)]';
    else if (rem > 300000) cls = 'text-[var(--amber)]';
    else                   cls = 'text-[var(--red)] animate-pulse';
  }, 500);

  onDestroy(() => clearInterval(interval));
</script>

<div class="font-mono text-2xl tracking-widest text-center py-2 px-3 rounded-lg border border-[var(--border)] bg-[var(--elevated)] {cls}">
  {display}
</div>
