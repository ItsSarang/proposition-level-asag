/**
 * Frontend API client communicating with backend API adapter.
 */
export async function fetchModels() {
  const res = await fetch('/api/models');
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
}

export async function gradeAnswer({ model, question, reference_answer, student_answer, scale = 5.0 }) {
  const res = await fetch('/api/grade', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, question, reference_answer, student_answer, scale }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Grading failed');
  }
  return res.json();
}
