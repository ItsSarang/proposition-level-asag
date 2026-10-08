const API_BASE = import.meta.env.VITE_API_URL || '';

export async function analyzeAnswer({ question, referenceAnswer, studentAnswer, scale = 5.0 }) {
  const payload = {
    question,
    reference_answer: referenceAnswer,
    student_answer: studentAnswer,
    scale,
  };

  const primaryUrl = API_BASE ? `${API_BASE.replace(/\/+$/, '')}/api/analyze` : '/api/analyze';

  try {
    const res = await fetch(primaryUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    void err;
  }

  if (!API_BASE) {
    try {
      const fallbackUrl = 'http://localhost:8000/api/analyze';
      const fallbackRes = await fetch(fallbackUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (fallbackRes.ok) {
        return await fallbackRes.json();
      }
    } catch (err) {
      void err;
    }
  }

  return null;
}
