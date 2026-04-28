const BASE = "/api/v1";

export async function getExams() {
  const r = await fetch(`${BASE}/exams`);
  if (!r.ok) throw new Error("Failed to fetch exams");
  const d = await r.json();
  return d.data ?? [];
}

export async function getExam(practice_set, exam_id) {
  const r = await fetch(`${BASE}/exams/${practice_set}/${exam_id}`);
  if (!r.ok) throw new Error(`Exam not found: ${r.status}`);
  return r.json();
}

export async function gradeExam(practice_set, exam_id, answers, questions) {
  // Mark unanswered / skipped questions as empty → backend scores as wrong
  const user_answers = questions.map((q) => {
    const qNum = parseQNum(q.question_number);
    return {
      question_number: qNum,
      selected_indices: answers[qNum] ?? [],
    };
  });

  const r = await fetch(`${BASE}/grade`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ practice_set, exam_id, user_answers }),
  });
  if (!r.ok) throw new Error("Grading failed");
  return r.json();
}

export function parseQNum(raw) {
  if (typeof raw === "number") return raw;
  const m = String(raw).match(/\d+/);
  return m ? parseInt(m[0]) : 0;
}
