<script>
  import { pendingExam, examStore, page } from '../store.js';

  const exam = $pendingExam;

  function start(mode) {
    examStore.startSession(exam, mode);
  }
</script>

<div class="max-w-2xl mx-auto px-6 py-16">
  <button class="btn btn-ghost mb-10 text-xs" on:click={() => page.set('home')}>
    ← Back
  </button>

  <p class="font-mono text-[10px] tracking-widest text-[var(--amber)] uppercase mb-2">
    {exam?.practice_set?.replace(/_/g, ' ')} · {exam?.exam_id?.replace(/_/g, ' ')}
  </p>
  <h1 class="font-body text-3xl font-semibold mb-10">Select a mode</h1>

  <div class="grid grid-cols-2 gap-4">
    <div class="card p-6 flex flex-col gap-4">
      <div>
        <div class="font-mono text-xs text-[var(--amber)] mb-2 tracking-widest uppercase">📘 Practice</div>
        <p class="font-ui text-sm text-[var(--muted)] leading-relaxed">
          One question at a time. Instant feedback after each answer. Explanations shown. No time limit.
        </p>
      </div>
      <button class="btn btn-primary mt-auto" on:click={() => start('practice')}>
        Start Practice
      </button>
    </div>

    <div class="card p-6 flex flex-col gap-4">
      <div>
        <div class="font-mono text-xs text-[var(--amber)] mb-2 tracking-widest uppercase">⏱ Exam</div>
        <p class="font-ui text-sm text-[var(--muted)] leading-relaxed">
          Strict 2-hour countdown. Navigate freely between questions. No feedback until submission.
        </p>
      </div>
      <button class="btn mt-auto" on:click={() => start('exam')}>
        Start Exam
      </button>
    </div>
  </div>
</div>
