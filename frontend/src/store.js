import { writable, derived, get } from 'svelte/store';

// ─── Router ───────────────────────────────────────────────────────────────────
export const page = writable('home'); // 'home' | 'mode_select' | 'exam' | 'results'

// ─── Session config ───────────────────────────────────────────────────────────
export const pendingExam = writable(null); // { practice_set, exam_id, exam_data }

// ─── Active exam state ────────────────────────────────────────────────────────
const INITIAL = {
  mode: null,           // 'practice' | 'exam'
  practice_set: null,
  exam_id: null,
  questions: [],        // shuffled
  currentIndex: 0,
  answers: {},          // { [question_number]: [idx, ...] }
  submitted: new Set(), // question_numbers locked in practice mode
  results: null,
  endTime: null,        // ms timestamp
  timeExpired: false,
};

function createExamStore() {
  const { subscribe, set, update } = writable({ ...INITIAL });

  let timerInterval = null;

  function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  return {
    subscribe,

    startSession(pendingExamData, mode) {
      clearInterval(timerInterval);
      const questions = shuffle(pendingExamData.exam_data.questions);
      const endTime = mode === 'exam' ? Date.now() + 7200_000 : null;

      set({
        mode,
        practice_set: pendingExamData.practice_set,
        exam_id: pendingExamData.exam_id,
        questions,
        currentIndex: 0,
        answers: {},
        submitted: new Set(),
        results: null,
        endTime,
        timeExpired: false,
      });

      if (mode === 'exam') {
        timerInterval = setInterval(() => {
          update(s => {
            if (!s.endTime) return s;
            if (Date.now() >= s.endTime) {
              clearInterval(timerInterval);
              return { ...s, timeExpired: true };
            }
            return s;
          });
        }, 500);
      }

      page.set('exam');
    },

    setAnswer(qNum, indices) {
      update(s => ({ ...s, answers: { ...s.answers, [qNum]: indices } }));
    },

    lockQuestion(qNum) {
      update(s => {
        const submitted = new Set(s.submitted);
        submitted.add(qNum);
        return { ...s, submitted };
      });
    },

    goTo(index) {
      update(s => ({ ...s, currentIndex: index }));
    },

    next() {
      update(s => ({
        ...s,
        currentIndex: Math.min(s.currentIndex + 1, s.questions.length - 1),
      }));
    },

    prev() {
      update(s => ({ ...s, currentIndex: Math.max(s.currentIndex - 1, 0) }));
    },

    setResults(results) {
      clearInterval(timerInterval);
      update(s => ({ ...s, results }));
      page.set('results');
    },

    reset() {
      clearInterval(timerInterval);
      set({ ...INITIAL });
      page.set('home');
    },
  };
}

export const examStore = createExamStore();

// ─── Derived helpers ──────────────────────────────────────────────────────────
export const currentQuestion = derived(
  examStore,
  $s => $s.questions[$s.currentIndex] ?? null
);

export const progress = derived(
  examStore,
  $s => ({
    current: $s.currentIndex + 1,
    total: $s.questions.length,
    answered: Object.keys($s.answers).length,
  })
);

export const remainingMs = derived(examStore, $s => {
  if (!$s.endTime) return null;
  return Math.max(0, $s.endTime - Date.now());
});
