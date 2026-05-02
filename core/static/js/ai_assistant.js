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

        const body = document.createElement("div");
        body.className = "chat-content";
        renderMessage(body, text);

        bubble.appendChild(label);
        bubble.appendChild(body);
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;

        return bubble;
    }

    function renderMessage(container, text) {
        container.innerHTML = "";
        const lines = String(text || "").split(/\n/);
        let list = null;

        lines.forEach(function (line) {
            const trimmed = line.trim();

            if (!trimmed) {
                list = null;
                container.appendChild(document.createElement("br"));
                return;
            }

            if (trimmed.startsWith("- ")) {
                if (!list) {
                    list = document.createElement("ul");
                    container.appendChild(list);
                }
                const li = document.createElement("li");
                li.textContent = trimmed.slice(2);
                list.appendChild(li);
                return;
            }

            list = null;

            if (/^\d+\.\s/.test(trimmed)) {
                const item = document.createElement("p");
                item.className = "chat-numbered-line";
                item.textContent = trimmed;
                container.appendChild(item);
                return;
            }

            if (trimmed.endsWith(":") && trimmed.length < 80) {
                const heading = document.createElement("h4");
                heading.textContent = trimmed.slice(0, -1);
                container.appendChild(heading);
                return;
            }

            const paragraph = document.createElement("p");
            paragraph.textContent = trimmed;
            container.appendChild(paragraph);
        });
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

            const source = document.createElement("small");
            source.textContent = `${item.source_name || "Portal record"} - ${item.freshness_note || "Verify before applying"}`;

            card.appendChild(type);
            card.appendChild(title);
            card.appendChild(meta);
            card.appendChild(source);
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

            renderMessage(thinking.querySelector(".chat-content"), data.answer);
            history.push({ role: "assistant", content: data.answer });
            provider.textContent = data.provider === "openai-rag"
                ? "LLM RAG"
                : "Local RAG";
            renderSources(data.items);
        } catch (error) {
            renderMessage(
                thinking.querySelector(".chat-content"),
                "I could not answer that request right now. Please try again."
            );
            provider.textContent = "Error";
        } finally {
            form.classList.remove("is-loading");
            form.querySelector("button").disabled = false;
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
        questionInput.style.height = "";
        form.classList.add("is-loading");
        form.querySelector("button").disabled = true;
        askAssistant(message);
    });

    questionInput.addEventListener("input", function () {
        questionInput.style.height = "auto";
        questionInput.style.height = `${Math.min(questionInput.scrollHeight, 180)}px`;
    });

    questionInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    chips.forEach(function (chip) {
        chip.addEventListener("click", function () {
            questionInput.value = chip.textContent.trim();
            questionInput.focus();
        });
    });
});
