document.addEventListener("DOMContentLoaded", () => {
    // Form submission loading
    const studyForm = document.getElementById("studyForm");
    if (studyForm) {
        studyForm.addEventListener("submit", () => {
            const btn = document.getElementById("submitBtn");
            const btnText = btn.querySelector(".btn-text");
            const spinner = document.getElementById("spinner");

            btn.disabled = true;
            if (btnText) btnText.style.display = "none";
            if (spinner) spinner.style.display = "inline";
        });
    }

    const quizForm = document.getElementById("quizForm");
    const checkAnswersBtn = document.getElementById("checkAnswersBtn");
    const moreQuestionsBtn = document.getElementById("moreQuestionsBtn");
    let isChecked = false;

    // Check / Reset Answers
    if (checkAnswersBtn) {
        checkAnswersBtn.addEventListener("click", () => {
            const quizItems = document.querySelectorAll(".quiz-item");
            const radioInputs = document.querySelectorAll("#quizForm input[type='radio']");

            if (!isChecked) {
                quizItems.forEach((item) => {
                    const rawCorrect = item.getAttribute("data-correct") || "";
                    const correctAnswer = rawCorrect.trim().toLowerCase();
                    const selectedRadio = item.querySelector("input[type='radio']:checked");
                    const allBoxes = item.querySelectorAll(".option-box");

                    allBoxes.forEach(box => box.classList.remove("correct", "incorrect"));

                    if (selectedRadio) {
                        const chosenValue = selectedRadio.value.trim().toLowerCase();
                        const chosenBox = selectedRadio.nextElementSibling;

                        if (chosenValue === correctAnswer) {
                            chosenBox.classList.add("correct");
                        } else {
                            chosenBox.classList.add("incorrect");
                        }
                    }

                    item.querySelectorAll(".option-label").forEach(label => {
                        const radio = label.querySelector("input");
                        if (radio && radio.value.trim().toLowerCase() === correctAnswer) {
                            label.querySelector(".option-box").classList.add("correct");
                        }
                    });
                });

                radioInputs.forEach(radio => radio.disabled = true);
                quizForm.classList.add("quiz-locked");
                checkAnswersBtn.textContent = "Reset Quiz";
                isChecked = true;
            } else {
                radioInputs.forEach(radio => {
                    radio.disabled = false;
                    radio.checked = false;
                });

                document.querySelectorAll(".option-box").forEach(box => {
                    box.classList.remove("correct", "incorrect");
                });

                quizForm.classList.remove("quiz-locked");
                checkAnswersBtn.textContent = "Check Answers";
                isChecked = false;
            }
        });
    }

    // Replace Questions Set via Fetch
    if (moreQuestionsBtn && quizForm) {
        moreQuestionsBtn.addEventListener("click", async () => {
            const sessionId = quizForm.getAttribute("data-session-id");
            const btnText = moreQuestionsBtn.querySelector(".more-btn-text");
            const spinner = moreQuestionsBtn.querySelector(".more-spinner");

            moreQuestionsBtn.disabled = true;
            btnText.style.display = "none";
            spinner.style.display = "inline";

            try {
                const response = await fetch(`/generate_more_questions/${sessionId}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });
                const data = await response.json();

                if (data.success) {
                    const container = document.getElementById("quizItemsContainer");
                    container.innerHTML = ""; // Clear existing questions

                    data.new_questions.forEach((item, index) => {
                        const itemDiv = document.createElement("div");
                        itemDiv.className = "quiz-item";
                        itemDiv.setAttribute("data-correct", item.correct_answer.trim());

                        let optionsHtml = "";
                        item.options.forEach(opt => {
                            optionsHtml += `
                                <label class="option-label">
                                    <input type="radio" name="question_${index}" value="${opt.trim()}">
                                    <span class="option-box">${opt}</span>
                                </label>
                            `;
                        });

                        itemDiv.innerHTML = `
                            <p class="question-text"><strong>Q${index + 1}.</strong> ${item.question}</p>
                            <div class="options-group">
                                ${optionsHtml}
                            </div>
                        `;

                        container.appendChild(itemDiv);
                    });

                    // Reset check button state
                    checkAnswersBtn.textContent = "Check Answers";
                    isChecked = false;
                    quizForm.classList.remove("quiz-locked");
                } else {
                    alert("Could not load new questions: " + (data.error || "Unknown error"));
                }
            } catch (err) {
                alert("Request failed: " + err.message);
            } finally {
                moreQuestionsBtn.disabled = false;
                btnText.style.display = "inline";
                spinner.style.display = "none";
            }
        });
    }
});