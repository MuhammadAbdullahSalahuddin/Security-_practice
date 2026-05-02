<script>
  import { examStore, currentQuestion, progress } from '../store.js';
  import { gradeExam, parseQNum } from '../api.js';
  import QuestionCard from '../components/QuestionCard.svelte';
  import Timer from '../components/Timer.svelte';

  let direction = 1; // animation direction
  let submitting = false;
  let error = null;

  $: mode = $examStore.mode;
  $: questions = $examStore.questions;
  $: idx = $examStore.currentIndex;
  $: total = questions.length;

  // Auto-submit when timer expires
  $: if ($examStore.timeExpired && !submitting) {
    submitExam();
  }

  function prev() {
    if (idx <= 0) return;
    direction = -1;
    examStore.prev();
  }

  function next() {
    if (idx >= total - 1) return;
    direction = 1;
    examStore.next();
  }

  function jumpTo(i) {
    direction = i > idx ? 1 : -1;
    examStore.goTo(i);
  }

  async function submitExam() {
    submitting = true;
    error = null;
    try {
      const results = await gradeExam(
        $examStore.practice_set,
        $examStore.exam_id,
        $examStore.answers,
        $examStore.questions
      );
      // Attach question text + options for results page
      const qLookup = Object.fromEntries(
        questions.map(q => [parseQNum(q.question_number), q])
      );
      for (const d of results.details ?? []) {
        const q = qLookup[d.question_number];
        d.question_text = q?.question_text ?? '';
        d.all_options = q?.all_options ?? [];
        d.displayNumber = q?.displayNumber ?? d.question_number;
      }
      examStore.setResults(results);
    } catch (e) {
      error = e.message;
    } finally {
      submitting = false;
    }
  }

  $: answeredSet = new Set(
    Object.entries($examStore.answers)
      .filter(([, v]) => v?.length > 0)
      .map(([k]) => parseInt(k))
  );
</script>

<div class="flex h-screen overflow-hidden">

  <!-- ── Sidebar ─────────────────────────────────── -->
  <aside class="w-56 flex-shrink-0 bg-[var(--surface)] border-r border-[var(--border)] flex flex-col py-6 px-3 overflow-y-auto">
    <div class="font-mono text-[10px] tracking-widest text-[var(--amber)] uppercase mb-1 px-2">
      {mode === 'practice' ? 'Practice' : 'Exam'}
    </div>
    <div class="font-ui text-xs text-[var(--muted)] mb-4 px-2 truncate">
      {$examStore.exam_id?.replace(/_/g, ' ')}
    </div>

    {#if mode === 'exam' && $examStore.endTime}
      <div class="mb-4 px-1">
        <Timer endTime={$examStore.endTime} />
      </div>
    {/if}

    <div class="font-ui text-[10px] text-[var(--faint)] uppercase tracking-widest px-2 mb-2">Questions</div>

    <div class="flex flex-col gap-1 flex-1">
      {#each questions as q, i}
        {@const qn = parseQNum(q.question_number)}
        {@const displayNum = q.displayNumber ?? (i + 1)}
        {@const isActive = i === idx}
        {@const isAnswered = answeredSet.has(qn)}
        {@const isSubmitted = $examStore.submitted.has(qn)}
        {@const isCorrectQ = isSubmitted && JSON.stringify([...(($examStore.answers[qn] ?? []).sort())]) === JSON.stringify([...(q.correct_indices ?? []).sort()])}

        <button
          class="text-left px-2 py-1.5 rounded font-mono text-xs transition-all
            {isActive
              ? 'bg-[rgba(240,168,48,.1)] text-[var(--amber)]'
              : 'text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--hover)]'}"
          on:click={() => jumpTo(i)}
        >
          <span>Q{displayNum}</span>
          <span class="ml-1 text-[10px]">
            {#if mode === 'practice' && isSubmitted}
              {isCorrectQ ? '✓' : '✗'}
            {:else if isAnswered}
              ·
            {:else}
              &nbsp;
            {/if}
          </span>
        </button>
      {/each}
    </div>

    <div class="mt-4 px-1">
      <button class="btn btn-ghost text-xs w-full" on:click={() => examStore.reset()}>
        ← Exit
      </button>
    </div>
  </aside>

  <!-- ── Main area ───────────────────────────────── -->
  <main class="flex-1 overflow-y-auto flex flex-col">
    <div class="max-w-2xl mx-auto w-full px-6 py-10 flex flex-col gap-6 flex-1">

      <!-- Progress bar -->
      <div class="flex items-center gap-3">
        <div class="flex-1 h-1 bg-[var(--border)] rounded-full overflow-hidden">
          <div
            class="h-full bg-[var(--amber)] transition-all duration-300 rounded-full"
            style="width: {((idx + 1) / total) * 100}%"
          ></div>
        </div>
        <span class="font-mono text-[10px] text-[var(--faint)] whitespace-nowrap">
          {idx + 1} / {total}
        </span>
      </div>

      <!-- Question card with fly animation -->
      {#if $currentQuestion}
        <QuestionCard
          question={$currentQuestion}
          {mode}
          {direction}
        />
      {/if}

      <!-- Navigation buttons -->
      <div class="flex items-center justify-between mt-2">
        <button class="btn btn-ghost" on:click={prev} disabled={idx === 0}>← Prev</button>

        <div class="flex gap-2">
          {#if idx < total - 1}
            <button class="btn" on:click={next}>Next →</button>
          {:else}
            <!-- Last question: show submit -->
            {#if mode === 'exam'}
              <button class="btn btn-primary" on:click={submitExam} disabled={submitting}>
                {submitting ? 'Grading...' : 'Submit Exam'}
              </button>
            {:else}
              <button class="btn btn-primary" on:click={submitExam} disabled={submitting}>
                {submitting ? 'Grading...' : 'Finish & See Results'}
              </button>
            {/if}
          {/if}
        </div>
      </div>

      {#if error}
        <div class="font-ui text-sm text-[var(--red)] mt-2">⚠ {error}</div>
      {/if}

      <!-- Practice mode: show submit anywhere -->
      {#if idx < total - 1}
        <div class="text-center mt-2">
          <button class="btn btn-ghost text-xs" on:click={submitExam} disabled={submitting}>
            {submitting ? 'Grading...' : 'Finish early & see results'}
          </button>
        </div>
      {/if}

    </div>
  </main>
</div>