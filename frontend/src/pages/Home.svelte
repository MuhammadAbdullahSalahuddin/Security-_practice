<script>
  import { getExams, getExam } from '../api.js';
  import { pendingExam, page } from '../store.js';

  let loading = false;
  let error = null;
  let sets = [];
  let expanded = null;

  async function loadSets() {
    loading = true;
    try {
      sets = await getExams();
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function selectExam(setId, examId) {
    loading = true;
    try {
      const exam_data = await getExam(setId, examId);
      pendingExam.set({ practice_set: setId, exam_id: examId, exam_data });
      page.set('mode_select');
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  loadSets();
</script>

<div class="max-w-3xl mx-auto px-6 py-16">
  <!-- Header -->
  <div class="mb-12">
    <p class="font-mono text-xs tracking-widest text-amber mb-3 uppercase">Security+</p>
    <h1 class="font-body text-4xl font-semibold text-[var(--text)] leading-tight mb-2">
      Practice Engine
    </h1>
    <p class="font-ui text-sm text-[var(--muted)]">Select a practice set to begin your session.</p>
  </div>

  {#if error}
    <div class="card p-4 border-[var(--red)] text-[var(--red)] font-ui text-sm mb-6">
      ⚠ {error} — ensure the FastAPI backend is running on port 8000.
    </div>
  {/if}

  {#if loading && !sets.length}
    <div class="font-ui text-sm text-[var(--muted)] animate-pulse">Loading exams...</div>
  {/if}

  <div class="grid grid-cols-1 gap-4">
    {#each sets as set, i}
      {@const isOpen = expanded === set._id}
      <div class="card overflow-hidden">
        <button
          class="w-full text-left px-6 py-5 flex items-center justify-between group"
          on:click={() => expanded = isOpen ? null : set._id}
        >
          <div>
            <div class="font-mono text-[10px] tracking-widest text-[var(--faint)] uppercase mb-1">
              Set {i + 1}
            </div>
            <div class="font-ui font-medium text-[var(--text)] group-hover:text-[var(--amber)] transition-colors">
              {set._id.replace(/_/g, ' ')}
            </div>
            <div class="font-ui text-xs text-[var(--muted)] mt-0.5">
              {set.exams.length} exam{set.exams.length !== 1 ? 's' : ''}
            </div>
          </div>
          <span class="font-mono text-[var(--faint)] group-hover:text-[var(--amber)] transition-all duration-200"
            style="transform: rotate({isOpen ? 90 : 0}deg); display:inline-block">▶</span>
        </button>

        {#if isOpen}
          <div class="border-t border-[var(--border)] px-6 py-4 flex flex-wrap gap-2">
            {#each set.exams.sort() as eid}
              <button
                class="btn btn-primary text-xs"
                on:click={() => selectExam(set._id, eid)}
                disabled={loading}
              >
                {eid.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {/each}

    <!-- Placeholder card -->
    <div class="card px-6 py-5 opacity-40 select-none">
      <div class="font-mono text-[10px] tracking-widest text-[var(--faint)] uppercase mb-1">Coming soon</div>
      <div class="font-ui font-medium text-[var(--muted)]">Practice Set 2</div>
      <div class="font-ui text-xs text-[var(--faint)] mt-0.5">Additional content in progress</div>
    </div>
  </div>
</div>
