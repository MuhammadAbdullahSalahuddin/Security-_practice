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
  if (!questions || questions.length === 0) {
    throw new Error("No questions loaded — cannot grade.");
  }

  const user_answers = questions.map((q) => {
    const qNum = parseQNum(q.question_number);
    const selected = answers[qNum];
    return {
      question_number: qNum,
      // Only use the answer if it's a non-empty array, otherwise force []
      selected_indices:
        Array.isArray(selected) && selected.length > 0 ? selected : [],
    };
  });

  const r = await fetch(`${BASE}/grade`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ practice_set, exam_id, user_answers }),
  });
  if (!r.ok) throw new Error("Grading failed");

  const data = await r.json();

  const answerLookup = Object.fromEntries(
    user_answers.map((a) => [a.question_number, a.selected_indices]),
  );
  for (const detail of data.details ?? []) {
    detail.user_selected = answerLookup[detail.question_number] ?? [];
  }

  return data;
}

export function parseQNum(raw) {
  if (typeof raw === "number") return raw;
  const m = String(raw).match(/\d+/);
  return m ? parseInt(m[0]) : 0;
}
