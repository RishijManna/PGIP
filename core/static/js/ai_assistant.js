document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("aiChatForm");
    const questionInput = document.getElementById("aiQuestion");
    const messages = document.getElementById("aiMessages");
    const provider = document.getElementById("aiProvider");
    const sources = document.getElementById("aiSources");
    const chips = document.querySelectorAll(".prompt-chip");
    const history = [];

    if (!form || !questionInput || !messages) {
        return;
    }

    function csrfToken() {
        const tokenInput = form.querySelector("input[name='csrfmiddlewaretoken']");
        return tokenInput ? tokenInput.value : "";
    }

    function addMessage(role, text) {
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble ${role}`;

        const label = document.createElement("strong");
        label.textContent = role === "user" ? "You" : "PGIP AI";

        const body = document.createElement("p");
        body.textContent = text;

        bubble.appendChild(label);
        bubble.appendChild(body);
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;

        return bubble;
    }

    function renderSources(items) {
        if (!sources || !Array.isArray(items) || !items.length) {
            return;
        }

        sources.innerHTML = "<h3>Sources used</h3>";

        items.forEach(function (item) {
            const card = document.createElement("a");
            card.className = "ai-source-card";
            card.href = `/details/${item.type}/${item.id}/`;

            const type = document.createElement("span");
            type.textContent = `${item.type} - ${item.confidence}% match`;

            const title = document.createElement("strong");
            title.textContent = item.title.replace(/^Exam: |^Scheme: |^Job: /, "");

            const meta = document.createElement("small");
            meta.textContent = `${item.category} - ${item.location} - ${item.date}`;

            card.appendChild(type);
            card.appendChild(title);
            card.appendChild(meta);
            sources.appendChild(card);
        });
    }

    async function askAssistant(message) {
        provider.textContent = "Thinking...";

        const thinking = addMessage("assistant", "Searching schemes, exams and jobs...");

        try {
            const response = await fetch(window.PGIP_AI_ENDPOINT, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken(),
                },
                body: JSON.stringify({
                    message,
                    history: history.slice(-8),
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "AI request failed.");
            }

            thinking.querySelector("p").textContent = data.answer;
            history.push({ role: "assistant", content: data.answer });
            provider.textContent = data.provider === "openai-rag"
                ? "LLM RAG"
                : "Local RAG";
            renderSources(data.items);
        } catch (error) {
            thinking.querySelector("p").textContent = "I could not answer that request right now. Please try again.";
            provider.textContent = "Error";
        }
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const message = questionInput.value.trim();

        if (!message) {
            return;
        }

        addMessage("user", message);
        history.push({ role: "user", content: message });
        questionInput.value = "";
        askAssistant(message);
    });

    chips.forEach(function (chip) {
        chip.addEventListener("click", function () {
            questionInput.value = chip.textContent.trim();
            questionInput.focus();
        });
    });
});
