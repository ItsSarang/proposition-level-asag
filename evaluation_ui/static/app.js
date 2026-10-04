/**
 * ASAG Evaluation Lab — Client-side interactions
 */

document.addEventListener('DOMContentLoaded', function () {
    const addBtn = document.getElementById('addAnswerBtn');
    const container = document.getElementById('answersContainer');
    const form = document.getElementById('evalForm');
    const submitBtn = document.getElementById('submitBtn');

    if (addBtn && container) {
        addBtn.addEventListener('click', function () {
            const count = container.querySelectorAll('.answer-item').length + 1;
            const newItem = document.createElement('div');
            newItem.className = 'answer-item';
            newItem.innerHTML = `
                <div class="answer-item-header">
                    <span class="answer-badge">Student Answer ${count}</span>
                    <button type="button" class="btn-remove-answer" title="Remove answer">&times;</button>
                </div>
                <textarea name="student_answers" rows="3" required placeholder="Enter student response..."></textarea>
            `;
            container.appendChild(newItem);

            // Bind removal event
            newItem.querySelector('.btn-remove-answer').addEventListener('click', function () {
                newItem.remove();
                renumberAnswers();
            });
        });

        // Bind existing removal buttons
        container.querySelectorAll('.btn-remove-answer').forEach(btn => {
            btn.addEventListener('click', function () {
                btn.closest('.answer-item').remove();
                renumberAnswers();
            });
        });
    }

    function renumberAnswers() {
        if (!container) return;
        container.querySelectorAll('.answer-item').forEach((item, idx) => {
            const badge = item.querySelector('.answer-badge');
            if (badge) {
                badge.innerText = `Student Answer ${idx + 1}`;
            }
        });
    }

    if (form && submitBtn) {
        form.addEventListener('submit', function () {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner">&#9696;</span> Evaluating Pipeline Across 4 Systems...';
        });
    }
});
