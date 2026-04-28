<script>
  import { fly } from 'svelte/transition';
  import { examStore } from '../store.js';
  import { parseQNum } from '../api.js';

  export let question;
  export let mode;
  export let direction = 1; // 1 = forward, -1 = back

  $: qNum = parseQNum(question?.question_number);
  $: options = question?.all_options ?? [];
  $: correct = question?.correct_indices ?? [];
  $: isMulti = correct.length > 1 || question?.question_type === 'multiple_choice';
  $: isLocked = $examStore.submitted.has(qNum);
  $: selected = $examStore.answers[qNum] ?? [];

  function toggle(idx) {
    if (isLocked && mode === 'practice') return;
    if (isMulti) {
      const next = selected.includes(idx)
        ? selected.filter(i => i !== idx)
        : [...selected, idx];
      examStore.setAnswer(qNum, next);
    } else {
      examStore.setAnswer(qNum, [idx]);
    }
  }

  function check() {
    examStore.lockQuestion(qNum);
  }

  function skip() {
    examStore.setAnswer(qNum, []);
    examStore.lockQuestion(qNum);
  }

  $: userCorrect = mode === 'practice' && isLocked
    ? JSON.stringify([...selected].sort()) === JSON.stringify([...correct].sort())
    : null;
</script>

{#key question?.question_number}
  <div
    in:fly={{ x: direction * 40, duration: 220, opacity: 0 }}
    out:fly={{ x: direction * -40, duration: 180, opacity: 0 }}
    class="card p-6 md:p-8"
  >
    <!-- Question header -->
    <div class="flex items-center gap-3 mb-5">
      <span class="font-mono text-[10px] tracking-widest text-[var(--amber)] uppercase">
        Q {qNum}
      </span>
      <span class="font-ui text-[10px] text-[var(--faint)]">
        {isMulti ? `Select ${correct.length}` : 'Select one'}
      </span>
    </div>

    <!-- Question text -->
    <p class="font-body text-[1.05rem] leading-relaxed text-[var(--text)] mb-6">
      {question?.question_text ?? ''}
    </p>

    <!-- Options -->
    <div class="flex flex-col gap-2">
      {#each options as opt, idx}
        {@const isSel = selected.includes(idx)}
        {@const isCorrectOpt = correct.includes(idx)}
        {@const showFeedback = mode === 'practice' && isLocked}

        <button
          class="text-left px-4 py-3 rounded-lg border transition-all duration-150 font-ui text-sm leading-relaxed
            {showFeedback
              ? isCorrectOpt
                ? 'border-[var(--green)] bg-[var(--green-bg)] text-[var(--green)]'
                : isSel && !isCorrectOpt
                  ? 'border-[var(--red)] bg-[var(--red-bg)] text-[var(--red)]'
                  : 'border-[var(--border)] text-[var(--muted)]'
              : isSel
                ? 'border-[var(--amber)] bg-[rgba(240,168,48,.06)] text-[var(--text)]'
                : 'border-[var(--border)] text-[var(--muted)] hover:border-[var(--border-hi)] hover:text-[var(--text)]'}
            {isLocked && mode === 'practice' ? 'cursor-default' : 'cursor-pointer'}"
          on:click={() => toggle(idx)}
          disabled={isLocked && mode === 'practice'}
        >
          <span class="font-mono text-[10px] mr-2 opacity-50">{String.fromCharCode(65 + idx)}.</span>
          {opt.text}
        </button>
      {/each}
    </div>

    <!-- Practice mode feedback -->
    {#if mode === 'practice'}
      {#if !isLocked}
        <div class="flex gap-2 mt-6">
          <button class="btn btn-primary" on:click={check} disabled={selected.length === 0}>
            Check Answer
          </button>
          <button class="btn btn-ghost text-xs" on:click={skip}>Skip</button>
        </div>
      {:else}
        <div class="mt-5 flex items-center gap-2">
          {#if userCorrect}
            <span class="font-ui text-xs px-2 py-1 rounded bg-[var(--green-bg)] text-[var(--green)] border border-[var(--green)]">
              ✓ Correct
            </span>
          {:else}
            <span class="font-ui text-xs px-2 py-1 rounded bg-[var(--red-bg)] text-[var(--red)] border border-[var(--red)]">
              ✗ {selected.length === 0 ? 'Skipped' : 'Incorrect'}
            </span>
          {/if}
        </div>

        {#if question?.explanation}
          <details class="mt-4">
            <summary class="font-ui text-xs text-[var(--muted)] cursor-pointer select-none">
              📖 Explanation
            </summary>
            <div class="mt-2 pl-3 border-l-2 border-[var(--amber-dim)] font-body text-sm text-[var(--muted)] leading-relaxed">
              {question.explanation}
            </div>
          </details>
        {/if}
      {/if}
    {/if}
  </div>
{/key}
