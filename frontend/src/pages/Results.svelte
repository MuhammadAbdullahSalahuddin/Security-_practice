<script>
  import { fly } from 'svelte/transition';
  import { examStore } from '../store.js';

  $: results = $examStore.results;
  $: mode = $examStore.mode;
  $: pct = results?.percentage ?? 0;
  $: score = results?.score ?? 0;
  $: total = results?.total_questions ?? 0;
  $: passing = pct >= 85;
  $: details = (results?.details ?? []).slice().sort((a, b) => (a.displayNumber ?? a.question_number) - (b.displayNumber ?? b.question_number));

  let filter = 'all'; // 'all' | 'wrong' | 'correct'
  $: filtered = details.filter(d =>
    filter === 'all' ? true : filter === 'correct' ? d.is_correct : !d.is_correct
  );
</script>

<div class="max-w-2xl mx-auto px-6 py-12">
  <!-- Score summary -->
  <div in:fly={{ y: 20, duration: 300 }} class="card p-8 mb-8 text-center">
    <div class="font-mono text-[11px] tracking-widest text-[var(--muted)] uppercase mb-4">
      Exam Complete
    </div>

    <div class="text-6xl font-body font-semibold mb-1"
      style="color: {passing ? 'var(--green)' : 'var(--red)'}">
      {pct}%
    </div>
  {#if mode === 'exam'}
  <div class="font-ui font-medium text-lg mb-6"
    style="color: {passing ? 'var(--green)' : 'var(--red)'}">
    {passing ? 'PASS' : 'FAIL'}
  </div>
  {/if}

    <div class="flex justify-center gap-8">
      <div>
        <div class="font-mono text-2xl text-[var(--text)]">{score}</div>
        <div class="font-ui text-xs text-[var(--muted)]">Correct</div>
      </div>
      <div>
        <div class="font-mono text-2xl text-[var(--text)]">{total - score}</div>
        <div class="font-ui text-xs text-[var(--muted)]">Incorrect</div>
      </div>
      <div>
        <div class="font-mono text-2xl text-[var(--text)]">{total}</div>
        <div class="font-ui text-xs text-[var(--muted)]">Total</div>
      </div>
    </div>
  </div>

  <!-- Filter bar -->
  <div class="flex gap-2 mb-4">
    {#each ['all', 'correct', 'wrong'] as f}
      <button
        class="btn text-xs {filter === f ? 'btn-primary' : 'btn-ghost'}"
        on:click={() => filter = f}
      >
        {f.charAt(0).toUpperCase() + f.slice(1)}
        ({f === 'all' ? total : f === 'correct' ? score : total - score})
      </button>
    {/each}
  </div>

  <!-- Per-question breakdown -->
  <div class="flex flex-col gap-3">
    {#each filtered as detail, i (detail.question_number)}
      {@const ok = detail.is_correct}
      {@const opts = detail.all_options ?? []}
      {@const correctTexts = (detail.correct_indices ?? []).map(ci => opts[ci]?.text).filter(Boolean)}

      <div
        in:fly={{ y: 10, duration: 200, delay: i * 20 }}
        class="card p-4 border-l-2"
        style="border-left-color: {ok ? 'var(--green)' : 'var(--red)'}"
      >
        <div class="flex items-start gap-2">
          <span class="font-mono text-sm mt-0.5 flex-shrink-0"
            style="color: {ok ? 'var(--green)' : 'var(--red)'}">
            {ok ? '✓' : '✗'}
          </span>
          <div class="flex-1 min-w-0">
            <div class="font-mono text-[10px] text-[var(--faint)] mb-1">Q {detail.displayNumber ?? detail.question_number}</div>
            <p class="font-body text-sm leading-relaxed text-[var(--text)] mb-2">
              {detail.question_text?.slice(0, 200)}{detail.question_text?.length > 200 ? '…' : ''}
            </p>
            <div class="font-ui text-xs text-[var(--muted)]">
              <span class="text-[var(--faint)]">Correct: </span>
              {correctTexts.join('; ') || '—'}
            </div>
            {#if detail.explanation}
              <details class="mt-2">
                <summary class="font-ui text-xs text-[var(--faint)] cursor-pointer">Explanation</summary>
                <p class="mt-1 font-body text-xs text-[var(--muted)] leading-relaxed pl-2 border-l border-[var(--border)]">
                  {detail.explanation}
                </p>
              </details>
            {/if}
          </div>
        </div>
      </div>
    {/each}
  </div>

  <div class="mt-8 text-center">
    <button class="btn btn-primary" on:click={() => examStore.reset()}>
      ← Return to Home
    </button>
  </div>
</div>
